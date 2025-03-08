from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    data = request.json
    prompt = data.get('prompt', '')
    model = data.get('model', 'anthropic/claude-3.5-sonnet')
    
    # Get API key from environment variable
    api_key = os.getenv('OPENROUTER_API_KEY')
    
    if not api_key:
        return jsonify({"error": "OpenRouter API key not found. Please set the OPENROUTER_API_KEY environment variable."}), 400
    
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
            return jsonify({"response": generated_text})
        else:
            return jsonify({"error": "No response generated"}), 500
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"API request failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)

