import logging
import requests
from typing import List, Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class WebSearchService:
    """Service for external web search using Tavily AI"""
    
    def __init__(self):
        self.api_key = settings.tavily_api_key
        self.base_url = "https://api.tavily.com/search"
        
    def search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search the web for a given query
        
        Args:
            query: The search query string
            max_results: Maximum number of search results to return
            
        Returns:
            A list of search results, each containing:
            - title: The page title
            - url: The page URL
            - content: A short snippet of the page's relevant content
        """
        if not self.api_key:
            logger.warning("Tavily API key is not configured. Web search is disabled.")
            return []
            
        try:
            logger.info(f"Performing web search for: {query}")
            
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": max_results,
                "include_answer": False,
                "include_raw_content": False,
                "include_images": False
            }
            
            response = requests.post(self.base_url, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return data.get("results", [])
            
        except Exception as e:
            logger.error(f"Web search failed: {str(e)}")
            return []

    def get_web_context(self, query: str, max_results: int = 3) -> str:
        """
        Perform web search and format results as a context string for the LLM
        """
        results = self.search(query, max_results=max_results)
        
        if not results:
            return ""
            
        context_parts = ["### Latest Web Information\n"]
        for i, res in enumerate(results, 1):
            title = res.get("title", "No Title")
            url = res.get("url", "#")
            content = res.get("content", "No information found.")
            
            context_parts.append(f"{i}. **{title}**\n")
            context_parts.append(f"   *Source:* [{url}]({url})\n")
            context_parts.append(f"   *Content:* {content}\n")
            
        return "\n".join(context_parts)

# Singleton instance
web_search_service = WebSearchService()
