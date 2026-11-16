"""Validates and runs generated Timeline code.

CodeExecutor starts this file as a separate process, so generated code never
shares memory or environment with the server. It imports only the standard
library and videodb.
"""

import ast
import builtins
import dis
import enum
import inspect
import json
import os
import sys
from functools import lru_cache

ALLOWED_IMPORT_MODULE = "videodb.editor"

# If these are missing the SDK changed shape and the allow-lists can't be trusted.
REQUIRED_SDK_NAMES = {"Timeline", "Track", "Clip", "add_track", "add_clip", "generate_stream"}  # fmt: skip

# Everything else (open, eval, exec, getattr, ...) is unavailable to generated code.
SAFE_BUILTIN_NAMES = (
    "abs", "all", "any", "bool", "dict", "enumerate", "float", "int",
    "isinstance", "len", "list", "max", "min", "print", "range", "round",
    "set", "sorted", "str", "sum", "tuple", "zip",
    "Exception", "KeyError", "IndexError", "TypeError", "ValueError",
)  # fmt: skip

# list, dict, str and enum attributes that Timeline code commonly uses.
COMMON_ATTRIBUTES = {
    "append", "extend", "items", "keys", "values", "join", "lower", "upper",
    "strip", "split", "replace", "value",
}  # fmt: skip


class UnsafeCodeError(ValueError):
    """Generated code uses something outside the Timeline subset."""


@lru_cache(maxsize=1)
def _sdk_surface() -> tuple:
    """(importable class names, allowed attribute names) read from videodb.editor.

    Imports are limited to the classes the module defines, so its own imports
    (json, upload helpers) are out of reach. Attributes are the public members,
    enum values and instance attributes of those classes.
    """
    from videodb import editor

    classes = {
        name: cls
        for name, cls in vars(editor).items()
        if inspect.isclass(cls)
        and cls.__module__ == editor.__name__
        and not name.startswith("_")
    }
    attributes = set(COMMON_ATTRIBUTES)
    for cls in classes.values():
        attributes.update(vars(cls))
        if issubclass(cls, enum.Enum):
            attributes.update(cls.__members__)
            continue
        # Instance attributes, read from bytecode so no source files are needed.
        for member in vars(cls).values():
            if inspect.isfunction(member):
                attributes.update(
                    op.argval
                    for op in dis.get_instructions(member)
                    if op.opname == "STORE_ATTR"
                )
    # Timeline keeps the connection it was given; generated code never needs it back.
    attributes.discard("connection")
    attributes = {name for name in attributes if not name.startswith("_")}

    missing = REQUIRED_SDK_NAMES - classes.keys() - attributes
    if missing:
        raise RuntimeError(f"videodb.editor is missing {sorted(missing)}")
    return frozenset(classes), frozenset(attributes)


class TimelineConnection:
    """The only part of the VideoDB connection that generated code can reach.

    Timeline posts to two editor paths and, for a large timeline, asks for an
    upload URL in its collection. The real connection, its HTTP session and the
    API key stay in the closure.
    """

    __slots__ = ("post", "get", "collection_id")

    def __init__(self, conn):
        from videodb._constants import ApiPath

        collection_id = getattr(conn, "collection_id", "default")
        post_paths = {ApiPath.editor, f"{ApiPath.editor}/{ApiPath.download}"}
        get_paths = {f"{ApiPath.collection}/{collection_id}/upload_url"}

        def post(path, data=None):
            if path not in post_paths:
                raise PermissionError(f"API path '{path}' is not allowed")
            return conn.post(path=path, data=data)

        def get(path, params=None):
            if path not in get_paths:
                raise PermissionError(f"API path '{path}' is not allowed")
            return conn.get(path=path, params=params)

        self.post = post
        self.get = get
        self.collection_id = collection_id


def validate_code(code: str) -> None:
    """Reject code that does more than build a Timeline with the videodb SDK."""
    classes, attributes = _sdk_surface()
    for node in ast.walk(ast.parse(code)):
        if isinstance(node, ast.Import):
            raise UnsafeCodeError("use 'from videodb.editor import ...' for imports")
        if isinstance(node, ast.ImportFrom):
            if node.level or node.module != ALLOWED_IMPORT_MODULE:
                raise UnsafeCodeError(f"import from '{node.module}' is not allowed")
            for alias in node.names:
                if alias.name not in classes:
                    raise UnsafeCodeError(f"import of '{alias.name}' is not allowed")
        elif isinstance(node, ast.ClassDef):
            raise UnsafeCodeError("class definitions are not allowed")
        elif isinstance(node, ast.Name) and node.id.startswith("_"):
            raise UnsafeCodeError(f"name '{node.id}' is not allowed")
        elif isinstance(node, ast.Attribute) and node.attr not in attributes:
            raise UnsafeCodeError(f"attribute '{node.attr}' is not allowed")


def _import_editor_only(name, globals=None, locals=None, fromlist=(), level=0):
    classes, _ = _sdk_surface()
    if level or name != ALLOWED_IMPORT_MODULE or not set(fromlist or ()) <= classes:
        raise ImportError(f"import of '{name}' is not allowed")
    return builtins.__import__(name, globals, locals, fromlist, level)


def _safe_builtins() -> dict:
    safe = {name: getattr(builtins, name) for name in SAFE_BUILTIN_NAMES}
    safe["__import__"] = _import_editor_only
    return safe


def run(code: str, conn) -> str:
    """Run validated Timeline code and return the stream_url it produced."""
    validate_code(code)
    exec_locals = {}
    exec(
        code,
        {"conn": TimelineConnection(conn), "__builtins__": _safe_builtins()},
        exec_locals,
    )
    stream_url = exec_locals.get("stream_url")
    return str(stream_url) if stream_url else None


def main() -> None:
    request = json.load(sys.stdin)
    # stdout carries the result, so anything the code prints goes to stderr.
    result_stream, sys.stdout = sys.stdout, sys.stderr
    try:
        import videodb

        conn = videodb.connect(
            api_key=os.environ["VIDEO_DB_API_KEY"], base_url=request["base_url"]
        )
        result = {"stream_url": run(request["code"], conn)}
    except Exception as e:
        result = {"error": str(e), "error_type": type(e).__name__}
    json.dump(result, result_stream)


if __name__ == "__main__":
    main()
