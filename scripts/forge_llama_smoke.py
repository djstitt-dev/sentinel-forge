#!/usr/bin/env python3
"""Explicit opt-in, bounded loopback llama smoke. No ordinary test discovery.

Run from the repository: python3 scripts/forge_llama_smoke.py --run
Exit 0 = passed; 77 = not opted in / model unavailable; 1 = inference/start failure.
No prompt, response text, child output, or model path is logged.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sentinel_forge.persistent_model import PersistentLocalModel, PersistentModelConfig


def run(args):
    if not args.run:
        return {'status': 'unavailable', 'reason': 'explicit --run required'}, 77
    if not args.executable.is_file() or not os.access(args.executable, os.X_OK) or not args.model.is_file():
        return {'status': 'unavailable', 'reason': 'executable or model missing'}, 77
    # Ephemeral selection does not claim atomic reservation across child exec.
    try:
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            port = probe.getsockname()[1]
    except OSError:
        return {'status': 'unavailable', 'reason': 'loopback socket unavailable',
                'child_started': False}, 77
    model = PersistentLocalModel(PersistentModelConfig(
        str(args.executable.resolve()), str(args.model.resolve()), port=port,
        startup_seconds=120, timeout_seconds=60, max_tokens=32,
    ))
    started = time.monotonic()
    old_alarm = signal.getsignal(signal.SIGALRM)
    old_term = signal.getsignal(signal.SIGTERM)

    def deadline(signum, frame):
        raise TimeoutError('smoke deadline or termination')

    signal.signal(signal.SIGALRM, deadline)
    signal.signal(signal.SIGTERM, deadline)
    signal.setitimer(signal.ITIMER_REAL, 180)
    result = {'status': 'failure'}
    code = 1
    try:
        response = model.respond('Reply with the single word READY.', '')
        result = {'status': 'passed', 'response_chars': len(response),
                  'response_sha256': hashlib.sha256(response.encode()).hexdigest(),
                  'semantic_ready': response.strip().rstrip('.').upper() == 'READY'}
        if not result['semantic_ready']:
            result['status'] = 'failure'
        else:
            code = 0
    except (Exception, KeyboardInterrupt) as exc:
        result = {'status': 'failure', 'reason': type(exc).__name__}
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        try:
            model.close()
        finally:
            signal.signal(signal.SIGALRM, old_alarm)
            signal.signal(signal.SIGTERM, old_term)
    result.update(elapsed_seconds=round(time.monotonic()-started, 3),
                  child_reaped=model._process is None,
                  child_exit_code=model.last_exit_code, diagnostics=model.diagnostics)
    # Check for an active listener after reap without touching another process.
    with socket.socket() as probe:
        probe.settimeout(1)
        result['port_released'] = probe.connect_ex(('127.0.0.1', port)) != 0
    if not result['port_released'] or not result['child_reaped']:
        result['status'] = 'failure'
        code = 1
    return result, code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--executable', type=Path, default=Path('/usr/bin/llama-server'))
    parser.add_argument('--model', type=Path, default=ROOT/'models/qwen3-8b/Qwen3-8B-Q4_K_M.gguf')
    args = parser.parse_args()
    result, code = run(args)
    result['context'] = 'CODEX SANDBOX CONTEXT'
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
