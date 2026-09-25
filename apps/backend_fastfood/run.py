# run.py
#
# Windows-compatible uvicorn launcher.
#
# psycopg (async) requires the SelectorEventLoop on Windows.
# uvicorn's default on Windows 3.8+ is ProactorEventLoop, which breaks psycopg.
# Setting the policy here — before uvicorn creates its event loop — fixes this.
#
# Usage:
#   python run.py                 (binds 0.0.0.0 → reachable from other devices, e.g. the tablet)
#   python run.py --reload        (development, auto-restarts on file change)
#   python run.py --host 127.0.0.1  (bind localhost only)

import asyncio
import os
import socket
import subprocess
import sys
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn


def _port_in_use(host: str, port: int) -> bool:
    """Pre-flight check so a stuck/duplicate instance fails with a clear,
    actionable message instead of uvicorn's raw Errno 10048/98 traceback."""
    probe_host = "127.0.0.1" if host in ("0.0.0.0", "::") else host
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((probe_host, port)) == 0


def _fail_port_in_use(host: str, port: int) -> None:
    print(f"\n{'=' * 64}")
    print(f"  ERROR: port {port} is already in use - another instance of this")
    print("  server (or something else) is already running on it.")
    print(f"{'=' * 64}")
    if sys.platform == "win32":
        print(f"  Find it:  netstat -ano | findstr :{port}")
        print("  Stop it:  taskkill /F /PID <pid from the last column above>")
    else:
        print(f"  Find it:  lsof -i :{port}          (or: fuser {port}/tcp)")
        print("  Stop it:  kill <pid>                (or: fuser -k {port}/tcp)".format(port=port))
    print("  Only one instance may bind this port at a time - starting a second")
    print("  one is never the fix; stop the existing one first.\n", flush=True)
    sys.exit(1)


def _lan_ip() -> str | None:
    """Best-effort primary LAN IPv4 (no traffic actually sent)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return None


def _print_banner(host: str, port: int) -> None:
    # 0.0.0.0 is a *bind* address — you cannot open it in a browser.
    # Show the URLs that actually work instead.
    urls = []
    if host in ("0.0.0.0", "127.0.0.1", "localhost", "::"):
        urls.append(f"http://localhost:{port}")
    if host == "0.0.0.0":
        ip = _lan_ip()
        if ip:
            urls.append(f"http://{ip}:{port}      (other devices on this network / the POS tablet)")
    if not urls:
        urls.append(f"http://{host}:{port}")

    line = "=" * 64
    print(f"\n{line}")
    print("  FastFood SaaS API - open one of these in your browser:")
    for u in urls:
        print(f"    {u}")
    base = urls[0].split()[0]
    print(f"\n    Platform dashboard : {base}/platform/login.html")
    print(f"    Tenant dashboard   : {base}/tenant/login.html")
    print(f"    API docs (Swagger) : {base}/docs")
    print(f"    Health check       : {base}/health")
    print(f"    Process ID (PID)   : {os.getpid()}   (save this - it's what you'd stop to restart the server)")
    print(f"{line}")
    print("  (uvicorn logs the bind address 0.0.0.0 below - that one is NOT clickable.)\n", flush=True)


def _prepare_database() -> None:
    """Apply migrations and create the first platform owner when DB is fresh."""
    project_root = Path(__file__).resolve().parent
    subprocess.run(
        [sys.executable, str(project_root / "scripts" / "prepare_database.py")],
        cwd=project_root,
        check=True,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Start the FastFood SaaS API server.")
    parser.add_argument("--host",   default="0.0.0.0",  help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port",   default=8000, type=int, help="Bind port (default: 8000)")
    parser.add_argument("--reload", action="store_true",   help="Enable auto-reload (development only)")
    parser.add_argument("--skip-db-prepare", action="store_true",
                        help="Skip automatic migrations/bootstrap (advanced use only)")
    args = parser.parse_args()

    if _port_in_use(args.host, args.port):
        _fail_port_in_use(args.host, args.port)

    if not args.skip_db_prepare:
        _prepare_database()

    _print_banner(args.host, args.port)

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
