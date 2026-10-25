"""Offline, provenance-preserving Forge knowledge library."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from .enrollment import EnrollmentError

SCHEMA_VERSION = 1
DEFAULT_DB = Path.home() / ".local/share/sentinel-forge/knowledge/knowledge.sqlite3"
ALLOWED_SUFFIXES = frozenset({".txt", ".md"})
MAX_SOURCE_BYTES = 16 * 1024 * 1024
CHUNK_TARGET_CHARS = 1800
CHUNK_OVERLAP_CHARS = 240


@dataclass(frozen=True)
class KnowledgeHit:
    source_id: str
    source_name: str
    source_sha256: str
    chunk_ordinal: int
    text: str
    score: float

    @property
    def citation(self) -> str:
        return f"forgekb:{self.source_id}:chunk-{self.chunk_ordinal}"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _normalize_text(text: str) -> str:
    return re.sub(r"\r\n?", "\n", text).strip()


def chunk_text(text: str) -> tuple[str, ...]:
    text = _normalize_text(text)
    if not text:
        raise EnrollmentError("knowledge source is empty")
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = paragraph if not current else current + "\n\n" + paragraph
        if len(candidate) <= CHUNK_TARGET_CHARS:
            current = candidate
            continue
        if current:
            chunks.append(current)
            overlap = current[-CHUNK_OVERLAP_CHARS:]
            current = overlap + "\n\n" + paragraph
        else:
            start = 0
            while start < len(paragraph):
                end = min(len(paragraph), start + CHUNK_TARGET_CHARS)
                chunks.append(paragraph[start:end])
                if end == len(paragraph):
                    current = ""
                    break
                start = max(end - CHUNK_OVERLAP_CHARS, start + 1)
    if current:
        chunks.append(current)
    return tuple(chunks)


class KnowledgeLibrary:
    def __init__(self, path: Path = DEFAULT_DB):
        self.path = Path(path)

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.path, timeout=0.25)
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA journal_mode=WAL")
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS metadata(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sources(
                source_id TEXT PRIMARY KEY,
                source_name TEXT NOT NULL,
                source_sha256 TEXT NOT NULL UNIQUE,
                byte_count INTEGER NOT NULL,
                ingested_at_utc TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS chunks(
                chunk_id INTEGER PRIMARY KEY,
                source_id TEXT NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
                ordinal INTEGER NOT NULL,
                text TEXT NOT NULL,
                UNIQUE(source_id, ordinal)
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                text,
                content='chunks',
                content_rowid='chunk_id'
            );
            CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
                INSERT INTO chunks_fts(rowid,text) VALUES(new.chunk_id,new.text);
            END;
            CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
                INSERT INTO chunks_fts(chunks_fts,rowid,text) VALUES('delete',old.chunk_id,old.text);
            END;
            """
        )
        row = con.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
        if row is None:
            con.execute("INSERT INTO metadata(key,value) VALUES('schema_version',?)", (str(SCHEMA_VERSION),))
        elif row[0] != str(SCHEMA_VERSION):
            con.close()
            raise EnrollmentError("knowledge library schema mismatch")
        return con

    def ingest(self, source: Path) -> dict[str, object]:
        source = Path(source)
        if not source.is_absolute():
            raise EnrollmentError("knowledge source path must be absolute")
        if source.suffix.lower() not in ALLOWED_SUFFIXES:
            raise EnrollmentError("knowledge source type not allowed")
        if not source.is_file() or source.is_symlink():
            raise EnrollmentError("knowledge source must be a regular non-symlink file")
        data = source.read_bytes()
        if len(data) > MAX_SOURCE_BYTES:
            raise EnrollmentError("knowledge source exceeds size limit")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise EnrollmentError("knowledge source must be UTF-8") from exc
        digest = _sha256(data)
        source_id = digest[:24]
        chunks = chunk_text(text)
        now = datetime.now(timezone.utc).isoformat()
        con = self._connect()
        try:
            existing = con.execute(
                "SELECT source_id,source_name,byte_count FROM sources WHERE source_sha256=?",
                (digest,),
            ).fetchone()
            if existing is not None:
                return {
                    "status": "already_ingested",
                    "source_id": existing[0],
                    "source_name": existing[1],
                    "source_sha256": digest,
                    "byte_count": existing[2],
                }
            con.execute(
                "INSERT INTO sources(source_id,source_name,source_sha256,byte_count,ingested_at_utc) VALUES(?,?,?,?,?)",
                (source_id, source.name, digest, len(data), now),
            )
            con.executemany(
                "INSERT INTO chunks(source_id,ordinal,text) VALUES(?,?,?)",
                ((source_id, i, chunk) for i, chunk in enumerate(chunks, start=1)),
            )
            con.commit()
        finally:
            con.close()
        return {
            "status": "ingested",
            "source_id": source_id,
            "source_name": source.name,
            "source_sha256": digest,
            "byte_count": len(data),
            "chunk_count": len(chunks),
            "ingested_at_utc": now,
        }

    def search(self, query: str, limit: int = 5) -> tuple[KnowledgeHit, ...]:
        if not isinstance(query, str) or not query.strip():
            raise EnrollmentError("knowledge query required")
        if type(limit) is not int or not 1 <= limit <= 10:
            raise EnrollmentError("knowledge result limit invalid")
        terms = re.findall(r"[A-Za-z0-9_.:/-]+", query.lower())
        if not terms:
            raise EnrollmentError("knowledge query has no searchable terms")
        # AND first rewards chunks that actually cover the operator's complete concept.
        # Fall back to OR only when the corpus has no all-term match.
        escaped = [term.replace(chr(34), "") for term in terms[:16]]
        candidates = (
            " AND ".join(f'"{term}"' for term in escaped),
            " OR ".join(f'"{term}"' for term in escaped),
        )
        rows = []
        con = self._connect()
        try:
            for fts_query in candidates:
                rows = con.execute(
                    """
                    SELECT s.source_id,s.source_name,s.source_sha256,c.ordinal,c.text,bm25(chunks_fts)
                    FROM chunks_fts
                    JOIN chunks c ON c.chunk_id=chunks_fts.rowid
                    JOIN sources s ON s.source_id=c.source_id
                    WHERE chunks_fts MATCH ?
                    ORDER BY bm25(chunks_fts), s.source_id, c.ordinal
                    LIMIT ?
                    """,
                    (fts_query, limit),
                ).fetchall()
                if rows:
                    break
        finally:
            con.close()
        return tuple(KnowledgeHit(*row) for row in rows)

    def search_sources(self, query: str, source_names: tuple[str, ...], limit: int = 5) -> tuple[KnowledgeHit, ...]:
        if not source_names:
            return ()
        if not isinstance(query, str) or not query.strip():
            raise EnrollmentError("knowledge query required")
        terms = re.findall(r"[A-Za-z0-9_.:/-]+", query.lower())
        if not terms:
            raise EnrollmentError("knowledge query has no searchable terms")
        escaped=[term.replace(chr(34),"") for term in terms[:16]]
        candidates=(
            " AND ".join(f'"{term}"' for term in escaped),
            " OR ".join(f'"{term}"' for term in escaped),
        )
        placeholders=",".join("?" for _ in source_names)
        con=self._connect()
        try:
            rows=[]
            for fts_query in candidates:
                rows=con.execute(
                    f"""SELECT s.source_id,s.source_name,s.source_sha256,c.ordinal,c.text,bm25(chunks_fts)
                    FROM chunks_fts JOIN chunks c ON c.chunk_id=chunks_fts.rowid
                    JOIN sources s ON s.source_id=c.source_id
                    WHERE chunks_fts MATCH ? AND s.source_name IN ({placeholders})
                    ORDER BY bm25(chunks_fts),s.source_id,c.ordinal LIMIT ?""",
                    (fts_query,*source_names,limit),
                ).fetchall()
                if rows:
                    break
        finally:
            con.close()
        return tuple(KnowledgeHit(*row) for row in rows)

    def stats(self) -> dict[str, int]:
        con = self._connect()
        try:
            sources = con.execute("SELECT count(*) FROM sources").fetchone()[0]
            chunks = con.execute("SELECT count(*) FROM chunks").fetchone()[0]
        finally:
            con.close()
        return {"source_count": sources, "chunk_count": chunks}


def knowledge_tool(query: str, path: Path = DEFAULT_DB) -> str:
    library = KnowledgeLibrary(path)
    hits = library.search(query)
    payload = {
        "query": query,
        "library": library.stats(),
        "hits": [
            {
                "citation": hit.citation,
                "source_name": hit.source_name,
                "source_sha256": hit.source_sha256,
                "chunk_ordinal": hit.chunk_ordinal,
                "text": hit.text,
                "score": hit.score,
            }
            for hit in hits
        ],
    }
    return json.dumps(payload, sort_keys=True)
