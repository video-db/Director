"""Stands in for `npx skills` in tests: knows one repo, acme/skills, with one skill, `hello`."""

import json
import os
import sys

SKILLS = {
    "hello": "---\nname: hello\ndescription: Says hello.\n---\nHELLO BODY v{version}\n",
}


def main(args):
    version = "1"
    if args[:1] == ["--fake-version"]:
        version, args = args[1], args[2:]
    if args == ["--version"]:
        print("9.9.9")
    elif args[0] == "find":
        print("\x1b[38;5;102mInstall with npx skills add <owner/repo@skill>\x1b[0m\n")
        print("\x1b[38;5;145macme/skills@hello\x1b[0m \x1b[36m1.2K installs\x1b[0m")
        print("\x1b[38;5;102m└ https://skills.sh/acme/skills/hello\x1b[0m\n")
        print("other/repo@hello-world 7 installs")
        print("└ https://skills.sh/other/repo/hello-world")
    elif args[0] == "use":
        source, _, skill = args[1].partition("@")
        if source != "acme/skills" or skill not in SKILLS:
            print(f"No skill {skill}", file=sys.stderr)
            sys.exit(1)
        print("You are being given a Skill.\n\n<SKILL.md>\n" + SKILLS[skill].format(version=version) + "</SKILL.md>")
    elif args[0] == "add":
        source, skill = args[1], args[args.index("--skill") + 1]
        assert "-a" in args and args[args.index("-a") + 1] == "universal"
        if source != "acme/skills" or skill not in SKILLS:
            print(json.dumps([{"status": "failed", "name": skill, "error": f"No skill {skill} in {source}"}]))
            return
        path = os.path.join(os.getcwd(), ".agents", "skills", skill)
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, "SKILL.md"), "w") as f:
            f.write(SKILLS[skill].format(version=version))
        print("progress noise\n" + json.dumps([{"status": "installed", "name": skill, "path": path,
                                                "security": {"gen": "safe"}}]))
    else:
        sys.exit(2)


if __name__ == "__main__":
    main(sys.argv[1:])
