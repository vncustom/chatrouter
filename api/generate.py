from http.server import BaseHTTPRequestHandler
import json
import os
import requests

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        prompt = data.get('prompt', '')
        model = data.get('model', 'anthropic/claude-3.5-sonnet')
        
        # Get API key from environment variable
        api_key = os.environ.get('OPENROUTER_API_KEY')
        
        if not api_key:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"error": "OpenRouter API key not found. Please set the OPENROUTER_API_KEY environment variable."}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return
        
        # OpenRouter API endpoint
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Request headers
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Request payload
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        try:
            # Make the API request
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            # Parse the response
            result = response.json()
            
            # Extract the generated text
            if 'choices' in result and len(result['choices']) > 0:
                generated_text = result['choices'][0]['message']['content']
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response_data = {"response": generated_text}
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
            else:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response_data = {"error": "No response generated"}
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
                
        except requests.exceptions.RequestException as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_data = {"error": f"API request failed: {str(e)}"}
            self.wfile.write(json.dumps(response_data).encode('utf-8'))

