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

DOWNLOADS_PATH="director/downloads"

CHAT_NAMING_SYSTEM_PROMPT = """
You are an assistant that generates short, descriptive titles for chat conversations.
The title should summarize the main intent or topic of the user's first message.

Guidelines:

**Output you give should strictly just be the title without any markdown content in plain text**

Keep the title under 6 words.

Use concise, professional phrasing.

Don't include punctuation unless necessary.

Capitalize like a headline (e.g., “Check SQL Query Logic”).

Avoid emojis or filler words.

Example input and outputs:

“Can you give me download links for these videos?” → Generate Video Download Links

“Summarize the lecture video for me” → Lecture Video Summary

“Add a watermark to my demo” → Add Watermark to Video

“Trim the video from 2:10 to 3:45” → Trim Video Segment

“Combine these three clips into one” → Merge Video Clips

“Extract subtitles from this recording” → Extract Video Subtitles

“Translate this video into Spanish” → Translate Video to Spanish

“Generate a short trailer from the full video” → Create Video Trailer

"""