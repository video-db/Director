import os
import base64
import json
import time
from typing import Optional
from elevenlabs.client import ElevenLabs
import traceback
from elevenlabs import VoiceSettings


class ElevenLabsTool:
    def __init__(self, api_key: str):
        # TODO: handler error if api_key is not set
        if api_key:
            self.client = ElevenLabs(api_key=api_key)
        self.voice_settings = VoiceSettings(
            stability=0.0, similarity_boost=1.0, style=0.0, use_speaker_boost=True
        )

    def text_to_speech(
        self, text, voice_id="pNInz6obpgDQGcFmaJgB", model="eleven_turbo_v2_5"
    ):
        """Convert text to speech using ElevenLabs API."""
        try:
            response = self.client.text_to_speech.convert(
                voice_id=voice_id,
                output_format="mp3_22050_32",
                text=text,
                model_id=model,
                voice_settings=self.voice_settings,
            )
            return response
        except Exception as e:
            return {"error": str(e)}

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
            return {"error": str(e)}

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
                print(traceback.format_exc())
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
            print(traceback.format_exc())
            print(f"Error downloading dubbed file: {str(e)}")
            return None
