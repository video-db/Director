# import logging
# import json
# import os
# import uuid


# from director.agents.base import BaseAgent, AgentResponse, AgentStatus
# from director.core.session import Session
# from director.tools.videodb_tool import VideoDBTool
# from director.tools.elevenlabs import ElevenLabsTool

# logger = logging.getLogger(__name__)

# GEN_AI_AUDIO_AGENT_PARAMETERS = {
#     "type": "object",
#     "properties": {
#         "collection_id": {
#             "type": "string",
#             "description": "The unique identifier of the collection to store the audio",
#         },
#         "job_type": {
#             "type": "string",
#             "enum": ["text_to_speech", "sound_effect", "speech_to_speech"],
#             "description": """The type of audio generation to perform
#             text_to_speech: 
#                 - converts text to speech
#                 - input: text, voice_id
#                 - output: will be a videodb audio
#             sound_effect: 
#                 - creates a sound effect from a text prompt
#                 - input: prompt, duration
#                 - output: will be a videodb audio
#             """,
#         },
#         "sound_effect": {
#             "type": "object",
#             "properties": {
#                 "prompt": {
#                     "type": "string",
#                     "description": "The prompt to generate the sound effect",
#                 },
#                 "duration": {
#                     "type": "number",
#                     "description": "The duration of the sound effect in seconds",
#                     "default": 2,
#                 },
#             },
#             "required": ["prompt"],
#         },
#         "text_to_speech": {
#             "type": "object",
#             "properties": {
#                 "text": {
#                     "type": "string",
#                     "description": "The text to convert to speech",
#                 },
#                 "voice_id": {
#                     "type": "string",
#                     "description": "The ID of the voice to use for speech generation",
#                 },
#             },
#             "required": ["text"],
#         },
#     },
#     "required": ["job_type", "collection_id"],
# }


# class GenAIAudioAgent(BaseAgent):
#     def __init__(self, session: Session, **kwargs):
#         self.agent_name = "gen_ai_audio"
#         self.description = (
#             "An agent designed to generate speech and sound effects "
#         )
#         self.parameters = GEN_AI_AUDIO_AGENT_PARAMETERS
#         super().__init__(session=session, **kwargs)

#     def run(
#         self,
#         job_type: str,
#         collection_id: str,
#         *args,
#         **kwargs,
#     ) -> AgentResponse:
#         """
#         Generates audio using ElevenLabs API based on input text.
#         :param str text: The text to convert to speech or sound effect
#         :param str collection_id: The collection ID to store the generated audio
#         :param bool is_sound_effect: Whether to generate sound effect or speech
#         :param str voice_id: Voice ID for speech generation (optional)
#         :param args: Additional positional arguments
#         :param kwargs: Additional keyword arguments
#         :return: Response containing the generated audio URL
#         :rtype: AgentResponse
#         """
#         try:
#             self.videodb_tool = VideoDBTool(collection_id=collection_id)

#             directory_path = os.path.abspath("director/editing_assets")
#             os.makedirs(directory_path, exist_ok=True)
#             file_name = str(uuid.uuid4()) + ".mp3"
#             output_path = os.path.join(directory_path, file_name)
#             if job_type == "sound_effect":
#                 self.output_message.actions.append(
#                     "Generating sound effect from text description"
#                 )
#                 self.output_message.push_update()
#                 args = kwargs.get("sound_effect", {})
#                 result = elevenlabs.text_to_sound_effects.convert(
#                     text=args.get("prompt"),
#                     duration_seconds=args.get("duration"),
#                     prompt_influence=0.3,
#                 )
#             elif job_type == "text_to_speech":
#                 self.output_message.actions.append("Converting text to speech")
#                 self.output_message.push_update()
#                 args = kwargs.get("text_to_speech", {})
#                 print("we got args", args)
#             with open(output_path, "wb") as f:
#                 for chunk in result:
#                     f.write(chunk)
#             media = self.videodb_tool.upload(
#                 output_path, source_type="file_path", media_type="audio"
#             )
#             self.output_message.publish()

#         except Exception as e:
#             logger.exception(f"Error in {self.agent_name} agent: {e}")
#             self.output_message.publish()
#             return AgentResponse(status=AgentStatus.ERROR, message=str(e))

#         return AgentResponse(
#             status=AgentStatus.SUCCESS,
#             message="Audio generated successfully",
#             data={"audio_id": media["id"]},
#         )
