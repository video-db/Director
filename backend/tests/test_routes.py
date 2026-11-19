def test_agent_route_is_gone_but_config_check_remains(monkeypatch, tmp_path):
    from director.db.sqlite.initialize import initialize_sqlite
    from director.entrypoint.api import create_app
    from director.entrypoint.api.server import LocalAppConfig

    db_path = str(tmp_path / "director.db")
    initialize_sqlite(db_path)
    monkeypatch.setenv("SQLITE_DB_PATH", db_path)
    monkeypatch.setenv("SERVER_DB_TYPE", "sqlite")
    client = create_app(app_config=LocalAppConfig).test_client()

    assert client.get("/agent").status_code == 404
    assert client.get("/config/check").status_code == 200


def make_client(monkeypatch, tmp_path, origins=None):
    from director.db.sqlite.initialize import initialize_sqlite
    from director.entrypoint.api import create_app
    from director.entrypoint.api.server import LocalAppConfig

    db_path = str(tmp_path / "director.db")
    initialize_sqlite(db_path)
    monkeypatch.setenv("SQLITE_DB_PATH", db_path)
    monkeypatch.setenv("SERVER_DB_TYPE", "sqlite")
    if origins is None:
        monkeypatch.delenv("SERVER_ALLOWED_ORIGINS", raising=False)
    else:
        monkeypatch.setenv("SERVER_ALLOWED_ORIGINS", origins)
    return create_app(app_config=LocalAppConfig).test_client()


def allowed_origin(client, origin):
    response = client.get("/config/check", headers={"Origin": origin})
    return response.headers.get("Access-Control-Allow-Origin")


def test_server_listens_on_loopback_by_default():
    from director.entrypoint.api.server import BaseAppConfig

    assert BaseAppConfig.HOST == "127.0.0.1"


def test_only_local_pages_may_call_the_api_by_default(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    assert allowed_origin(client, "http://localhost:8094") == "http://localhost:8094"
    assert allowed_origin(client, "http://127.0.0.1:8080") == "http://127.0.0.1:8080"
    assert allowed_origin(client, "https://evil.example") is None
    assert allowed_origin(client, "http://localhost.evil.example") is None


def test_configured_origins_replace_the_default(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path, "https://director.example.com")
    assert allowed_origin(client, "https://director.example.com") == "https://director.example.com"
    assert allowed_origin(client, "http://localhost:8080") is None


def test_socket_uses_the_same_origin_rule():
    from director.entrypoint.api import origin_check

    _, socket_rule = origin_check([])
    assert socket_rule("http://localhost:5173")
    assert not socket_rule("https://evil.example")
    assert not socket_rule(None)
    assert origin_check(["https://a.example"])[1] == ["https://a.example"]


def test_permission_rules_api(monkeypatch, tmp_path):
    from director.db.sqlite.db import SQLiteDB

    client = make_client(monkeypatch, tmp_path)
    SQLiteDB(str(tmp_path / "director.db")).add_permission_rule(
        rule_id="r1", agent="bash_executor", pattern="bash_executor:ffprobe", action="allow"
    )
    assert [r["rule_id"] for r in client.get("/config/permission-rules").json["rules"]] == ["r1"]
    assert client.delete("/config/permission-rules/r1").status_code == 200
    assert client.delete("/config/permission-rules/r1").status_code == 404
    assert client.get("/config/permission-rules").json["rules"] == []


def test_permissions_endpoint_reports_the_sandbox(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    body = client.get("/config/permissions").json
    assert body["default_mode"] in ("ask", "auto")
    assert body["default_mode"] in body["modes"]
