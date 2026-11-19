import base64
import http.server
import os
import sys
import threading

import pytest

import director.core.sandbox.local as local_module
from director.core.sandbox.egress import EgressProxy, _token, host_allowed
from director.core.sandbox.isolation import (
    Bubblewrap,
    Policy,
    Seatbelt,
    detect,
)
from director.core.sandbox.local import LocalSandboxExecutor

ISOLATION = detect()
needs_isolation = pytest.mark.skipif(
    ISOLATION is None, reason="no sandbox-exec or working bwrap on this machine"
)


@pytest.fixture
def home(tmp_path, monkeypatch, isolated_skills_dir):
    """A fake home with a credential, a project .env and the skills folder inside it."""
    home = tmp_path / "home"
    (home / ".ssh").mkdir(parents=True)
    (home / ".ssh" / "id_ed25519").write_text("PRIVATE KEY")
    (home / "project").mkdir()
    (home / "project" / ".env").write_text("OPENAI_API_KEY=sk-secret")
    skills = home / ".agents" / "skills" / "demo"
    skills.mkdir(parents=True)
    (skills / "SKILL.md").write_text("---\nname: demo\ndescription: d\n---\nhello skill")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("SKILLS_DIR", str(home / ".agents" / "skills"))
    return home


@pytest.fixture
def sandbox(home):
    return LocalSandboxExecutor(timeout=60)


# ---- every local run ----


def test_home_and_temp_point_at_the_run_folder():
    sandbox = LocalSandboxExecutor(timeout=30, isolation="off")
    out = sandbox.run_bash('echo "$HOME|$TMPDIR|$(pwd -P)"').stdout.strip().split("|")
    assert out[0] == out[1] == out[2]


def test_isolation_off_reports_unisolated():
    assert LocalSandboxExecutor(isolation="off").isolated is False


# ---- Seatbelt / bubblewrap ----


@needs_isolation
def test_isolated_when_the_os_supports_it(sandbox):
    assert sandbox.isolated


@needs_isolation
def test_run_folder_is_writable_and_the_rest_is_not(sandbox, tmp_path):
    outside = tmp_path / "outside.txt"
    result = sandbox.run_bash(f"echo hi > inside.txt && cat inside.txt; echo x > {outside}")
    assert result.stdout.strip() == "hi"
    assert not outside.exists()


@needs_isolation
def test_credentials_and_other_projects_are_unreadable(sandbox, home):
    result = sandbox.run_bash(
        f"cat {home}/.ssh/id_ed25519; cat {home}/project/.env; ls {home}/project"
    )
    assert "PRIVATE KEY" not in result.stdout
    assert "sk-secret" not in result.stdout
    assert ".env" not in result.stdout


@needs_isolation
def test_directors_own_env_file_is_unreadable(home, tmp_path, monkeypatch):
    env_file = tmp_path / "backend.env"
    env_file.write_text("ANTHROPIC_API_KEY=sk-director")
    monkeypatch.setattr(local_module, "DIRECTOR_ENV_FILES", (str(env_file),))
    sandbox = LocalSandboxExecutor(timeout=60)
    assert "sk-director" not in sandbox.run_bash(f"cat {env_file}").stdout


@needs_isolation
def test_skills_and_the_sdk_still_work(sandbox, home):
    skill = home / ".agents" / "skills" / "demo" / "SKILL.md"
    assert "hello skill" in sandbox.run_bash(f"cat {skill}").stdout
    result = sandbox.run_code("import videodb, json; print('ok')")
    assert result.ok and result.stdout.strip() == "ok"


# ---- network allowlist ----


@pytest.fixture
def web_server():
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            body = b"hello from origin"
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield server.server_address[1]
    server.shutdown()


def fetch(url):
    return (
        "import urllib.request\n"
        "try:\n"
        f"    print(urllib.request.urlopen({url!r}, timeout=10).read().decode())\n"
        "except Exception as e:\n"
        "    print('failed', e)\n"
    )


@needs_isolation
def test_allowlisted_hosts_go_through_the_proxy(home, web_server):
    sandbox = LocalSandboxExecutor(timeout=60, network="allowlist", allowed_hosts=["localhost"])
    result = sandbox.run_code(fetch(f"http://localhost:{web_server}/"))
    assert result.stdout.strip() == "hello from origin"


@needs_isolation
def test_other_hosts_are_blocked_and_reported(home):
    sandbox = LocalSandboxExecutor(timeout=60, network="allowlist", allowed_hosts=["localhost"])
    result = sandbox.run_code(fetch("http://blocked.example/"))
    assert "failed" in result.stdout
    assert "blocked: blocked.example" in result.stderr


@needs_isolation
def test_code_that_ignores_the_proxy_cannot_connect(home, web_server):
    sandbox = LocalSandboxExecutor(timeout=60, network="allowlist", allowed_hosts=["localhost"])
    code = (
        "import socket\n"
        "try:\n"
        f"    socket.create_connection(('127.0.0.1', {web_server}), timeout=5)\n"
        "    print('connected')\n"
        "except OSError as e:\n"
        "    print('refused', e)\n"
    )
    assert sandbox.run_code(code).stdout.startswith("refused")


def test_host_patterns():
    allowed = ["api.videodb.io", "*.cdn.example"]
    assert host_allowed("api.videodb.io", allowed)
    assert host_allowed("API.videodb.io.", allowed)
    assert host_allowed("a.b.cdn.example", allowed)
    assert not host_allowed("cdn.example", allowed)
    assert not host_allowed("evil-api.videodb.io", allowed)
    assert not host_allowed("api.videodb.io.evil.com", allowed)


def test_run_token_is_the_proxy_password():
    header = "Basic " + base64.b64encode(b"run:abc123").decode()
    assert _token(header) == "abc123"
    assert _token("Bearer x") is None


def test_blocked_hosts_are_kept_per_run():
    proxy = EgressProxy(["ok.example"])
    first, second = proxy.open_run(), proxy.open_run()
    assert not proxy.check(first, "bad.example")
    assert proxy.check(second, "ok.example")
    assert proxy.close_run(first) == ["bad.example"]
    assert proxy.close_run(second) == []


# ---- the wrappers themselves ----


def test_seatbelt_profile_hides_home_but_keeps_needed_folders(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / "venv").mkdir(parents=True)
    (home / ".ssh").mkdir()
    monkeypatch.setenv("HOME", str(home))
    real = os.path.realpath(home)
    profile = Seatbelt().profile(
        str(tmp_path / "run"),
        Policy(
            hidden=[str(home / ".ssh")],
            readable=[str(home / "venv"), str(home)],
            proxy_port=4000,
        ),
    )
    assert f'(deny file-read-data (subpath "{real}"))' in profile
    assert f'(allow file-read-data (subpath "{real}/venv"))' in profile
    # Home itself is never re-allowed, even when a PATH entry points at it.
    assert f'(allow file-read-data (subpath "{real}"))' not in profile
    assert profile.index(f'(subpath "{real}/.ssh")') > profile.index("allow file-read-data")
    assert '(allow network-outbound (remote ip "localhost:4000"))' in profile


def test_bubblewrap_args_hide_home_and_bridge_the_proxy(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / "venv").mkdir(parents=True)
    (home / ".ssh").mkdir()
    monkeypatch.setenv("HOME", str(home))
    real = os.path.realpath(home)
    workdir = str(tmp_path / "run")
    args = Bubblewrap("/usr/bin/bwrap").wrap(
        ["bash", "-c", "true"],
        workdir,
        Policy(
            hidden=[str(home / ".ssh")],
            readable=[str(home / "venv"), str(home)],
            proxy_socket=str(tmp_path / "egress" / "proxy.sock"),
        ),
    )
    joined = " ".join(args)
    assert f"--tmpfs {real}" in joined
    assert f"--ro-bind {real}/venv {real}/venv" in joined
    assert f"--ro-bind {real} {real}" not in joined
    assert f"--bind {workdir} {workdir}" in joined
    assert joined.index(f"--tmpfs {real}/.ssh") > joined.index(f"--ro-bind {real}/venv")
    assert "--unshare-net" in args
    assert args[args.index("--") + 1 :][:2] == [sys.executable, args[args.index("--") + 2]]
    assert args[-3:] == ["bash", "-c", "true"]
