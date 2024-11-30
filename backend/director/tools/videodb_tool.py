import os
import requests
import videodb

from videodb import SearchType, SubtitleStyle, IndexType, SceneExtractionType
from videodb.timeline import Timeline
from videodb.asset import VideoAsset, ImageAsset


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
        }

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

    def generate_thumbnail(self, video_id: str, timestamp: int = 5):
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
            if index_type == IndexType.scene:
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
    

