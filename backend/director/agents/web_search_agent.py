from dotenv import load_dotenv
import logging
import os

from director.agents.base import BaseAgent, AgentResponse, AgentStatus
from director.core.session import (Session, TextContent, MsgStatus,)

from director.tools.serpapi import SerpApi
from director.tools.jina_reranker import JinaReranker


load_dotenv()
logger = logging.getLogger(__name__)

class WebSearchAgent(BaseAgent):
    def __init__(self, session: Session, **kwargs):
        self.agent_name = "Web_Search_Agent"
        self.description = "Searches for web links and videos based on the query and provide most relevant ranked responses."
        self.parameters = self.get_parameters()
        
        # SERP API configuration
        self.serp_api_key = os.getenv('SERP_API_KEY')

        # Jina Reranker API configuration
        self.jina_api_key = os.getenv('JINA_RERANK_API_KEY')

        super().__init__(session=session, **kwargs)

    def get_parameters(self):
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Comprehensive search query to fetch web links, articles, and videos",
                    "minLength": 1,
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of search results to retrieve (web links and/or videos)",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20,
                },
                "content_type": {
                    "type": "string",
                    "description": "Specify content type for targeted search results either text or videos",
                    "enum": ["text", "videos"],
                    "default": "videos",
                },
            },
            "required": ["query", "content_type"],
        }

    def run(self, query: str, content_type: str = "text", max_results: int = 5, *args, **kwargs) -> AgentResponse:


        text_content = TextContent(
            agent_name=self.agent_name,
            status=MsgStatus.progress,
            status_message=f"Searching Web for content: {query}...",
        )

        self.output_message.content.append(text_content)
        self.output_message.push_update()

        serp_api = SerpApi(api_key=self.serp_api_key)

        try:
            search_results = serp_api.search(query, max_results, content_type)
            if not search_results:
                text_content.status = MsgStatus.error
                text_content.status_message = "No search results found. Please try again."
                self.output_message.publish()
                return AgentResponse(
                    status=AgentStatus.ERROR,
                    message="No search results found.",
                    data={"results": []},
                )
            
            # Format search results for jina reranker
            documents = []
            reranker_documents = []
            
            if content_type == "text":
                knowledge_graph = search_results.get("knowledge_graph")
                if knowledge_graph:
                    title = knowledge_graph.get("source", {}).get("name")
                    link = knowledge_graph.get("source", {}).get("link")
                    description = knowledge_graph.get("description", "No description available.")
                    if title and link:
                        documents.append({
                            "index": len(documents),
                            "title": title,
                            "link": link,
                            "snippet": description
                        })
                        reranker_documents.append(f"Search Title: {result.get('title')}. Search Snippet: {result.get('snippet')}.")

                for result in search_results.get("organic_results", []):
                    title = result.get("title")
                    link = result.get("link")
                    snippet = result.get("snippet", "No description available.")
                    if title and link:
                        documents.append({
                            "index": len(documents),
                            "title": title,
                            "link": link,
                            "snippet": snippet
                        })
                        reranker_documents.append(f"Search Title: {result.get('title')}. Search Snippet: {result.get('snippet')}.")

            elif content_type == "videos":
                for result in search_results.get("video_results", []):
                    link = result.get("link", "")
                    video_link = result.get("video_link", "")

                    # Skip channels, playlists, or invalid links
                    if "channel" in link or "user" in link or "playlist" in link or "watch?v=" not in link:
                        continue

                    # Prefer YouTube videos or links with valid video_link
                    if "youtube.com/watch" in link or video_link:
                        documents.append({
                            "index": len(documents),
                            "link": link,
                            "video_link": video_link,
                            "title": result.get("title"),
                            "duration": result.get("duration"),
                            "thumbnail": result.get("thumbnail"),
                            "snippet": result.get("snippet", "No description available.")
                        })
                        reranker_documents.append(f"Video Title: {result.get('title')}. Video Snippet: {result.get('snippet')}. Duration: {result.get('duration')}.")

            reranker_api = JinaReranker(api_key=self.jina_api_key)             
            # Call the reranker API
            reranked_results = reranker_api.rerank(query, reranker_documents, max_results)

            # Re-rank documents based on new indices
            reranked_indices = {item["index"]: idx for idx, item in enumerate(reranked_results["results"])}
            reranked_documents = []

            for item in reranked_results["results"]:
                old_index = item["index"]
                if old_index < len(documents):
                    # Merge old metadata with the new rank order
                    full_data = {**documents[old_index], "relevance_score": item["relevance_score"]}
                    reranked_documents.append(full_data)

            # Sort documents by their new rank
            reranked_documents.sort(key=lambda x: reranked_indices.get(x["index"], float("inf")))
            
            agent_results = [
                {
                    "content_type": content_type,
                    "source": r.get("link") or r.get("video_link"),
                    "source_type": "url",
                    "snippet": r.get("snippet") or None,
                    "media_type": "video" if content_type == "videos" else "text",
                    "name": r.get("title") or f"Untitled Video {idx + 1}",
                    "thumbnail": r.get("thumbnail") or None,
                    "duration": r.get("duration") or "unknown",
                }
                for idx, r in enumerate(reranked_documents)
                if r.get("link") or r.get("video_link")
            ]

            suggested = agent_results[0] if reranked_documents else None

            text_content.status = MsgStatus.success
            text_content.status_message = f"Found {len(reranked_documents)} results."
            self.output_message.publish()

            return AgentResponse(
                status=AgentStatus.SUCCESS,
                message="Search completed successfully.",
                data={"results": agent_results, "suggested": suggested},
            )
        
        except RuntimeError as e:
            logger.exception(f"Error in SerpAPI call: {e}")
            text_content.status = MsgStatus.error
            text_content.status_message = "An error occurred while searching on Web."
            self.output_message.publish()
            return AgentResponse(
                status=AgentStatus.ERROR,
                message="An error occurred during the Web search. Please try again later.",
            )

