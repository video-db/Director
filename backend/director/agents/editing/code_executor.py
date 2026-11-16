import ast
import builtins
import dis
import enum
import inspect
import logging
from functools import lru_cache

from director.agents.base import AgentResponse, AgentStatus

logger = logging.getLogger(__name__)

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


class CodeExecutor:
    """Runs generated Timeline code after checking it only uses the videodb SDK.

    The check narrows what generated code can reach; it is not a sandbox.
    """

    def __init__(self, session):
        self.session = session

    def execute_code(self, code: str, description: str = "") -> AgentResponse:
        try:
            conn = self.session.state.get("conn")
            if not conn:
                raise ValueError("No VideoDB connection available in session")

            validate_code(code)

            exec_globals = {
                "conn": TimelineConnection(conn),
                "__builtins__": _safe_builtins(),
            }
            exec_locals = {}

            logger.info("Executing generated code.")
            stream_url = self._execute_with_retry(code, exec_globals, exec_locals)

            if not stream_url:
                raise ValueError("Generated code did not produce a stream_url variable")

            data = {
                "stream_url": stream_url,
                "generated_code": code,
                "description": description,
                "execution_success": True,
            }

            return AgentResponse(
                data=data,
                message=f"Timeline code executed successfully{': ' + description if description else ''}",
                status=AgentStatus.SUCCESS,
            )

        except SyntaxError as e:
            logger.exception(f"Syntax error in generated code: {e}")
            return AgentResponse(
                data={
                    "code": code,
                    "error": str(e),
                    "error_type": "SyntaxError",
                    "line_number": e.lineno,
                    "execution_success": False,
                },
                message=f"Syntax error in generated code at line {e.lineno}: {str(e)}",
                status=AgentStatus.ERROR,
            )

        except NameError as e:
            logger.exception(f"Name error in generated code: {e}")
            return AgentResponse(
                data={
                    "code": code,
                    "error": str(e),
                    "error_type": "NameError",
                    "execution_success": False,
                },
                message=f"Name error in generated code: {str(e)}",
                status=AgentStatus.ERROR,
            )

        except ValueError as e:
            logger.exception(f"Value error in generated code: {e}")
            return AgentResponse(
                data={
                    "code": code,
                    "error": str(e),
                    "error_type": "ValueError",
                    "execution_success": False,
                },
                message=f"Value error: {str(e)}",
                status=AgentStatus.ERROR,
            )

        except Exception as e:
            logger.exception(f"Error executing Timeline code: {e}")
            return AgentResponse(
                data={
                    "code": code,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "execution_success": False,
                },
                message=f"Error executing code: {str(e)}",
                status=AgentStatus.ERROR,
            )

    def _execute_with_retry(
        self,
        code: str,
        exec_globals: dict,
        exec_locals: dict,
        max_retries: int = 3,
    ) -> str:
        import time

        for attempt in range(max_retries):
            try:
                exec(code, exec_globals, exec_locals)
                stream_url = exec_locals.get("stream_url")

                if stream_url:
                    logger.info(f"Code execution successful on attempt {attempt + 1}")
                    return stream_url

                raise ValueError("No stream_url produced")

            except Exception as e:
                error_str = str(e).lower()

                if any(
                    keyword in error_str
                    for keyword in [
                        "audio chunks failed",
                        "transcoding",
                        "runtime error",
                    ]
                ):
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2
                        logger.warning(
                            "Audio transcoding error on attempt "
                            f"{attempt + 1}/{max_retries}: {e}"
                        )
                        logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue

                    logger.error(
                        "Audio transcoding failed after retries, trying "
                        f"video-only fallback: {e}"
                    )
                    try:
                        video_only_code = self._generate_video_only_fallback(code)
                        exec(video_only_code, exec_globals, exec_locals)
                        fallback_url = exec_locals.get("stream_url")
                        if fallback_url:
                            logger.info("Video-only fallback successful")
                            return fallback_url
                    except Exception as fallback_error:
                        logger.error(
                            "Video-only fallback also failed: "
                            f"{fallback_error}"
                        )

                    raise Exception(
                        "Audio transcoding failed after retries and video-only "
                        "fallback also failed. This typically indicates a "
                        "corrupted or unsupported audio track in the source "
                        "media. Suggested fixes: 1) Re-upload the asset without "
                        "an audio track (silent), 2) Upload a re-muxed version "
                        "with a valid audio codec, or 3) Regenerate code for a "
                        "purely visual edit and provide a separate AudioAsset "
                        f"later. Original error: {e}"
                    )

                logger.error(
                    f"Code execution failed with non-transcoding error: {e}"
                )
                raise e

        raise Exception("Unexpected error in retry logic")

    def _generate_video_only_fallback(self, original_code: str) -> str:
        import re
        
        pattern = r"VideoAsset\(([^)]*)\)"

        def add_volume_zero(match):
            params = match.group(1)
            if "volume=" not in params:
                if params.strip():
                    return f"VideoAsset({params}, volume=0)"
                else:
                    return "VideoAsset(volume=0)"
            return match.group(0)

        modified_code = re.sub(pattern, add_volume_zero, original_code)
        logger.info("Generated video-only fallback code.")
        return modified_code
