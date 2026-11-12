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
