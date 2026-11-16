import ast
import builtins
import enum
import inspect
import logging
import re
import types
from functools import lru_cache

from director.agents.base import AgentResponse, AgentStatus

logger = logging.getLogger(__name__)

ALLOWED_IMPORT_ROOT = "videodb"

# Everything else (open, eval, exec, getattr, ...) is unavailable to generated code.
SAFE_BUILTIN_NAMES = (
    "abs", "all", "any", "bool", "dict", "enumerate", "float", "int",
    "isinstance", "len", "list", "max", "min", "print", "range", "round",
    "set", "sorted", "str", "sum", "tuple", "zip",
    "Exception", "KeyError", "IndexError", "TypeError", "ValueError",
)  # fmt: skip

# list, dict, str and enum attributes that Timeline code commonly uses.
COMMON_ATTRIBUTES = {
    "append", "extend", "items", "keys", "values", "get", "join", "lower",
    "upper", "strip", "split", "replace", "value",
}  # fmt: skip


class UnsafeCodeError(ValueError):
    """Generated code uses something outside the Timeline subset."""


def _is_allowed_module(name: str) -> bool:
    return name == ALLOWED_IMPORT_ROOT or name.startswith(ALLOWED_IMPORT_ROOT + ".")


@lru_cache(maxsize=1)
def _allowed_attributes() -> frozenset:
    """Public members, enum values and instance attributes of the videodb.editor classes."""
    from videodb import editor

    names = set(COMMON_ATTRIBUTES)
    for cls in vars(editor).values():
        if not inspect.isclass(cls) or cls.__module__ != editor.__name__:
            continue
        names.update(vars(cls))
        if issubclass(cls, enum.Enum):
            names.update(cls.__members__)
        else:
            names.update(re.findall(r"self\.(\w+)", inspect.getsource(cls)))
    # Timeline keeps the connection it was given; generated code never needs it back.
    names.discard("connection")
    return frozenset(name for name in names if not name.startswith("_"))


class TimelineConnection:
    """The only part of the VideoDB connection that generated code can reach.

    Timeline needs `post` on two fixed paths. The real connection, its HTTP
    session and the API key stay in the closure.
    """

    __slots__ = ("post",)

    def __init__(self, conn):
        from videodb._constants import ApiPath

        allowed_paths = {ApiPath.editor, f"{ApiPath.editor}/{ApiPath.download}"}

        def post(path, data=None):
            if path not in allowed_paths:
                raise PermissionError(f"API path '{path}' is not allowed")
            return conn.post(path=path, data=data)

        self.post = post


def validate_code(code: str) -> None:
    """Reject code that does more than build a Timeline with the videodb SDK."""
    for node in ast.walk(ast.parse(code)):
        if isinstance(node, ast.Import):
            raise UnsafeCodeError("use 'from videodb... import ...' for imports")
        if isinstance(node, ast.ImportFrom):
            if node.level or not _is_allowed_module(node.module or ""):
                raise UnsafeCodeError(f"import from '{node.module}' is not allowed")
            if any(alias.name == "*" for alias in node.names):
                raise UnsafeCodeError("wildcard imports are not allowed")
        elif isinstance(node, ast.Name) and node.id.startswith("_"):
            raise UnsafeCodeError(f"name '{node.id}' is not allowed")
        elif (
            isinstance(node, ast.Attribute) and node.attr not in _allowed_attributes()
        ):
            raise UnsafeCodeError(f"attribute '{node.attr}' is not allowed")


def _import_videodb_only(name, globals=None, locals=None, fromlist=(), level=0):
    if level or not _is_allowed_module(name):
        raise ImportError(f"import of '{name}' is not allowed")
    module = builtins.__import__(name, globals, locals, fromlist, level)
    for item in fromlist or ():
        value = getattr(module, item, None)
        # Submodules of videodb re-export os, requests and friends.
        if isinstance(value, types.ModuleType) and not _is_allowed_module(
            value.__name__
        ):
            raise ImportError(f"import of '{item}' from '{name}' is not allowed")
    return module


def _safe_builtins() -> dict:
    safe = {name: getattr(builtins, name) for name in SAFE_BUILTIN_NAMES}
    safe["__import__"] = _import_videodb_only
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
