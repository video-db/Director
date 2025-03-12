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
from director.llm import get_default_llm

logger = logging.getLogger(__name__)

PROMPTCLIP_AGENT_PARAMETERS = {
    "type": "object",
    "properties": {
        "prompt": {
            "type": "string",
            "description": "Prompt to generate clip",
        },
        "content_type": {
            "type": "string",
            "enum": ["spoken_content", "visual_content", "multimodal"],
            "default": "spoken_content",
            "description": "Type of content based on which clip is to be generated, default is spoken_content, spoken_content: based on transcript of the video, visual_content: based on visual description of the video, multimodal: based on both transcript and visual description of the video",
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
    "required": ["prompt", "content_type", "video_id", "collection_id"],
}


class PromptClipAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "prompt_clip"
        # TODO: Improve this
        self.description = "Generates video clips based on user prompts. This agent uses AI to analyze the text of a video transcript and identify sentences relevant to the user prompt for making clips. It then generates video clips based on the identified sentences. Use this tool to create clips based on specific themes or topics from a video."
        self.parameters = PROMPTCLIP_AGENT_PARAMETERS
        self.llm = get_default_llm()
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
        matches = []
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
                    matches.extend(output["sentences"])
                except Exception as e:
                    logger.exception(f"Error in getting matches: {e}")
                    continue
        return matches

    def _text_prompter(self, transcript_text, prompt):
        chunk_size = 10000
        # sentence tokenizer
        chunks = self._chunk_docs(transcript_text, chunk_size=chunk_size)
        prompts = []
        i = 0
        for chunk in chunks:
            chunk_prompt = """
            You are a video editor who uses AI. Given a user prompt and transcript of a video analyze the text to identify sentences in the transcript relevant to the user prompt for making clips. 
            - **Instructions**: 
            - Evaluate the sentences for relevance to the specified user prompt.
            - Make sure that sentences start and end properly and meaningfully complete the discussion or topic. Choose the one with the greatest relevance and longest.
            - We'll use the sentences to make video clips in future, so optimize for great viewing experience for people watching the clip of these.
            - Strictly make each result minimum 20 words long. If the match is smaller, adjust the boundries and add more context around the sentences.

            - **Output Format**: Return a JSON list of strings named 'sentences' that containes the output sentences, make sure they are exact substrings.
            - **User Prompts**: User prompts may include requests like 'find funny moments' or 'find moments for social media'. Interpret these prompts by 
            identifying keywords or themes in the transcript that match the intent of the prompt.
            """
            # pass the data
            chunk_prompt += f"""
            Transcript: {chunk}
            User Prompt: {prompt}
            """
            # Add instructions to always return JSON at the end of processing.
            chunk_prompt += """
            Ensure the final output strictly adheres to the JSON format specified without including additional text or explanations. \
            If there is no match return empty list without additional text. Use the following structure for your response:
            {
            "sentences": [
                {},
                ...
            ]
            }
            """
            prompts.append(chunk_prompt)
            i += 1

        return self._prompt_runner(prompts)

    def _scene_prompter(self, scene_index, prompt):
        chunk_size = 10000
        chunks = self._chunk_docs(scene_index, chunk_size=chunk_size)

        prompts = []
        i = 0
        for chunk in chunks:
            descriptions = [scene["description"] for scene in chunk]
            chunk_prompt = """
            You are a video editor who uses AI. Given a user prompt and AI-generated scene descriptions of a video, analyze the descriptions to identify segments relevant to the user prompt for creating clips.

            - **Instructions**: 
                - Evaluate the scene descriptions for relevance to the specified user prompt.
                - Choose description with the highest relevance and most comprehensive content.
                - Optimize for engaging viewing experiences, considering visual appeal and narrative coherence.

                - User Prompts: Interpret prompts like 'find exciting moments' or 'identify key plot points' by matching keywords or themes in the scene descriptions to the intent of the prompt.
            """

            chunk_prompt += f"""
            Descriptions: {json.dumps(descriptions)}
            User Prompt: {prompt}
            """

            chunk_prompt += """
            **Output Format**: Return a JSON list of strings named 'result' that containes the  fileds `sentence` Ensure the final output
            strictly adheres to the JSON format specified without including additional text or explanations. \
            If there is no match return empty list without additional text. Use the following structure for your response:
            {"sentences": []}
            """
            prompts.append(chunk_prompt)
            i += 1

        return self._prompt_runner(prompts)

    def _multimodal_prompter(self, transcript, scene_index, prompt):
        docs = self._get_multimodal_docs(transcript, scene_index)
        chunk_size = 80
        chunks = self._chunk_docs(docs, chunk_size=chunk_size)

        prompts = []
        i = 0
        for chunk in chunks:
            chunk_prompt = f"""
            You are given visual and spoken information of the video of each second, and a transcipt of what's being spoken along with timestamp.
            Your task is to evaluate the data for relevance to the specified user prompt.
            Corelate visual and spoken content to find the relevant video segment.

            Multimodal Data:
            video: {chunk}
            User Prompt: {prompt}

        
            """
            chunk_prompt += """
            **Output Format**: Return a JSON list of strings named 'result' that containes the  fileds `sentence`.
            sentence is from the visual section of the input.
            Ensure the final output strictly adheres to the JSON format specified without including additional text or explanations.
            If there is no match return empty list without additional text. Use the following structure for your response:
            {"sentences": []}
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
        self,
        prompt: str,
        content_type: str,
        video_id: str,
        collection_id: str,
        *args,
        **kwargs,
    ) -> AgentResponse:
        try:
            self.videodb_tool = VideoDBTool(collection_id=collection_id)
            result = []
            try:
                if content_type == "spoken_content":
                    transcript_text, _ = self._get_transcript(video_id=video_id)
                    result = self._text_prompter(transcript_text, prompt)

                elif content_type == "visual_content":
                    scene_index_id, scenes = self._get_scenes(video_id=video_id)
                    result = self._scene_prompter(scenes, prompt)

                else:
                    _, transcript = self._get_transcript(video_id=video_id)
                    scene_index_id, scenes = self._get_scenes(video_id=video_id)
                    result = self._multimodal_prompter(transcript, scenes, prompt)

            except Exception as e:
                logger.exception(f"Error in getting video content: {e}")
                return AgentResponse(status=AgentStatus.ERROR, message=str(e))

            self.output_message.actions.append("Identifying key moments..")
            self.output_message.push_update()
            result_timestamps = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                if content_type == "spoken_content":
                    future_to_index = {
                        executor.submit(
                            self.videodb_tool.keyword_search,
                            query=description,
                            video_id=video_id,
                        ): description
                        for description in result
                    }
                else:
                    future_to_index = {
                        executor.submit(
                            self.videodb_tool.keyword_search,
                            query=description,
                            index_type="scene",
                            video_id=video_id,
                            scene_index_id=scene_index_id,
                        ): description
                        for description in result
                    }

                for future in concurrent.futures.as_completed(future_to_index):
                    description = future_to_index[future]
                    try:
                        search_res = future.result()
                        matched_segments = search_res.get_shots()
                        video_shot = matched_segments[0]
                        result_timestamps.append(
                            (video_shot.start, video_shot.end, video_shot.text)
                        )
                    except Exception as e:
                        logger.error(
                            f"Error in getting timestamps of {description}: {e}"
                        )
                        continue
            if result_timestamps:
                try:
                    self.output_message.actions.append("Key moments identified..")
                    self.output_message.actions.append("Creating video clip..")
                    video_content = VideoContent(
                        agent_name=self.agent_name, status=MsgStatus.progress
                    )
                    self.output_message.content.append(video_content)
                    self.output_message.push_update()
                    timeline = []
                    for timestamp in result_timestamps:
                        timeline.append((timestamp[0], timestamp[1]))
                    stream_url = self.videodb_tool.generate_video_stream(
                        video_id=video_id, timeline=timeline
                    )
                    video_content.status_message = "Clip generated successfully."
                    video_content.video = VideoData(stream_url=stream_url)
                    video_content.status = MsgStatus.success
                    self.output_message.publish()

                except Exception as e:
                    logger.exception(f"Error in creating video content: {e}")
                    return AgentResponse(status=AgentStatus.ERROR, message=str(e))

                return AgentResponse(
                    status=AgentStatus.SUCCESS,
                    message=f"Agent {self.name} completed successfully.",
                    data={"stream_url": stream_url},
                )
            else:
                return AgentResponse(
                    status=AgentStatus.ERROR,
                    message="No relevant moments found.",
                )

        except Exception as e:
            logger.exception(f"error in {self.agent_name}")
            return AgentResponse(status=AgentStatus.ERROR, message=str(e))
