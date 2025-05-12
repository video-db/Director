import logging

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.llm import get_default_llm
from director.core.session import (
    Session,
    MsgStatus,
    TextContent,
    SearchResultsContent,
    SearchData,
    ShotData,
    VideoContent,
    VideoData,
    ContextMessage,
    RoleTypes,
)
from director.tools.videodb_tool import VideoDBTool
from videodb import InvalidRequestError

logger = logging.getLogger(__name__)

SUPPORTED_INDEX_TYPES = ["spoken_word", "scene"]

SEARCH_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Search query"},
        "search_type": {
            "type": "string",
            "enum": ["semantic", "keyword"],
            "description": "Type of search, default is semantic. semantic: search based on semantic similarity, keyword: search based on keyword only avilable on video not collection",
        },
        "index_type": {
            "type": "string",
            "enum": SUPPORTED_INDEX_TYPES,
            "description": "Type of indexing to perform, spoken_word: based on transcript of the video, scene: based on visual description of the video",
        },
        "result_threshold": {
            "type": "number",
            "description": " Initial filter for top N matching documents (default: 8).",
        },
        "score_threshold": {
            "type": "integer",
            "description": "Absolute threshold filter for relevance scores (default: 0.2).",
        },
        "dynamic_score_percentage": {
            "type": "integer",
            "description": "Adaptive filtering mechanism: Useful when there is a significant gap between top results and tail results after score_threshold filter. Retains top x% of the score range. Calculation: dynamic_threshold = max_score - (range * dynamic_score_percentage) (default: 20 percent)",
        },
        "video_id": {
            "type": "string",
            "description": "The ID of the video to process.",
        },
        "collection_id": {
            "type": "string",
            "description": "The ID of the collection to process.",
        },
    },
    "required": ["query", "search_type", "index_type", "collection_id"],
}


class SearchAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "search"
        self.description = "Agent to search information from VideoDB collections. Mainly used with a collection of videos."
        self.llm = get_default_llm()
        self.parameters = SEARCH_AGENT_PARAMETERS
        super().__init__(session=session, **kwargs)

    def run(
        self,
        query: str,
        search_type: str,
        index_type: str,
        collection_id: str,
        video_id: str = None,
        result_threshold=8,
        score_threshold=0.2,
        dynamic_score_percentage=20,
        *args,
        **kwargs,
    ) -> AgentResponse:
        """
        Retreive data from VideoDB collections and videos.

        :return: The response containing search results, text summary and compilation video.
        :rtype: AgentResponse
        """
        try:
            search_result_content = SearchResultsContent(
                status=MsgStatus.progress,
                status_message="Started getting search results.",
                agent_name=self.agent_name,
            )
            self.output_message.content.append(search_result_content)
            self.output_message.actions.append(
                f"Running {search_type} search on {index_type} index."
            )
            self.output_message.push_update()

            videodb_tool = VideoDBTool(collection_id=collection_id)

            scene_index_id = None

            if index_type not in SUPPORTED_INDEX_TYPES:
                raise ValueError(
                    f"Invalid index type '{index_type}'. Supported types: {', '.join(SUPPORTED_INDEX_TYPES)}."
                )
            
            if video_id:
                if index_type == "scene":
                    scene_index_list = videodb_tool.list_scene_index(video_id)
                    if scene_index_list:
                        scene_index_id = scene_index_list[0].get("scene_index_id")
                    else:
                        self.output_message.actions.append("Scene index not found")
                        self.output_message.push_update()
                        raise ValueError("Scene index not found. Please index scene first.")

                elif index_type == "spoken_word":
                    try:
                        videodb_tool.get_transcript(video_id)
                    except InvalidRequestError as e:
                        logger.error(f"Transcript not found for video {video_id}. {e}")
                        search_result_content.status = MsgStatus.error
                        search_result_content.status_message = (
                            "Spoken words index not found for video."
                        )
                        self.output_message.push_update()
                        raise ValueError(
                            "Transcript not found. Please index spoken word first."
                        )

            if search_type == "semantic":
                search_results = videodb_tool.semantic_search(
                    query,
                    index_type=index_type,
                    video_id=video_id,
                    result_threshold=result_threshold,
                    score_threshold=score_threshold,
                    dynamic_score_percentage=dynamic_score_percentage,
                    scene_index_id=scene_index_id,
                )

            elif search_type == "keyword" and video_id:
                search_results = videodb_tool.keyword_search(
                    query,
                    index_type=index_type,
                    video_id=video_id,
                    result_threshold=result_threshold,
                    scene_index_id=scene_index_id,
                )
            else:
                raise ValueError(f"Invalid search type {search_type}")

            compilation_content = VideoContent(
                status=MsgStatus.progress,
                status_message="Started video compilation.",
                agent_name=self.agent_name,
            )
            self.output_message.content.append(compilation_content)
            search_summary_content = TextContent(
                status=MsgStatus.progress,
                status_message="Started generating summary of search results.",
                agent_name=self.agent_name,
            )
            self.output_message.content.append(search_summary_content)

            shots = search_results.get_shots()
            if not shots:
                search_result_content.status = MsgStatus.error
                search_result_content.status_message = (
                    f"Failed due to no search results found for query {query}"
                )
                compilation_content.status = MsgStatus.error
                compilation_content.status_message = (
                    "Failed to create compilation of search results."
                )
                search_summary_content.status = MsgStatus.error
                search_summary_content.status_message = (
                    "Failed to generate summary of results."
                )
                return AgentResponse(
                    status=AgentStatus.ERROR,
                    message=f"Failed due to no search results found for query {query}",
                    data={
                        "message": f"Failed due to no search results found for query {query}"
                    },
                )

            search_result_videos = {}

            for shot in shots:
                video_id = shot["video_id"]
                if video_id not in search_result_videos:
                    video = videodb_tool.get_video(video_id)
                    search_result_videos[video_id] = {
                        "video_id": video_id,
                        "video_title": shot["video_title"],
                        "stream_url": video.get("stream_url"),
                        "duration": video.get("length"),
                        "shots": [],
                    }

                shot_data = {
                    "search_score": shot["search_score"],
                    "start": shot["start"],
                    "end": shot["end"],
                    "text": shot["text"],
                }
                search_result_videos[video_id]["shots"].append(shot_data)

            search_result_content.search_results = [
                SearchData(
                    video_id=sr["video_id"],
                    video_title=sr["video_title"],
                    stream_url=sr["stream_url"],
                    duration=sr["duration"],
                    shots=[ShotData(**shot) for shot in sr["shots"]],
                )
                for sr in search_result_videos.values()
            ]
            search_result_content.status = MsgStatus.success
            search_result_content.status_message = "Search done."

            self.output_message.actions.append(
                "Generating search result compilation clip.."
            )
            self.output_message.push_update()
            compilation_stream_url = search_results.compile()
            compilation_content.video = VideoData(stream_url=compilation_stream_url)
            compilation_content.status = MsgStatus.success
            compilation_content.status_message = "Compilation done."

            self.output_message.actions.append("Generating search result summary..")
            self.output_message.push_update()

            search_result_text_list = [shot["text"] for shot in shots]
            search_result_text = "\n\n".join(search_result_text_list)
            search_summary_llm_prompt = f"Summarize the search results for query: {query} search results: {search_result_text}"
            search_summary_llm_message = ContextMessage(
                content=search_summary_llm_prompt, role=RoleTypes.user
            )
            llm_response = self.llm.chat_completions(
                [search_summary_llm_message.to_llm_msg()]
            )

            if not llm_response.status:
                search_summary_content.status = MsgStatus.error
                search_summary_content.status_message = (
                    "Failed to generate the summary of search results."
                )
                logger.error(f"LLM failed with {llm_response}")
            else:
                search_summary_content.text = llm_response.content
                search_summary_content.status = MsgStatus.success
                search_summary_content.status_message = (
                    "Here is the summary of search results."
                )

            self.output_message.publish()

            return AgentResponse(
                status=AgentStatus.SUCCESS,
                message="Search done and showed above to user.",
                data={
                    "message": "Search done.",
                    "stream_link": compilation_stream_url,
                    "search_results": search_result_videos,
                },
            )

        except ValueError as ve:
            logger.error(f"ValueError in {self.agent_name}: {ve}")
            if search_result_content.status != MsgStatus.success:
                search_result_content.status = MsgStatus.error
                search_result_content.status_message = "Failed to get search results."

            return AgentResponse(
                status=AgentStatus.ERROR,
                message=f"{ve}",
            )

        except Exception as e:
            logger.exception(f"Error in {self.agent_name}.")
            if search_result_content.status != MsgStatus.success:
                search_result_content.status = MsgStatus.error
                search_result_content.status_message = "Failed to get search results."
            elif compilation_content.status != MsgStatus.success:
                compilation_content.status = MsgStatus.error
                compilation_content.status_message = (
                    "Failed to create compilation of search results."
                )
            elif search_summary_content.status != MsgStatus.success:
                search_summary_content.status = MsgStatus.error
                search_summary_content.status_message = (
                    "Failed to generate summary of results."
                )
            return AgentResponse(
                status=AgentStatus.ERROR,
                message=f"Failed the search with exception. {e}",
            )
