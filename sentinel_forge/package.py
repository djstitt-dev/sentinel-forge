"""Offline Forge candidate package construction and verification.

This module creates a deterministic logical manifest from local regular files.
It does not transfer, deploy, sign, authorize, or contact another component.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
from typing import Iterable

FORMAT = "sentinel-forge-candidate-manifest-v1"
DIGEST = "sha256"

class PackageError(ValueError):
    pass

@dataclass(frozen=True)
class FileIdentity:
    path: str
    size: int
    sha256: str

    def as_dict(self) -> dict[str, object]:
        return {"path": self.path, "size": self.size, "sha256": self.sha256}

@dataclass(frozen=True)
class CandidateManifest:
    work_package_revision: str
    artifact_type_class: str
    classification_handling: str
    source_component: str
    files: tuple[FileIdentity, ...]
    artifact_id: str
    integrity_reference: str
    integrity_provenance: str = "FORGE_LOCAL_SHA256"
    completeness_state: str = "COMPLETE"
    format: str = FORMAT

    def as_dict(self) -> dict[str, object]:
        return {
            "format": self.format,
            "work_package_revision": self.work_package_revision,
            "artifact_type_class": self.artifact_type_class,
            "classification_handling": self.classification_handling,
            "source_component": self.source_component,
            "files": [x.as_dict() for x in self.files],
            "artifact_id": self.artifact_id,
            "integrity_reference": self.integrity_reference,
            "integrity_provenance": self.integrity_provenance,
            "completeness_state": self.completeness_state,
        }

    def canonical_bytes(self) -> bytes:
        return _canonical(self.as_dict())

    def artifact_identity(self) -> dict[str, str]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type_class": self.artifact_type_class,
            "integrity_reference": self.integrity_reference,
            "integrity_provenance": self.integrity_provenance,
            "source_work_package_revision": self.work_package_revision,
            "source_component": self.source_component,
            "classification_handling": self.classification_handling,
            "completeness_state": self.completeness_state,
        }

def build_manifest(
    root: Path,
    relative_paths: Iterable[str],
    *,
    work_package_revision: str,
    artifact_type_class: str,
    classification_handling: str,
    source_component: str = "forge",
) -> CandidateManifest:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise PackageError("root must be a directory")
    names = sorted(set(relative_paths))
    if not names:
        raise PackageError("at least one artifact file is required")
    files = tuple(_identity(root, name) for name in names)
    core = {
        "format": FORMAT,
        "work_package_revision": _required(work_package_revision, "work_package_revision"),
        "artifact_type_class": _required(artifact_type_class, "artifact_type_class"),
        "classification_handling": _required(classification_handling, "classification_handling"),
        "source_component": _required(source_component, "source_component"),
        "files": [x.as_dict() for x in files],
    }
    digest = hashlib.sha256(_canonical(core)).hexdigest()
    reference = f"{DIGEST}:{digest}"
    return CandidateManifest(
        work_package_revision=core["work_package_revision"],
        artifact_type_class=core["artifact_type_class"],
        classification_handling=core["classification_handling"],
        source_component=core["source_component"],
        files=files,
        artifact_id=reference,
        integrity_reference=reference,
    )

def verify_manifest(root: Path, manifest: CandidateManifest) -> bool:
    rebuilt = build_manifest(
        root,
        [x.path for x in manifest.files],
        work_package_revision=manifest.work_package_revision,
        artifact_type_class=manifest.artifact_type_class,
        classification_handling=manifest.classification_handling,
        source_component=manifest.source_component,
    )
    return rebuilt == manifest

def _identity(root: Path, relative: str) -> FileIdentity:
    p = PurePosixPath(relative)
    if p.is_absolute() or not p.parts or any(part in ("", ".", "..") for part in p.parts):
        raise PackageError(f"unsafe artifact path: {relative!r}")
    candidate = root.joinpath(*p.parts)
    try:
        st_before = candidate.lstat()
    except OSError as exc:
        raise PackageError(f"cannot inspect artifact {relative!r}: {exc}") from exc
    if not stat.S_ISREG(st_before.st_mode) or st_before.st_nlink != 1:
        raise PackageError(f"artifact must be a single-link regular file: {relative!r}")
    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise PackageError(f"artifact escapes package root: {relative!r}") from exc
    h = hashlib.sha256()
    try:
        fd = os.open(candidate, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            st_open = os.fstat(fd)
            if not stat.S_ISREG(st_open.st_mode) or st_open.st_nlink != 1:
                raise PackageError(f"artifact changed type/link state before read: {relative!r}")
            opened_identity = (st_open.st_dev, st_open.st_ino, st_open.st_size, st_open.st_mtime_ns, st_open.st_mode)
            initial_identity = (st_before.st_dev, st_before.st_ino, st_before.st_size, st_before.st_mtime_ns, st_before.st_mode)
            if opened_identity != initial_identity:
                raise PackageError(f"artifact changed before hashing: {relative!r}")
            with os.fdopen(fd, "rb", closefd=False) as fh:
                while chunk := fh.read(1024 * 1024):
                    h.update(chunk)
            st_fd_after = os.fstat(fd)
        finally:
            os.close(fd)
    except PackageError:
        raise
    except OSError as exc:
        raise PackageError(f"cannot read artifact {relative!r}: {exc}") from exc
    st_path_after = candidate.lstat()
    final_fd_identity = (st_fd_after.st_dev, st_fd_after.st_ino, st_fd_after.st_size, st_fd_after.st_mtime_ns, st_fd_after.st_mode)
    final_path_identity = (st_path_after.st_dev, st_path_after.st_ino, st_path_after.st_size, st_path_after.st_mtime_ns, st_path_after.st_mode)
    if initial_identity != final_fd_identity or initial_identity != final_path_identity:
        raise PackageError(f"artifact changed while hashing: {relative!r}")
    return FileIdentity(p.as_posix(), st_fd_after.st_size, h.hexdigest())

def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")

def _required(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PackageError(f"{name} is required")
    return value
