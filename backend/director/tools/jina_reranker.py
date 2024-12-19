import requests

class JinaReranker:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Please provide a valid Jina_Rerank Api key")
        self.api_key = api_key
        self.base_url = 'https://api.jina.ai/v1/rerank'


    def rerank(self, query: str, documents: list, max_results: int = 5):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.api_key
        }

        payload = {
            "model": "jina-reranker-v2-base-multilingual",
            "query": query,
            "top_n": max_results,
            "documents": documents
        }
        try:
            response = requests.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Error while Reranking Search Results {e}")
            