"""Static checks on the bash and Python the model wants to run.

Read-only is proven with allowlists: anything not on a list is not read-only
and goes through the mode, so a missing entry costs a prompt, never a silent write.
"""

import ast
import os
import re
import shlex
from typing import List, Optional

from director.core.permissions import CallInfo

# ---- bash ----

READ_ONLY_COMMANDS = {
    "ls", "cat", "head", "tail", "grep", "egrep", "fgrep", "wc", "pwd", "echo",
    "which", "file", "stat", "du", "df", "find", "tree", "sort", "uniq", "cut",
    "diff", "basename", "dirname", "realpath", "date", "ffprobe", "true",
}  # fmt: skip

# Flags that turn a read-only command into one that writes or runs things.
WRITING_FLAGS = {
    "find": {"-exec", "-execdir", "-ok", "-okdir", "-delete", "-fprint", "-fprintf", "-fls"},
    "sort": {"-o", "--output"},
    "tree": {"-o"},
}  # fmt: skip

SEPARATORS = {"&&", "||", ";", "|", "&", "|&"}
BLOCKED_COMMANDS = {"sudo", "su", "doas", "shutdown", "reboot", "halt", "poweroff"}
PROTECTED_TARGETS = {"/", "/*", "~", "~/", "~/*", "$HOME", "$HOME/", "$HOME/*"}
INTERPRETERS = {"sh", "bash", "zsh", "python", "python3", "perl", "node"}
PIPE_TO_SHELL = re.compile(
    r"\b(curl|wget)\b[^|;&]*\|\s*(sudo\s+)?(sh|bash|zsh|python3?|perl|node)\b"
)
UNPARSEABLE = "Uses shell features Director can't check (command substitution, subshells or unbalanced quotes)."


def split_bash(command: str) -> Optional[List[List[str]]]:
    """Split a command into simple segments, or None when it can't be checked."""
    if any(s in command for s in ("`", "$(", "<(", ">(")):
        return None
    lexer = shlex.shlex(
        command.replace("\n", " ; "), posix=True, punctuation_chars=True
    )
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:
        return None
    segments: List[List[str]] = [[]]
    for token in tokens:
        if token in ("(", ")"):
            return None
        if token in SEPARATORS:
            segments.append([])
        else:
            segments[-1].append(token)
    return [s for s in segments if s]


def _is_redirect(token: str) -> bool:
    return bool(token) and set(token) <= set("<>&") and token not in SEPARATORS


def _command(segment: List[str]):
    """Skip leading VAR=value assignments; return (name, args)."""
    i = 0
    while i < len(segment) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", segment[i]):
        i += 1
    if i >= len(segment):
        return "", []
    return os.path.basename(segment[i]), segment[i + 1 :]


def _inside(path: str, root: str) -> bool:
    real = os.path.realpath(os.path.expanduser(path))
    return real == root or real.startswith(root.rstrip(os.sep) + os.sep)


def _outside_workdir(arg: str, skills_dir: str) -> bool:
    """True for a path that can reach beyond the run's temp folder or the skills folder."""
    value = arg.split("=", 1)[1] if arg.startswith("-") and "=" in arg else arg
    if "$" in value or ".." in value.split("/"):
        return True
    if value.startswith(("/", "~")):
        return not (skills_dir and _inside(value, skills_dir))
    return False


def inspect_bash(command: str, skills_dir: str = "") -> CallInfo:
    info = CallInfo(preview=command, language="bash")
    segments = split_bash(command)

    if segments is None:
        if re.search(r"(^|[\s;&|(`])(sudo|su|doas)\s", command):
            info.blocked = "Running as another user is blocked."
        info.risks.append(UNPARSEABLE)
        return info

    if PIPE_TO_SHELL.search(command):
        info.risks.append("Runs a script downloaded from the internet.")

    read_only = True
    key_parts = []
    for segment in segments:
        name, args = _command(segment)
        flags = {a for a in args if a.startswith("-")}

        if name in BLOCKED_COMMANDS or name.startswith("mkfs"):
            info.blocked = f"`{name}` is blocked."
            return info
        if name == "rm":
            targets = [a for a in args if not a.startswith("-")]
            recursive = any(
                f in flags for f in ("-r", "-R", "-rf", "-fr", "-Rf", "--recursive")
            )
            if recursive and any(t in PROTECTED_TARGETS for t in targets):
                info.blocked = "Deleting the root or home folder is blocked."
                return info
            if any(_outside_workdir(t, skills_dir) for t in targets):
                info.destructive = "Deletes files outside its working folder."

        redirect_targets = [
            segment[i + 1]
            for i, token in enumerate(segment[:-1])
            if _is_redirect(token) and not segment[i + 1].isdigit()
        ]
        if any(_outside_workdir(t, skills_dir) for t in redirect_targets):
            info.risks.append("Writes files outside its working folder.")

        if (
            name not in READ_ONLY_COMMANDS
            or flags & WRITING_FLAGS.get(name, set())
            or any(_is_redirect(t) for t in segment)
            or any(
                _outside_workdir(a, skills_dir)
                for a in args
                if not a.startswith("-") or "=" in a
            )
        ):
            read_only = False

        first = args[0] if args else ""
        key_parts.append(
            f"{name} {first}".strip()
            if name in INTERPRETERS or first.startswith("-") or first.isalpha()
            else name
        )

    info.read_only = read_only and not info.risks and not info.destructive
    info.key = "bash_executor:" + " | ".join(sorted(set(key_parts)))
    return info


# ---- python ----

# SDK calls that only issue GET requests (checked against videodb 0.3.0).
# get_transcript's GET returns an existing transcript and never generates one,
# so `force` is safe here. Methods not listed (generate_url is a POST) are not read-only.
READ_CALLS = {
    "get_collection", "get_collections", "get_video", "get_videos",
    "get_audio", "get_audios", "get_image", "get_images", "get_thumbnails",
    "get_transcript", "get_transcript_text", "get_scenes", "get_scene_index",
    "list_scene_index", "get_scene_collection", "list_scene_collection",
    "get_rtstream", "list_rtstreams", "list_events", "get_invoices",
}  # fmt: skip

SAFE_METHODS = {
    # str / list / dict / set
    "append", "extend", "insert", "items", "keys", "values", "get", "setdefault",
    "join", "split", "rsplit", "strip", "lstrip", "rstrip", "lower", "upper",
    "title", "startswith", "endswith", "format", "replace", "count", "index",
    "find", "sort", "copy", "add", "isdigit", "splitlines",
    # json / os
    "dumps", "loads", "getenv",
}  # fmt: skip

SAFE_BUILTINS = {
    "print", "len", "str", "int", "float", "bool", "round", "abs", "sorted",
    "reversed", "list", "dict", "set", "tuple", "enumerate", "zip", "range",
    "min", "max", "sum", "any", "all", "isinstance", "repr", "map", "filter",
}  # fmt: skip

SAFE_IMPORTS = {"json", "os", "videodb"}
DYNAMIC = {
    "getattr",
    "setattr",
    "delattr",
    "eval",
    "exec",
    "compile",
    "__import__",
    "globals",
    "locals",
    "vars",
}
SHELL_CALLS = {
    "system",
    "popen",
    "spawn",
    "run",
    "call",
    "check_call",
    "check_output",
    "Popen",
    "execv",
    "execvp",
}
NETWORK_MODULES = {
    "requests",
    "urllib",
    "httpx",
    "socket",
    "http",
    "aiohttp",
    "ftplib",
    "smtplib",
}
LOCAL_DELETES = {"rmtree", "unlink", "rmdir", "removedirs"}


def _is_destructive(name: str) -> bool:
    return name == "delete" or name.startswith(("delete_", "remove_"))


def _literal_attr(call: ast.Call) -> Optional[str]:
    """The attribute name of getattr/hasattr when it's a plain string literal."""
    if len(call.args) >= 2:
        arg = call.args[1]
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
    return None


def inspect_python(code: str) -> CallInfo:
    info = CallInfo(preview=code, language="python")
    try:
        tree = ast.parse(code)
    except SyntaxError:
        info.risks.append("The code doesn't parse.")
        return info

    read_only = True
    dynamic = False
    # Calling a function defined in the snippet is fine: its body is scanned too.
    defined = {
        n.name
        for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    ops = set()

    def risk(text):
        if text not in info.risks:
            info.risks.append(text)

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = (
                [a.name.split(".")[0] for a in node.names]
                if isinstance(node, ast.Import)
                else [(node.module or "").split(".")[0]]
            )
            for module in modules:
                if module in NETWORK_MODULES:
                    risk("Makes its own network requests.")
                if module in ("subprocess", "pty"):
                    risk("Runs shell commands.")
                if module not in SAFE_IMPORTS:
                    read_only = False

        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("_"):
                risk("Uses private internals the scan can't follow.")
                dynamic = True

        elif isinstance(node, ast.Call):
            if any(isinstance(k, ast.keyword) and k.arg is None for k in node.keywords):
                read_only = False  # **kwargs can hide arguments
            func = node.func

            if isinstance(func, ast.Name):
                name = func.id
                if name in ("getattr", "hasattr") and _literal_attr(node):
                    # getattr(x, "name", None) is just x.name with a fallback.
                    attr = _literal_attr(node)
                    if attr.startswith("_"):
                        risk("Uses private internals the scan can't follow.")
                        dynamic = True
                    elif _is_destructive(attr):
                        info.destructive = (
                            f"Calls `{attr}()`, which deletes data and can't be undone."
                        )
                elif name in DYNAMIC:
                    risk("Builds code at run time, which the scan can't follow.")
                    dynamic = True
                elif name == "open":
                    read_only = False
                    path = node.args[0] if node.args else None
                    if not (
                        isinstance(path, ast.Constant)
                        and isinstance(path.value, str)
                        and not path.value.startswith(("/", "~"))
                        and ".." not in path.value
                    ):
                        risk("Opens files outside its working folder.")
                elif name not in SAFE_BUILTINS and name not in defined:
                    read_only = False
                    ops.add(name)

            elif isinstance(func, ast.Attribute):
                name = func.attr
                if _is_destructive(name):
                    info.destructive = (
                        f"Calls `{name}()`, which deletes data and can't be undone."
                    )
                    ops.add(name)
                elif (
                    name in SHELL_CALLS
                    and isinstance(func.value, ast.Name)
                    and func.value.id in ("os", "subprocess")
                ):
                    risk("Runs shell commands.")
                elif name in LOCAL_DELETES or (
                    name == "remove"
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "os"
                ):
                    risk("Deletes local files.")
                if name in READ_CALLS:
                    ops.add(name)
                elif name not in SAFE_METHODS:
                    read_only = False
                    ops.add(name)
            else:
                read_only = False  # calling the result of an expression

    info.read_only = (
        read_only and not dynamic and not info.risks and not info.destructive
    )
    info.key = None if dynamic else "code_executor:" + ",".join(sorted(ops))
    return info
