import logging
import json
import concurrent.futures

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import (
    Session,
    ContextMessage,
    RoleTypes,
    MsgStatus,
    VideoContent,
    VideoData,
)
from director.tools.videodb_tool import VideoDBTool
from director.llm.openai import OpenAI

logger = logging.getLogger(__name__)

MEMEMAKER_PARAMETERS = {
    "type": "object",
    "properties": {
        "prompt": {
            "type": "string",
            "description": "Prompt to generate Meme",
        },
        "video_id": {
            "type": "string",
            "description": "Video Id to generate clip",
        },
        "collection_id": {
            "type": "string",
            "description": "Collection Id to of the video",
        },
    },
    "required": ["prompt", "video_id", "collection_id"],
}


class MemeMakerAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "meme_maker"
        self.description = "Generates meme clips and images based on user prompts. This agent usages LLM to analyze the transcript and visual content of the video to generate memes."
        self.parameters = MEMEMAKER_PARAMETERS
        self.llm = OpenAI()
        super().__init__(session=session, **kwargs)

    def _chunk_docs(self, docs, chunk_size):
        """
        chunk docs to fit into context of your LLM
        :param docs:
        :param chunk_size:
        :return:
        """
        for i in range(0, len(docs), chunk_size):
            yield docs[i : i + chunk_size]  # Yield the current chunk

    def _filter_transcript(self, transcript, start, end):
        result = []
        for entry in transcript:
            if float(entry["end"]) > start and float(entry["start"]) < end:
                result.append(entry)
        return result

    def _get_multimodal_docs(self, transcript, scenes, club_on="scene"):
        # TODO: Implement club on transcript
        docs = []
        if club_on == "scene":
            for scene in scenes:
                spoken_result = self._filter_transcript(
                    transcript, float(scene["start"]), float(scene["end"])
                )
                spoken_text = " ".join(
                    entry["text"] for entry in spoken_result if entry["text"] != "-"
                )
                data = {
                    "visual": scene["description"],
                    "spoken": spoken_text,
                    "start": scene["start"],
                    "end": scene["end"],
                }
                docs.append(data)
        return docs

    def _prompt_runner(self, prompts):
        """Run the prompts in parallel."""
        clip_timestamps = []
        image_timestamps = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_index = {
                executor.submit(
                    self.llm.chat_completions,
                    [ContextMessage(content=prompt, role=RoleTypes.user).to_llm_msg()],
                    response_format={"type": "json_object"},
                ): i
                for i, prompt in enumerate(prompts)
            }
            for future in concurrent.futures.as_completed(future_to_index):
                try:
                    llm_response = future.result()
                    if not llm_response.status:
                        logger.error(f"LLM failed with {llm_response.content}")
                        continue
                    output = json.loads(llm_response.content)
                    clip_timestamps.extend(output.get("clip_timestamps", []))
                    image_timestamps.extend(output.get("image_timestamps", []))
                except Exception as e:
                    logger.exception(f"Error in getting matches: {e}")
                    continue
        return {
            "clip_timestamps": clip_timestamps,
            "image_timestamps": image_timestamps,
        }

    def _multimodal_prompter(self, transcript, scene_index, prompt):
        docs = self._get_multimodal_docs(transcript, scene_index)
        chunk_size = 80
        chunks = self._chunk_docs(docs, chunk_size=chunk_size)

        prompts = []
        i = 0
        for chunk in chunks:
            chunk_prompt = f"""
            Input Format:
                You are given visual and spoken information of the video of each second, and a transcipt of what's being spoken along with timestamp.
            
            Task: Analyze video content to identify peak Meme potential clip and images by evaluating:
                1. Memeable Moments
                    - Reaction-worthy facial expressions
                    - Quotable one-liners or catchphrases
                    - Unexpected or comedic timing
                    - Relatable human moments
                    - Visual gags or physical humor

                2. Meme Format Compatibility
                    - Reaction meme potential
                    - Image macro possibilities
                    - Multi-panel story potential
                    - GIF-worthy sequences
                    - Exploitable templates

                3. Virality Indicators
                    - Universal humor/relatability
                    - Clear emotional response triggers
                    - Easy to remix/recontextualize
                    - Cultural reference potential
                    - Distinct visual hooks

            Multimodal Data:
            video: {chunk}
            User Prompt: {prompt}

        
            """
            chunk_prompt += """
            **Output Format**: Return a JSON that containes the  fileds `clip_timestamps` and `image_timestamps`.
            clip_timestamps is from the visual section of the input.
            image_timestamps is the timestamp of the image in the visual section.
            Ensure the final output strictly adheres to the JSON format specified without including additional text, explanations or any extra characters.
            If there is no match return empty list without additional text. Use the following structure for your response:
            {"clip_timestamps": [{"start": start timestamp of the clip, "end": end timestamp of the clip, "text":  "text content of the clip"}], "image_timestamps": [timestamp of the image]}
            """
            prompts.append(chunk_prompt)
            i += 1

        return self._prompt_runner(prompts)

    def _get_scenes(self, video_id):
        self.output_message.actions.append("Retrieving video scenes..")
        self.output_message.push_update()
        scene_index_id = None
        scene_list = self.videodb_tool.list_scene_index(video_id)
        if scene_list:
            scene_index_id = scene_list[0]["scene_index_id"]
            return scene_index_id, self.videodb_tool.get_scene_index(
                video_id=video_id, scene_id=scene_index_id
            )
        else:
            self.output_message.actions.append("Scene index not found")
            self.output_message.push_update()
            raise Exception("Scene index not found, please index the scene first.")

    def _get_transcript(self, video_id):
        self.output_message.actions.append("Retrieving video transcript..")
        self.output_message.push_update()
        try:
            return self.videodb_tool.get_transcript(
                video_id
            ), self.videodb_tool.get_transcript(video_id, text=False)
        except Exception:
            self.output_message.actions.append(
                "Transcript unavailable. Indexing spoken content."
            )
            self.output_message.push_update()
            self.videodb_tool.index_spoken_words(video_id)
            return self.videodb_tool.get_transcript(
                video_id
            ), self.videodb_tool.get_transcript(video_id, text=False)

    def run(
        self, prompt: str, video_id: str, collection_id: str, *args, **kwargs
    ) -> AgentResponse:
        """
        Run the agent to generate meme clips and images based on user prompts.

        :return: The response containing information about the sample processing operation.
        :rtype: AgentResponse
        """
        try:
            self.videodb_tool = VideoDBTool(collection_id=collection_id)
            try:
                _, transcript = self._get_transcript(video_id=video_id)
                scene_index_id, scenes = self._get_scenes(video_id=video_id)

                self.output_message.actions.append("Identifying meme content..")
                self.output_message.push_update()
                result = self._multimodal_prompter(transcript, scenes, prompt)

            except Exception as e:
                logger.exception(f"Error in getting video content: {e}")
                return AgentResponse(status=AgentStatus.ERROR, message=str(e))

            if not result:
                return AgentResponse(
                    status=AgentStatus.SUCCESS,
                    message="No meme content found.",
                    data={},
                )
            self.output_message.actions.append("Key moments identified..")
            self.output_message.actions.append("Creating video clips..")
            self.output_message.push_update()
            success_data = {"clip_timestamps": [], "image_timestamps": []}
            for clip in result["clip_timestamps"]:
                video_content = VideoContent(
                    agent_name=self.agent_name, status=MsgStatus.progress
                )
                self.output_message.content.append(video_content)
                stream_url = stream_url = self.videodb_tool.generate_video_stream(
                    video_id=video_id, timeline=[(clip["start"], clip["end"])]
                )
                video_content.video = VideoData(stream_url=stream_url)
                video_content.status_message = f'Clip "{clip["text"]}" generated.'
                video_content.status = MsgStatus.success
                clip["stream_url"] = stream_url
                success_data["clip_timestamps"].append(clip)
                self.output_message.publish()

        except Exception as e:
            logger.exception(f"Error in {self.agent_name}")
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))

        return AgentResponse(
            status=AgentStatus.SUCCESS,
            message=f"Agent {self.name} completed successfully.",
            data=success_data,
        )
