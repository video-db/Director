from enum import Enum


class RoleTypes(str, Enum):
    system = "system"
    user = "user"
    assistant = "assistant"


class DBType(str, Enum):
    SQLITE = "sqlite"
    TURSO = "turso"
    SQL = "sql"
    POSTGRES = "postgres"


class LLMType(str, Enum):
    """Enum for LLM types"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLEAI = "googleai"
    VIDEODB_PROXY = "videodb_proxy"


class EnvPrefix(str, Enum):
    """Enum for environment prefixes"""

    OPENAI_ = "OPENAI_"
    ANTHROPIC_ = "ANTHROPIC_"
    GOOGLEAI_ = "GOOGLEAI_"

DOWNLOADS_PATH = "director/downloads"

# VideoDB public demo assets used as brandkit defaults when the user has none.
# These IDs are hosted in VideoDB's public collection and are accessible via any API key.
# TODO: Replace with canonical asset IDs from the VideoDB team.
BRANDKIT_DEMO_INTRO_VIDEO_ID = None
BRANDKIT_DEMO_OUTRO_VIDEO_ID = None
BRANDKIT_DEMO_BRAND_IMAGE_ID = None
