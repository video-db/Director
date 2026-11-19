import os
import sys
import time

import pytest

import director.skill_library as skill_library
from director.core.sandbox.isolation import detect
from director.core.sandbox.local import LocalSandboxExecutor
from director.skill_library import manage_problem
from director.skill_library.folder_store import FolderStore
from director.skill_library.ports import SkillError, StagedSkill
from director.skill_library.service import SkillLibrary
from director.skill_library.skills_cli import (
    SkillsCliSource,
    check_source,
    parse_find,
)

FAKE_CLI = f"{sys.executable} {os.path.join(os.path.dirname(__file__), 'fake_skills_cli.py')}"


def write_skill(folder, name, description="A skill."):
    os.makedirs(folder / name, exist_ok=True)
    front = f"name: {name}\n" + (f"description: {description}\n" if description else "")
    (folder / name / "SKILL.md").write_text(f"---\n{front}---\nbody of {name}\n")


@pytest.fixture
def skills_dir(isolated_skills_dir):
    return isolated_skills_dir


@pytest.fixture
def library(skills_dir):
    return SkillLibrary(
        store=lambda: FolderStore(str(skills_dir)),
        source=SkillsCliSource(FAKE_CLI),
        required=[("acme/skills", "hello")],
    )


def wait(job, library):
    for _ in range(200):
        job = library.job(job["id"])
        if job["status"] != "running":
            return job
        time.sleep(0.05)
    raise AssertionError("job didn't finish")


# ---- folder store ----


def test_lists_skills_and_explains_broken_ones(skills_dir):
    write_skill(skills_dir, "good")
    write_skill(skills_dir, "broken", description=None)
    skills = {s.name: s for s in FolderStore(str(skills_dir)).list()}
    assert skills["good"].problem is None and skills["good"].description == "A skill."
    assert "no description" in skills["broken"].problem


def test_publish_replaces_and_records_the_source(skills_dir, tmp_path):
    write_skill(tmp_path / "staged", "demo", description="New.")
    store = FolderStore(str(skills_dir))
    store.publish(StagedSkill(name="demo", path=str(tmp_path / "staged" / "demo"), source="acme/skills"))
    skill = store.list()[0]
    assert (skill.name, skill.description, skill.source) == ("demo", "New.", "acme/skills")
    assert not [e for e in os.listdir(skills_dir) if e.startswith(".demo")]  # no leftovers


def test_removing_a_linked_skill_keeps_its_target(skills_dir, tmp_path):
    write_skill(tmp_path / "elsewhere", "linked")
    os.symlink(tmp_path / "elsewhere" / "linked", skills_dir / "linked")
    store = FolderStore(str(skills_dir))
    assert store.list()[0].linked
    store.remove("linked")
    assert not os.path.lexists(skills_dir / "linked")
    assert (tmp_path / "elsewhere" / "linked" / "SKILL.md").exists()


@pytest.mark.parametrize("name", ["../x", "..", ".director-skills.json", "a/b", "missing"])
def test_names_outside_the_folder_are_refused(skills_dir, name):
    with pytest.raises(SkillError):
        FolderStore(str(skills_dir)).remove(name)


# ---- skills CLI adapter ----


def test_find_output_is_parsed_with_colours_and_links():
    text = (
        "\x1b[38;5;145mvideo-db/skills@videodb\x1b[0m \x1b[36m1.7K installs\x1b[0m\n"
        "\x1b[38;5;102m└ https://skills.sh/video-db/skills/videodb\x1b[0m\n\n"
        "tusharkrbarman/skills-for-open-code@videodb 17 installs\n"
        "└ https://skills.sh/tusharkrbarman/skills-for-open-code/videodb\n"
    )
    entries = parse_find(text)
    assert [(e.source, e.skill, e.installs) for e in entries] == [
        ("video-db/skills", "videodb", "1.7K"),
        ("tusharkrbarman/skills-for-open-code", "videodb", "17"),
    ]
    assert entries[0].url == "https://skills.sh/video-db/skills/videodb"


@pytest.mark.parametrize("source", ["-rf", "a/b;rm -rf /", "../x", "a", "http://github.com/a/b", "a/b/c"])
def test_bad_sources_are_refused(source):
    with pytest.raises(SkillError):
        check_source(source)


def test_github_urls_are_accepted():
    assert check_source("https://github.com/video-db/skills") == "https://github.com/video-db/skills"


def test_missing_cli_is_reported():
    problem = SkillsCliSource("definitely-not-a-real-command-xyz skills").available()
    assert "isn't installed" in problem


# ---- the service ----


def test_search_and_preview(library):
    results = library.search("hello")
    assert results[0] == {
        "source": "acme/skills",
        "skill": "hello",
        "installs": "1.2K",
        "url": "https://skills.sh/acme/skills/hello",
    }
    assert "HELLO BODY" in library.preview("acme/skills", "hello")


def test_install_update_remove(library, skills_dir, monkeypatch):
    assert library.overview(None)["missing_required"] == [{"source": "acme/skills", "skill": "hello"}]

    job = wait(library.install("acme/skills", "hello"), library)
    assert job["status"] == "done" and job["result"]["security"] == {"gen": "safe"}
    assert "v1" in library.read("hello")
    assert library.overview(None)["missing_required"] == []

    library.source = SkillsCliSource(FAKE_CLI + " --fake-version 2")
    assert wait(library.update("hello"), library)["status"] == "done"
    assert "v2" in library.read("hello")

    library.remove("hello")
    assert library.overview(None)["skills"] == []


def test_failed_install_reports_why(library):
    job = wait(library.install("acme/skills", "nope"), library)
    assert job["status"] == "failed" and "No skill nope" in job["error"]


def test_skills_installed_outside_director_are_left_alone(library, skills_dir):
    write_skill(skills_dir, "hello")
    with pytest.raises(SkillError, match="outside Director"):
        library.install("acme/skills", "hello")
    with pytest.raises(SkillError, match="outside Director"):
        library.update("hello")


def test_staging_folder_is_deleted(library, monkeypatch, tmp_path):
    made = []
    real = skill_library.service.tempfile.mkdtemp
    monkeypatch.setattr(
        skill_library.service.tempfile, "mkdtemp", lambda **kw: made.append(real(**kw)) or made[-1]
    )
    wait(library.install("acme/skills", "hello"), library)
    assert made and not os.path.exists(made[0])


# ---- who may manage skills ----


class FakeSandbox:
    def __init__(self, location):
        self.skills_location = location


def test_manage_rules(monkeypatch):
    monkeypatch.delenv("DIRECTOR_SKILLS_MANAGE", raising=False)
    assert manage_problem(FakeSandbox("host"), "127.0.0.1") is None
    assert manage_problem(FakeSandbox("host"), "localhost") is None
    assert "Modal" in manage_problem(FakeSandbox("image"), "127.0.0.1")
    assert "DIRECTOR_SKILLS_MANAGE" in manage_problem(FakeSandbox("host"), "0.0.0.0")
    monkeypatch.setenv("DIRECTOR_SKILLS_MANAGE", "1")
    assert manage_problem(FakeSandbox("host"), "0.0.0.0") is None


@pytest.mark.skipif(detect() is None, reason="no OS sandbox on this machine")
def test_sandboxed_code_cannot_install_skills(skills_dir):
    sandbox = LocalSandboxExecutor(timeout=30)
    result = sandbox.run_bash(f"mkdir {skills_dir}/evil; echo x > {skills_dir}/evil/SKILL.md")
    assert not os.path.exists(skills_dir / "evil")
    assert result.exit_code != 0


# ---- routes ----


@pytest.fixture
def client(monkeypatch, tmp_path, skills_dir):
    from director.db.sqlite.initialize import initialize_sqlite
    from director.entrypoint.api import create_app
    from director.entrypoint.api.server import LocalAppConfig

    db_path = str(tmp_path / "director.db")
    initialize_sqlite(db_path)
    monkeypatch.setenv("SQLITE_DB_PATH", db_path)
    monkeypatch.setenv("SERVER_DB_TYPE", "sqlite")
    monkeypatch.setenv("SKILLS_CLI", FAKE_CLI)
    monkeypatch.delenv("SERVER_HOST", raising=False)
    monkeypatch.delenv("DIRECTOR_SKILLS_MANAGE", raising=False)
    skill_library.get_library.cache_clear()
    yield create_app(app_config=LocalAppConfig).test_client()
    skill_library.get_library.cache_clear()


def test_routes_install_and_list(client):
    assert client.get("/skills").json["manage"]["enabled"]
    job = client.post("/skills/install", json={"source": "acme/skills", "skill": "hello"})
    assert job.status_code == 202
    for _ in range(200):
        state = client.get(f"/skills/jobs/{job.json['id']}").json
        if state["status"] != "running":
            break
        time.sleep(0.05)
    assert state["status"] == "done"
    assert [s["name"] for s in client.get("/skills").json["skills"]] == ["hello"]
    assert "HELLO BODY" in client.get("/skills/installed/hello").json["content"]
    assert client.delete("/skills/installed/hello").status_code == 200
    assert client.get("/skills/installed/hello").status_code == 400


def test_routes_refuse_changes_when_exposed(client, monkeypatch):
    monkeypatch.setenv("SERVER_HOST", "0.0.0.0")
    assert not client.get("/skills").json["manage"]["enabled"]
    response = client.post("/skills/install", json={"source": "acme/skills", "skill": "hello"})
    assert response.status_code == 403
    assert client.get("/skills/search?q=x").status_code == 403
