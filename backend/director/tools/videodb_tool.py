import os
import requests
import videodb
import logging

from videodb import SearchType, SubtitleStyle, IndexType, SceneExtractionType
from videodb.timeline import Timeline
from videodb.asset import VideoAsset, ImageAsset
from director.tools.elevenlabs import VOICE_ID_MAP
from director.constants import DOWNLOADS_PATH


class VideoDBTool:
    def __init__(self, collection_id="default"):
        self.conn = videodb.connect(
            base_url=os.getenv("VIDEO_DB_BASE_URL", "https://api.videodb.io")
        )
        self.collection = None
        if collection_id:
            self.collection = self.conn.get_collection(collection_id)
        self.timeline = None

    def get_collection(self):
        return {
            "id": self.collection.id,
            "name": self.collection.name,
            "description": self.collection.description,
        }

    def get_collections(self):
        """Get all collections."""
        collections = self.conn.get_collections()
        return [
            {
                "id": collection.id,
                "name": collection.name,
                "description": collection.description,
            }
            for collection in collections
        ]

    def get_image(self, image_id: str = None):
        """
        Fetch image details by ID or validate an image URL.
        """
        try:
            image = self.collection.get_image(image_id)
            return {
                "id": image.id,
                "url": image.url,
                "name": image.name,
                "description": getattr(image, "description", None),
                "collection_id": image.collection_id,
            }
        except Exception as e:
            raise Exception(f"Failed to fetch image with ID {image_id}: {e}")

    def get_images(self):
        """Get all images in a collection."""
        images = self.collection.get_images()
        return [
            {
                "id": image.id,
                "collection_id": image.collection_id,
                "name": image.name,
                "url": image.url,
                "type": "image",
            }
            for image in images
        ]

    def create_collection(self, name, description=""):
        """Create a new collection with the given name and description."""
        if not name:
            raise ValueError("Collection name is required to create a collection.")

        try:
            new_collection = self.conn.create_collection(name, description)
            return {
                "success": True,
                "message": f"Collection '{new_collection.id}' created successfully",
                "collection": {
                    "id": new_collection.id,
                    "name": new_collection.name,
                    "description": new_collection.description,
                },
            }
        except Exception as e:
            logging.error(f"Failed to create collection '{name}': {e}")
            raise Exception(f"Failed to create collection '{name}': {str(e)}") from e

    def delete_collection(self):
        """Delete the current collection."""
        if not self.collection:
            raise ValueError("Collection ID is required to delete a collection.")
        try:
            self.collection.delete()
            return {
                "success": True,
                "message": f"Collection {self.collection.id} deleted successfully",
            }
        except Exception as e:
            raise Exception(
                f"Failed to delete collection {self.collection.id}: {str(e)}"
            )

    def get_video(self, video_id):
        """Get a video by ID."""
        video = self.collection.get_video(video_id)
        return {
            "id": video.id,
            "name": video.name,
            "description": video.description,
            "collection_id": video.collection_id,
            "stream_url": video.stream_url,
            "length": video.length,
            "thumbnail_url": video.thumbnail_url,
        }

    def delete_video(self, video_id):
        """Delete a specific video by its ID."""
        if not video_id:
            raise ValueError("Video ID is required to delete a video.")
        try:
            video = self.collection.get_video(video_id)
            if not video:
                raise ValueError(
                    f"Video with ID {video_id} not found in collection {self.collection.id}."
                )

            video.delete()
            return {
                "success": True,
                "message": f"Video {video.id} deleted successfully",
            }
        except ValueError as ve:
            logging.error(f"ValueError while deleting video: {ve}")
            raise ve
        except Exception as e:
            logging.exception(
                f"Unexpected error occurred while deleting video {video_id}"
            )
            raise Exception(
                "An unexpected error occurred while deleting the video. Please try again later."
            )

    def get_videos(self):
        """Get all videos in a collection."""
        videos = self.collection.get_videos()
        return [
            {
                "id": video.id,
                "name": video.name,
                "description": video.description,
                "collection_id": video.collection_id,
                "stream_url": video.stream_url,
                "length": video.length,
                "thumbnail_url": video.thumbnail_url,
                "type": "video",
            }
            for video in videos
        ]

    def get_audio(self, audio_id):
        """Get an audio by ID."""
        audio = self.collection.get_audio(audio_id)
        return {
            "id": audio.id,
            "name": audio.name,
            "collection_id": audio.collection_id,
            "length": audio.length,
            "url": audio.generate_url(),
        }

    def get_audios(self):
        """Get all audios in a collection."""
        audios = self.collection.get_audios()
        return [
            {
                "id": audio.id,
                "collection_id": audio.collection_id,
                "name": audio.name,
                "length": audio.length,
                "type": "audio",
            }
            for audio in audios
        ]

    def generate_audio_url(self, audio_id):
        audio = self.collection.get_audio(audio_id)
        return audio.generate_url()

    def generate_image_url(self, image_id):
        image = self.collection.get_image(image_id)
        return image.generate_url()

    def upload(self, source, source_type="url", media_type="video", name=None):
        upload_args = {"media_type": media_type}
        if name:
            upload_args["name"] = name
        if source_type == "url":
            upload_args["url"] = source
        elif source_type == "file":
            upload_url_data = self.conn.get(
                path=f"/collection/{self.collection.id}/upload_url",
                params={"name": name},
            )
            upload_url = upload_url_data.get("upload_url")
            files = {"file": (name, source)}
            response = requests.post(upload_url, files=files)
            response.raise_for_status()
            upload_args["url"] = upload_url
        else:
            upload_args["file_path"] = source
        media = self.conn.upload(**upload_args)
        name = media.name
        if media_type == "video":
            return {
                "id": media.id,
                "collection_id": media.collection_id,
                "stream_url": media.stream_url,
                "player_url": media.player_url,
                "name": name,
                "description": media.description,
                "thumbnail_url": media.thumbnail_url,
                "length": media.length,
            }
        elif media_type == "audio":
            return {
                "id": media.id,
                "collection_id": media.collection_id,
                "name": media.name,
                "length": media.length,
            }
        elif media_type == "image":
            return {
                "id": media.id,
                "collection_id": media.collection_id,
                "name": media.name,
                "url": media.url,
            }

    def extract_frame(self, video_id: str, timestamp: int = 5):
        video = self.collection.get_video(video_id)
        image = video.generate_thumbnail(time=float(timestamp))
        return {
            "id": image.id,
            "collection_id": image.collection_id,
            "name": image.name,
            "url": image.url,
        }

    def get_transcript(self, video_id: str, text=True):
        video = self.collection.get_video(video_id)
        if text:
            transcript = video.get_transcript_text()
        else:
            transcript = video.get_transcript()
        return transcript

    def index_spoken_words(self, video_id: str):
        # TODO: Language support
        video = self.collection.get_video(video_id)
        index = video.index_spoken_words()
        return index

    def index_scene(
        self,
        video_id: str,
        extraction_type=SceneExtractionType.shot_based,
        extraction_config={},
        prompt=None,
    ):
        video = self.collection.get_video(video_id)
        return video.index_scenes(
            extraction_type=extraction_type,
            extraction_config=extraction_config,
            prompt=prompt,
        )

    def list_scene_index(self, video_id: str):
        video = self.collection.get_video(video_id)
        return video.list_scene_index()

    def get_scene_index(self, video_id: str, scene_id: str):
        video = self.collection.get_video(video_id)
        return video.get_scene_index(scene_id)

    def download(self, stream_link: str, name: str = None):
        download_response = self.conn.download(stream_link, name)
        return download_response

    def semantic_search(
        self, query, index_type=IndexType.spoken_word, video_id=None, **kwargs
    ):
        if video_id:
            video = self.collection.get_video(video_id)
            search_resuls = video.search(query=query, index_type=index_type, **kwargs)
        else:
            kwargs.pop("scene_index_id", None)
            search_resuls = self.collection.search(
                query=query, index_type=index_type, **kwargs
            )
        return search_resuls

    def keyword_search(
        self, query, index_type=IndexType.spoken_word, video_id=None, **kwargs
    ):
        """Search for a keyword in a video."""
        video = self.collection.get_video(video_id)
        return video.search(
            query=query, search_type=SearchType.keyword, index_type=index_type, **kwargs
        )

    def generate_video_stream(self, video_id: str, timeline):
        """Generate a video stream from a timeline. timeline is a list of tuples. ex [(0, 10), (20, 30)]"""
        video = self.collection.get_video(video_id)
        return video.generate_stream(timeline)

    def add_brandkit(self, video_id, intro_video_id, outro_video_id, brand_image_id):
        timeline = Timeline(self.conn)
        if intro_video_id:
            intro_video = VideoAsset(asset_id=intro_video_id)
            timeline.add_inline(intro_video)
        video = VideoAsset(asset_id=video_id)
        timeline.add_inline(video)
        if outro_video_id:
            outro_video = VideoAsset(asset_id=outro_video_id)
            timeline.add_inline(outro_video)
        if brand_image_id:
            brand_image = ImageAsset(asset_id=brand_image_id)
            timeline.add_overlay(0, brand_image)
        stream_url = timeline.generate_stream()
        return stream_url

    def get_and_set_timeline(self):
        self.timeline = Timeline(self.conn)
        return self.timeline

    def add_subtitle(self, video_id, style: SubtitleStyle = SubtitleStyle()):
        video = self.collection.get_video(video_id)
        stream_url = video.add_subtitle(style)
        return stream_url

    def translate_transcript(self, video_id, language, additional_notes=None):
        video = self.collection.get_video(video_id)
        return video.translate_transcript(
            language=language,
            additional_notes=additional_notes,
        )

    def youtube_search(self, query, count=5, duration=None):
        return self.conn.youtube_search(
            query=query,
            result_threshold=count,
            duration=duration,
        )

    def dub_video(self, video_id, language_code):
        dubed_video = self.collection.dub_video(
            video_id=video_id, language_code=language_code
        )
        return {
            "id": dubed_video.id,
            "name": dubed_video.name,
            "description": dubed_video.description,
            "collection_id": dubed_video.collection_id,
            "stream_url": dubed_video.stream_url,
            "length": dubed_video.length,
            "thumbnail_url": dubed_video.thumbnail_url,
        }

    def generate_image(self, prompt, aspect_ratio="16:9"):
        image = self.collection.generate_image(prompt=prompt, aspect_ratio=aspect_ratio)
        return {
            "id": image.id,
            "name": image.name,
            "collection_id": image.collection_id,
            "url": image.generate_url(),
        }

    def generate_music(self, prompt, duration):
        music = self.collection.generate_music(prompt=prompt, duration=duration)
        return {
            "id": music.id,
            "name": music.name,
            "collection_id": music.collection_id,
            "url": music.generate_url(),
        }

    def generate_sound_effect(self, prompt, duration, config):
        sound_effect = self.collection.generate_sound_effect(
            prompt=prompt,
            duration=duration,
            config=config,
        )
        return {
            "id": sound_effect.id,
            "name": sound_effect.name,
            "collection_id": sound_effect.collection_id,
            "url": sound_effect.generate_url(),
        }

    def generate_voice(self, text, voice_name, config):
        voice = self.collection.generate_voice(
            text=text,
            voice_name=voice_name,
            config=config,
        )
        return {
            "id": voice.id,
            "name": voice.name,
            "collection_id": voice.collection_id,
            "url": voice.generate_url(),
        }

    def generate_video(self, prompt, duration):
        video = self.collection.generate_video(prompt=prompt, duration=duration)
        return {
            "id": video.id,
            "name": video.name,
            "collection_id": video.collection_id,
            "stream_url": video.generate_stream(),
            "length": video.length,
        }

    def delete_audio(self, audio_id):
        """Delete a specific audio by its ID."""
        if not audio_id:
            raise ValueError("Audio ID is required to delete a audio.")
        try:
            audio = self.collection.get_audio(audio_id)
            if not audio:
                raise ValueError(
                    f"Audio with ID {audio_id} not found in collection {self.collection.id}."
                )

            audio.delete()
            return {
                "success": True,
                "message": f"Video {audio.id} deleted successfully",
            }
        except ValueError as ve:
            logging.error(f"ValueError while deleting video: {ve}")
            raise ve
        except Exception as e:
            logging.exception(
                f"Unexpected error occurred while deleting video {audio_id}"
            )
            raise Exception(
                "An unexpected error occurred while deleting the video. Please try again later."
            )

    def delete_image(self, image_id):
        """Delete a specific image by its ID."""
        if not image_id:
            raise ValueError("Image ID is required to delete a image.")
        try:
            image = self.collection.get_image(image_id)
            if not image:
                raise ValueError(
                    f"Image with ID {image_id} not found in collection {self.collection.id}."
                )

            image.delete()
            return {
                "success": True,
                "message": f"Image {image_id} deleted successfully",
            }
        except ValueError as ve:
            logging.error(f"ValueError while deleting video: {ve}")
            raise ve
        except Exception as e:
            logging.exception(
                f"Unexpected error occurred while deleting video {image_id}"
            )
            raise Exception(
                "An unexpected error occurred while deleting the video. Please try again later."
            )


class VDBVideoGenerationTool:
    def __init__(self, collection_id="default"):
        self.videodb_tool = VideoDBTool(collection_id=collection_id)
        self.collection = self.videodb_tool.conn.get_collection(collection_id)

    def _download_video_file(self, video_url: str, save_at: str) -> bool:
        os.makedirs(DOWNLOADS_PATH, exist_ok=True)

        response = requests.get(video_url, stream=True)
        response.raise_for_status()

        if not response.headers.get("Content-Type", "").startswith("video"):
            raise ValueError(f"The URL does not point to a video file: {video_url}")

        with open(save_at, "wb") as file:
            file.write(response.content)

    def text_to_video(
        self, prompt: str, save_at: str, duration: float, config: dict = {}
    ):
        media = self.collection.generate_video(prompt=prompt, duration=duration)

        download_response = self.videodb_tool.download(media.stream_url)
        download_url = download_response.get("download_url")

        self._download_video_file(download_url, save_at)
        if not os.path.exists(save_at):
            raise Exception(f"Failed to save video at {save_at}")

        video_dict = {
            "id": media.id,
            "collection_id": media.collection_id,
            "stream_url": media.stream_url,
            "player_url": media.player_url,
            "name": media.name,
            "description": media.description,
            "thumbnail_url": media.thumbnail_url,
            "length": media.length,
        }
        return video_dict


class VDBAudioGenerationTool:
    def __init__(self, collection_id="default"):
        self.videodb_tool = VideoDBTool(collection_id=collection_id)
        self.collection = self.videodb_tool.conn.get_collection(collection_id)

    def _download_audio_file(self, audio_url: str, save_at: str) -> bool:
        os.makedirs(DOWNLOADS_PATH, exist_ok=True)
        response = requests.get(audio_url, stream=True)
        response.raise_for_status()

        with open(save_at, "wb") as file:
            file.write(response.content)

    def generate_sound_effect(
        self, prompt: str, save_at: str, duration: float, config: dict
    ):
        audio = self.collection.generate_sound_effect(
            prompt=prompt, duration=duration, config=config
        )

        download_url = audio.generate_url()
        self._download_audio_file(download_url, save_at)

        return {
            "id": audio.id,
            "collection_id": audio.collection_id,
            "name": audio.name,
            "length": audio.length,
            "url": audio.generate_url(),
        }

    def text_to_speech(self, text: str, save_at: str, config: dict):
        audio = self.collection.generate_voice(
            text=text,
            voice_name=VOICE_ID_MAP.get(config.get("voice_id")),
            config=config,
        )

        download_url = audio.generate_url()
        self._download_audio_file(download_url, save_at)

        return {
            "id": audio.id,
            "collection_id": audio.collection_id,
            "name": audio.name,
            "length": audio.length,
            "url": audio.generate_url(),
        }

    def generate_music(self, prompt: str, save_at: str, duration: float):
        audio = self.collection.generate_music(prompt=prompt, duration=duration)

        download_url = audio.generate_url()
        self._download_audio_file(download_url, save_at)

        return {
            "id": audio.id,
            "collection_id": audio.collection_id,
            "name": audio.name,
            "length": audio.length,
            "url": audio.generate_url(),
        }
