import os
from types import SimpleNamespace

import pytest

from director.core.context import ContextBuilder
from director.core.sandbox import LocalSandboxExecutor, ModalSandboxExecutor
from director.core.session import InputMessage, Session
from director.core.skills import (
    VIDEODB_SKILL_INSTALL,
    get_skills_dir,
    load_skills,
    format_skills_for_prompt,
)


def write_skill(root, name, frontmatter):
    skill_dir = root / name
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(f"---\n{frontmatter}\n---\n\n# {name}\n")
    return skill_dir


@pytest.fixture
def local():
    return LocalSandboxExecutor()


def test_skills_dir_defaults_to_agents_folder_and_expands_home(monkeypatch):
    monkeypatch.delenv("SKILLS_DIR")
    assert get_skills_dir() == os.path.join(
        os.path.expanduser("~"), ".agents", "skills"
    )

    monkeypatch.setenv("SKILLS_DIR", "~/my-skills")
    assert get_skills_dir() == os.path.join(os.path.expanduser("~"), "my-skills")


def test_load_skills_reads_the_configured_folder(isolated_skills_dir):
    write_skill(
        isolated_skills_dir, "videodb", "name: videodb\ndescription: Use VideoDB"
    )
    write_skill(
        isolated_skills_dir,
        "long-desc",
        "name: long-desc\ndescription: >\n  First line\n  second line",
    )
    write_skill(isolated_skills_dir, "no-desc", "name: no-desc")
    (isolated_skills_dir / "not-a-skill").mkdir()

    skills = {s.name: s for s in load_skills()}

    assert set(skills) == {"videodb", "long-desc"}
    assert skills["long-desc"].description == "First line second line"
    assert skills["videodb"].file_path == str(
        isolated_skills_dir / "videodb" / "SKILL.md"
    )


def test_load_skills_follows_symlinked_skills(isolated_skills_dir, tmp_path):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    write_skill(elsewhere, "linked", "name: linked\ndescription: From a symlink")
    os.symlink(elsewhere / "linked", isolated_skills_dir / "linked")

    assert [s.name for s in load_skills()] == ["linked"]


def test_missing_folder_means_no_skills(monkeypatch, tmp_path):
    monkeypatch.setenv("SKILLS_DIR", str(tmp_path / "does-not-exist"))
    assert load_skills() == []


def test_prompt_lists_skills_with_local_paths(isolated_skills_dir, local):
    write_skill(
        isolated_skills_dir, "videodb", "name: videodb\ndescription: Use VideoDB"
    )
    write_skill(
        isolated_skills_dir,
        "hidden",
        "name: hidden\ndescription: Not for the model\ndisable-model-invocation: true",
    )
    skills_dir = str(isolated_skills_dir)

    block = format_skills_for_prompt(load_skills(), skills_dir, local)

    location = (isolated_skills_dir / "videodb" / "SKILL.md").as_posix()
    assert f"<location>{location}</location>" in block
    assert "<name>hidden</name>" not in block
    assert "VideoDB skill missing" not in block


def test_prompt_maps_paths_into_the_modal_image(isolated_skills_dir):
    write_skill(
        isolated_skills_dir, "videodb", "name: videodb\ndescription: Use VideoDB"
    )
    modal_sandbox = ModalSandboxExecutor.__new__(ModalSandboxExecutor)
    modal_sandbox._skills_dir = "/opt/skills"

    block = format_skills_for_prompt(
        load_skills(), str(isolated_skills_dir), modal_sandbox
    )

    assert "<location>/opt/skills/videodb/SKILL.md</location>" in block
    assert "<base_dir>/opt/skills/videodb</base_dir>" in block


def test_missing_videodb_skill_tells_the_user_how_to_install(
    isolated_skills_dir, local
):
    write_skill(
        isolated_skills_dir, "other", "name: other\ndescription: Something else"
    )

    block = format_skills_for_prompt(load_skills(), str(isolated_skills_dir), local)

    assert "VideoDB skill missing" in block
    assert VIDEODB_SKILL_INSTALL in block
    assert "<name>other</name>" in block


def test_empty_folder_still_asks_for_the_videodb_skill(isolated_skills_dir, local):
    block = format_skills_for_prompt([], str(isolated_skills_dir), local)
    assert VIDEODB_SKILL_INSTALL in block
    assert "<available_skills>" not in block


def build_system_prompt(db, sandbox):
    session = Session(db=db, session_id="s-1")
    session.sandbox = sandbox
    session.state["collection"] = SimpleNamespace(
        name="default", id="c-1", description=""
    )
    message = InputMessage(
        db=db, session_id="s-1", conv_id="c-1", content=[{"type": "text", "text": "hi"}]
    )
    return ContextBuilder().build(session, message)[0].content


def test_context_has_no_skills_without_a_sandbox(db, isolated_skills_dir):
    write_skill(
        isolated_skills_dir, "videodb", "name: videodb\ndescription: Use VideoDB"
    )
    prompt = build_system_prompt(db, None)
    assert "<available_skills>" not in prompt
    assert "VideoDB skill missing" not in prompt


def test_new_skill_shows_up_on_the_next_turn(db, isolated_skills_dir, local):
    write_skill(
        isolated_skills_dir, "videodb", "name: videodb\ndescription: Use VideoDB"
    )
    assert "<name>fresh</name>" not in build_system_prompt(db, local)

    write_skill(isolated_skills_dir, "fresh", "name: fresh\ndescription: Just added")
    assert "<name>fresh</name>" in build_system_prompt(db, local)
