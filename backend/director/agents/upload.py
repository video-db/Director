import logging

import yt_dlp

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import (
    Session,
    MsgStatus,
    VideoContent,
    TextContent,
    VideoData,
    VideosUpdateEvent,
)
from director.tools.videodb_tool import VideoDBTool

logger = logging.getLogger(__name__)

UPLOAD_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "source": {
            "type": "string",
            "description": "URL or local path to upload the content",
        },
        "source_type": {
            "type": "string",
            "description": "Type of given source.",
            "enum": ["url", "local_file"],
        },
        "name": {
            "type": "string",
            "description": "Name of the content to upload, optional parameter",
        },
        "media_type": {
            "type": "string",
            "enum": ["video", "audio", "image"],
            "description": "Type of media to upload, default is video",
        },
        "collection_id": {
            "type": "string",
            "description": "Collection ID to upload the content",
        },
    },
    "required": ["source", "media_type", "collection_id"],
}


class UploadAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "upload"
        self.description = (
            "This agent uploads the media content to VideoDB. "
            "This agent takes a source which can be a URL or local path of the media content. "
            "The media content can be a video, audio, or image file. "
            "Youtube playlist and links are also supported. "
        )
        self.parameters = UPLOAD_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def _upload(
        self,
        source: str,
        source_type: str,
        media_type: str,
        name: str = None,
    ):
        """Upload the media with the given URL."""
        try:
            if media_type == "video":
                content = VideoContent(
                    agent_name=self.agent_name, status=MsgStatus.progress
                )
            else:
                content = TextContent(
                    agent_name=self.agent_name, status=MsgStatus.progress
                )
            self.output_message.content.append(content)
            content.status_message = f"Uploading {media_type}..."
            self.output_message.push_update()

            upload_data = self.videodb_tool.upload(
                source, source_type, media_type, name=name
            )

            content.status_message = f"{upload_data['name']} uploaded successfully"
            if media_type == "video":
                content.video = VideoData(**upload_data)
                # emit event to update the videos list
                self.session.emit_event(
                    VideosUpdateEvent(collection_id=upload_data.get("collection_id"))
                )
            else:
                content.text = (
                    f"\n ID: {upload_data['id']}, Title: {upload_data['name']}"
                )
            content.status = MsgStatus.success
            self.output_message.publish()
            return AgentResponse(
                status=AgentStatus.SUCCESS,
                message="Upload successful",
                data=upload_data,
            )

        except Exception as e:
            logger.exception(f"error in {self.agent_name} agent: {e}")
            content.status = MsgStatus.error
            content.status_message = f"Error in uploading {media_type}"
            self.output_message.publish()
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))

    def _get_yt_playlist_videos(self, playlist_url: str):
        """Get the list of videos from a youtube playlist."""
        try:
            # Create the downloader object
            with yt_dlp.YoutubeDL({"extract_flat": True, "quiet": True}) as ydl:
                playlist_info = ydl.extract_info(playlist_url, download=False)
            if "entries" in playlist_info:
                video_list = []
                for video in playlist_info["entries"]:
                    video_list.append(
                        {
                            "title": video.get("title", "Unknown Title"),
                            "url": f"https://www.youtube.com/watch?v={video['id']}",
                        }
                    )
                return video_list
        except Exception as e:
            logger.exception(f"Error in getting playlist info: {e}")
            return None

    def _upload_yt_playlist(self, playlist_info: dict, media_type):
        """Upload the videos in a youtube playlist."""
        for media in playlist_info:
            try:
                self.output_message.actions.append(
                    f"Uploading video: {media['title']} as {media_type}"
                )
                self._upload(media["url"], "url", media_type)
            except Exception as e:
                self.output_message.actions.append(
                    f"Upload failed for {media['title']}"
                )
                logger.exception(f"Error in uploading {media['title']}: {e}")
        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message=f"All the videos in the playlist uploaded successfully as {media_type}",
        )

    def run(
        self,
        collection_id: str,
        source: str,
        source_type: str,
        media_type="video",
        name: str = None,
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Upload the media with the given source.

        :param collection_id: str - collection_id in which the upload is required.
        :param source: str - The URL or local path of the media to upload.
        :param source_type: str - The type indicating the source of the media.
        :param media_type: str, optional - The type of media to upload, defaults to "video".
        :param name: str, optional - Name required for uploaded file.
        :return: AgentResponse - The response containing information about the upload operation.
        """

        self.videodb_tool = VideoDBTool(collection_id=collection_id)

        if source_type == "local_file":
            return self._upload(source, source_type, media_type, name)
        elif source_type == "url":
            playlist_info = self._get_yt_playlist_videos(source)
            if playlist_info:
                self.output_message.actions.append("YouTube Playlist detected")
                self.output_message.push_update()
                return self._upload_yt_playlist(playlist_info, media_type)
            return self._upload(source, source_type, media_type, name)
        else:
            error_message = f"Invalid source type {source_type}"
            logger.error(error_message)
            return AgentResponse(
                status=AgentStatus.ERROR, message=error_message, data={}
            )
