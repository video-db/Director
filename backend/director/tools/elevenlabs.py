import time
from typing import Optional

from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from elevenlabs.core import RequestOptions

DEFAULT_VOICES = """
1. 9BWtsMINqrJLrRacOk9x - Aria: Expressive, American, female.
2. CwhRBWXzGAHq8TQ4Fs17 - Roger: Confident, American, male.
3. EXAVITQu4vr4xnSDxMaL - Sarah: Soft, American, young female.
4. FGY2WhTYpPnrIDTdsKH5 - Laura: Upbeat, American, young female.
5. IKne3meq5aSn9XLyUdCD - Charlie: Natural, Australian, male.
6. JBFqnCBsd6RMkjVDRZzb - George: Warm, British, middle-aged male.
7. N2lVS1w4EtoT3dr4eOWO - Callum: Intense, Transatlantic, male.
8. SAz9YHcvj6GT2YYXdXww - River: Confident, American, non-binary.
9. TX3LPaxmHKxFdv7VOQHJ - Liam: Articulate, American, young male.
10. XB0fDUnXU5powFXDhCwa - Charlotte: Seductive, Swedish, young female.
11. Xb7hH8MSUJpSbSDYk0k2 - Alice: Confident, British, middle-aged female.
12. XrExE9yKIg1WjnnlVkGX - Matilda: Friendly, American, middle-aged female.
13. bIHbv24MWmeRgasZH58o - Will: Friendly, American, young male.
14. cgSgspJ2msm6clMCkdW9 - Jessica: Expressive, American, young female.
15. cjVigY5qzO86Huf0OWal - Eric: Friendly, American, middle-aged male.
16. iP95p4xoKVk53GoZ742B - Chris: Casual, American, middle-aged male.
17. nPczCjzI2devNBz1zQrb - Brian: Deep, American, middle-aged male.
18. onwK4e9ZLuTAKqWW03F9 - Daniel: Authoritative, British, middle-aged male.
19. pFZP5JQG7iQjIQuC4Bku - Lily: Warm, British, middle-aged female.
20. pqHfZKP75CvOlQylNhV4 - Bill: Trustworthy, American, old male.
"""

VOICE_ID_MAP = {
    "9BWtsMINqrJLrRacOk9x": "Aria",
    "CwhRBWXzGAHq8TQ4Fs17": "Roger",
    "EXAVITQu4vr4xnSDxMaL": "Sarah",
    "FGY2WhTYpPnrIDTdsKH5": "Laura",
    "IKne3meq5aSn9XLyUdCD": "Charlie",
    "JBFqnCBsd6RMkjVDRZzb": "George",
    "N2lVS1w4EtoT3dr4eOWO": "Callum",
    "SAz9YHcvj6GT2YYXdXww": "River",
    "TX3LPaxmHKxFdv7VOQHJ": "Liam",
    "XB0fDUnXU5powFXDhCwa": "Charlotte",
    "Xb7hH8MSUJpSbSDYk0k2": "Alice",
    "XrExE9yKIg1WjnnlVkGX": "Matilda",
    "bIHbv24MWmeRgasZH58o": "Will",
    "cgSgspJ2msm6clMCkdW9": "Jessica",
    "cjVigY5qzO86Huf0OWal": "Eric",
    "iP95p4xoKVk53GoZ742B": "Chris",
    "nPczCjzI2devNBz1zQrb": "Brian",
    "onwK4e9ZLuTAKqWW03F9": "Daniel",
    "pFZP5JQG7iQjIQuC4Bku": "Lily",
    "pqHfZKP75CvOlQylNhV4": "Bill",
}

PARAMS_CONFIG = {
    "sound_effect": {
        "prompt_influence": {
            "type": "number",
            "description": (
                "A value between 0 and 1 that determines how closely the generation "
                "follows the prompt. Higher values make generations follow the prompt "
                "more closely while also making them less variable. Defaults to 0.3"
            ),
            "minimum": 0,
            "maximum": 1,
            "default": 0.3,
        }
    },
    "text_to_speech": {
        "model_id": {
            "type": "string",
            "description": ("Identifier of the model that will be used"),
            "default": "eleven_multilingual_v2",
        },
        "voice_id": {
            "type": "string",
            "description": f"The ID of the voice to use for text-to-speech, Some available voice ids are {DEFAULT_VOICES}",
            "default": "pNInz6obpgDQGcFmaJg",
        },
        "output_format": {
            "type": "string",
            "description": (
                "Output format of the generated audio. Format options:\n"
                "mp3_22050_32 - MP3 at 22.05kHz sample rate, 32kbps\n"
                "mp3_44100_32 - MP3 at 44.1kHz sample rate, 32kbps\n"
                "mp3_44100_64 - MP3 at 44.1kHz sample rate, 64kbps\n"
                "mp3_44100_96 - MP3 at 44.1kHz sample rate, 96kbps\n"
                "mp3_44100_128 - MP3 at 44.1kHz sample rate, 128kbps\n"
                "mp3_44100_192 - MP3 at 44.1kHz sample rate, 192kbps"
            ),
            "enum": [
                "mp3_22050_32",
                "mp3_44100_32",
                "mp3_44100_64",
                "mp3_44100_96",
                "mp3_44100_128",
                "mp3_44100_192",
            ],
            "default": "mp3_44100_128",
        },
        "language_code": {
            "type": "string",
            "description": (
                "Language code (ISO 639-1) used to enforce a language for the "
                "model. Currently only Turbo v2.5 supports language enforcement. "
                "For other models, an error will be returned if language code is "
                "provided."
            ),
        },
        "stability": {
            "type": "number",
            "description": "Stability value between 0 and 1 for voice settings",
            "minimum": 0,
            "maximum": 1,
            "default": 0.0,
        },
        "similarity_boost": {
            "type": "number",
            "description": "Similarity boost value between 0 and 1 for voice settings",
            "minimum": 0,
            "maximum": 1,
            "default": 1.0,
        },
        "style": {
            "type": "number",
            "description": "Style value between 0 and 1 for voice settings",
            "minimum": 0,
            "maximum": 1,
            "default": 0.0,
        },
        "use_speaker_boost": {
            "type": "boolean",
            "description": "Whether to use speaker boost in voice settings",
            "default": True,
        },
    },
}


class ElevenLabsTool:
    def __init__(self, api_key: str):
        if api_key:
            self.client = ElevenLabs(api_key=api_key)
        else:
            raise Exception("ElevenLabs API key not found")
        self.voice_settings = VoiceSettings(
            stability=0.0, similarity_boost=1.0, style=0.0, use_speaker_boost=True
        )
        self.constrains = {
            "sound_effect": {"max_duration": 20},
        }

    def generate_sound_effect(
        self, prompt: str, save_at: str, duration: float, config: dict
    ):
        try:
            result = self.client.text_to_sound_effects.convert(
                text=prompt,
                duration_seconds=min(
                    duration, self.constrains["sound_effect"]["max_duration"]
                ),
                prompt_influence=config.get("prompt_influence", 0.3),
            )
            with open(save_at, "wb") as f:
                for chunk in result:
                    f.write(chunk)
        except Exception as e:
            raise Exception(f"Error generating sound effect: {str(e)}")

    def text_to_speech(self, text: str, save_at: str, config: dict):
        try:
            response = self.client.text_to_speech.convert(
                voice_id=config.get("voice_id", "pNInz6obpgDQGcFmaJgB"),
                output_format=config.get("output_format", "mp3_44100_128"),
                text=text,
                model_id=config.get("model_id", "eleven_multilingual_v2"),
                voice_settings=VoiceSettings(
                    stability=config.get("stability", 0.0),
                    similarity_boost=config.get("similarity_boost", 1.0),
                    style=config.get("style", 0.0),
                    use_speaker_boost=config.get("use_speaker_boost", True),
                ),
            )
            with open(save_at, "wb") as f:
                for chunk in response:
                    if chunk:
                        f.write(chunk)
        except Exception as e:
            raise Exception(f"Error converting text to speech: {str(e)}")

    def create_dub_job(
        self,
        source_url: str,
        target_language: str,
    ) -> Optional[str]:
        """
        Dub an audio or video file from one language to another.

        Args:
            input_file_path: Path to input file
            file_format: Format of input file (e.g. "audio/mpeg")
            source_language: Source language code (e.g. "en")
            target_language: Target language code (e.g. "es")

        Returns:
            Path to dubbed file if successful, None if failed
        """
        try:
            response = self.client.dubbing.dub_a_video_or_an_audio_file(
                source_url=source_url,
                target_lang=target_language,
            )

            dubbing_id = response.dubbing_id
            return dubbing_id

        except Exception as e:
            raise Exception(f"Error creating dub job: {str(e)}")

    def wait_for_dub_job(self, dubbing_id: str) -> bool:
        """Wait for dubbing to complete."""
        MAX_ATTEMPTS = 120
        CHECK_INTERVAL = 30  # In seconds

        for _ in range(MAX_ATTEMPTS):
            try:
                metadata = self.client.dubbing.get_dubbing_project_metadata(dubbing_id)
                print("this is metadata", metadata)
                if metadata.status == "dubbed":
                    return True
                elif metadata.status == "dubbing":
                    time.sleep(CHECK_INTERVAL)
                else:
                    return False
            except Exception as e:
                print(f"Error checking dubbing status: {str(e)}")
                return False
        return False

    def download_dub_file(
        self, dubbing_id: str, language_code: str, output_path: str
    ) -> Optional[str]:
        """Download the dubbed file."""
        try:
            with open(output_path, "wb") as file:
                for chunk in self.client.dubbing.get_dubbed_file(
                    dubbing_id, language_code
                ):
                    file.write(chunk)
            return output_path
        except Exception as e:
            print(f"Error downloading dubbed file: {str(e)}")
            return None

    
    def clone_audio(self, audio_files: list[str], name_of_voice, description):
        voice = self.client.clone(
            name=name_of_voice,
            files=audio_files,
            description=description
        )
        return voice

    def get_voice(self, voice_id):
        voice = self.client.voices.get(voice_id=voice_id)
        return voice

    def synthesis_text(self, voice, text_to_synthesis:str):
        try:
            request_options = RequestOptions(timeout_in_seconds=120)
            audio = self.client.generate(text=text_to_synthesis, voice=voice, model="eleven_multilingual_v2", request_options=request_options)
            return audio
        except Exception as e:
            print(f"Error while text synthesis {e}")
            return None
