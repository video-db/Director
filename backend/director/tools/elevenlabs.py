import time
from typing import Optional

from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings, Voice, play

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
            "description": "The ID of the voice to use for text-to-speech",
            "default": "pNInz6obpgDQGcFmaJgB"
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
                "mp3_44100_192"
            ],
            "default": "mp3_44100_128"
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
            "default": 0.0
        },
        "similarity_boost": {
            "type": "number", 
            "description": "Similarity boost value between 0 and 1 for voice settings",
            "minimum": 0,
            "maximum": 1,
            "default": 1.0
        },
        "style": {
            "type": "number",
            "description": "Style value between 0 and 1 for voice settings",
            "minimum": 0,
            "maximum": 1,
            "default": 0.0
        },
        "use_speaker_boost": {
            "type": "boolean",
            "description": "Whether to use speaker boost in voice settings",
            "default": True
        }
    },
}


class ElevenLabsTool:
    def __init__(self, api_key: str):
        if api_key:
            self.client = ElevenLabs(api_key=api_key)
        else:
            raise Exception("ElevenLabs API key not found")
        self.voice_settings = VoiceSettings(
            stability=0.0,
            similarity_boost=1.0,
            style=0.0,
            use_speaker_boost=True
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
                metadata = self.client.dubbing.get_dubbing_project_metadata(
                    dubbing_id
                )
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
        
    def clone_audio(self, audio_url, name_of_voice, description):
        voice = self.client.clone(
            name=name_of_voice,
            files=[audio_url],
            description=description
        )
        
        return voice
    
    def synthesis_text(self, voice:Voice, text_to_synthesis:str):
        audio = self.client.generate(text=text_to_synthesis, voice=voice, model="elevenlabs-multilingual-v2")
        return audio
