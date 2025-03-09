from http.server import BaseHTTPRequestHandler
import json
import os
import requests
import base64
import cgi
import io
import uuid
import tempfile

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Get content type
        content_type = self.headers.get('Content-Type', '')
        
        # Handle multipart/form-data (file uploads)
        if content_type.startswith('multipart/form-data'):
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': content_type,
                }
            )
            
            # Extract form fields
            prompt = form.getvalue('prompt', '')
            model = form.getvalue('model', 'deepseek/deepseek-r1:free')
            
            # Process files
            files = []
            if 'files' in form:
                file_items = form['files']
                # Handle multiple files
                if isinstance(file_items, list):
                    for file_item in file_items:
                        if file_item.file:
                            file_data = file_item.file.read()
                            file_name = file_item.filename
                            mime_type = self._get_mime_type(file_name)
                            files.append({
                                'name': file_name,
                                'data': base64.b64encode(file_data).decode('utf-8'),
                                'mime_type': mime_type
                            })
                # Handle single file
                elif file_items.file:
                    file_data = file_items.file.read()
                    file_name = file_items.filename
                    mime_type = self._get_mime_type(file_name)
                    files.append({
                        'name': file_name,
                        'data': base64.b64encode(file_data).decode('utf-8'),
                        'mime_type': mime_type
                    })
        
        # Handle application/json
        else:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            prompt = data.get('prompt', '')
            model = data.get('model', 'deepseek/deepseek-r1:free')
            files = data.get('files', [])
        
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
        
        # Prepare messages with files if applicable
        messages = []
        
        # Add files to the message content if there are any
        if files and len(files) > 0:
            # Check if the model supports image input
            if self._model_supports_images(model):
                content = []
                
                # Add text part
                if prompt:
                    content.append({
                        "type": "text",
                        "text": prompt
                    })
                
                # Add image parts
                for file in files:
                    if self._is_image_file(file.get('name', '')):
                        content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{file.get('mime_type', 'image/jpeg')};base64,{file.get('data')}"
                            }
                        })
                
                messages.append({
                    "role": "user",
                    "content": content
                })
            else:
                # For models that don't support images, just use the text
                messages.append({
                    "role": "user",
                    "content": f"{prompt}\n\n(Note: Files were attached but this model doesn't support image input)"
                })
        else:
            # No files, just text
            messages.append({
                "role": "user",
                "content": prompt
            })
        
        # Request payload
        payload = {
            "model": model,
            "messages": messages
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
    
    def _get_mime_type(self, filename):
        """Get MIME type based on file extension"""
        ext = os.path.splitext(filename)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        return mime_types.get(ext, 'application/octet-stream')
    
    def _is_image_file(self, filename):
        """Check if the file is an image based on extension"""
        ext = os.path.splitext(filename)[1].lower()
        return ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    
    def _model_supports_images(self, model):
        """Check if the model supports image input"""
        # List of models that support image input
        # This is a simplified list and may need to be updated
        vision_models = [
            'qwen/qwen2.5-vl-72b-instruct',
            'google/gemini-2.0-pro',
            'google/gemini-2.0-flash',
            'google/gemini-2.0-pro-exp-02-05',
            'google/gemini-2.0-flash-exp',
            'google/gemini-2.0-flash-thinking-exp'
        ]
        
        # Extract the base model name without the ":free" suffix
        base_model = model.split(':')[0] if ':' in model else model
        
        return any(base_model.startswith(vm) for vm in vision_models)

