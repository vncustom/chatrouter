from http.server import BaseHTTPRequestHandler
import json
import os
import requests
import urllib.parse

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        query = data.get('query', '')
        
        if not query:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"error": "No search query provided"}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return
        
        try:
            # Use SerpAPI if available
            serpapi_key = os.environ.get('SERPAPI_KEY')
            if serpapi_key:
                search_results = self._search_with_serpapi(query, serpapi_key)
            else:
                # Fallback to a simpler search method
                search_results = self._search_fallback(query)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(search_results).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"error": f"Search failed: {str(e)}"}
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def _search_with_serpapi(self, query, api_key):
        """Search using SerpAPI"""
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": api_key,
            "engine": "google"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        results = []
        
        # Extract organic results
        if "organic_results" in data:
            for result in data["organic_results"][:5]:  # Limit to top 5 results
                results.append({
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", "")
                })
        
        return {
            "results": results,
            "query": query
        }
    
    def _search_fallback(self, query):
        """Fallback search method using DuckDuckGo API"""
        # This is a simple implementation using DuckDuckGo's API
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json"
        
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        results = []
        
        # Extract results from DuckDuckGo response
        if "RelatedTopics" in data:
            for topic in data["RelatedTopics"][:5]:  # Limit to top 5 results
                if "Text" in topic and "FirstURL" in topic:
                    results.append({
                        "title": topic.get("Text", "").split(" - ")[0] if " - " in topic.get("Text", "") else topic.get("Text", ""),
                        "link": topic.get("FirstURL", ""),
                        "snippet": topic.get("Text", "")
                    })
        
        # If no results from DuckDuckGo, provide a message
        if not results:
            return {
                "results": [],
                "query": query,
                "message": "No search results found. Try a different query or enable SERPAPI_KEY for better results."
            }
        
        return {
            "results": results,
            "query": query
        }

