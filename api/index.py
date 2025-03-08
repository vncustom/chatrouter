from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import requests
import base64
import os
import hashlib
import sys
import json
from typing import List, Optional
from datetime import datetime

app = FastAPI()

# Thêm middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hàm ghi log
def custom_log(message):
    print(message, file=sys.stderr)
    sys.stderr.flush()

# Thiết lập templates và static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    models = [
        "deepseek/deepseek-r1:free",
        "qwen/qwen2.5-vl-72b-instruct:free",
        "deepseek/deepseek-chat:free",
        "google/gemini-2.0-flash-exp:free",
        "google/gemini-2.0-pro-exp-02-05:free",
        "google/gemini-2.0-flash-thinking-exp:free",
        "meta-llama/llama-3.3-70b-instruct:free"         
    ]
    return templates.TemplateResponse("index.html", {"request": request, "models": models})

@app.get("/api/status")
async def check_status():
    custom_log("Checking API status")
    return {"status": "ok", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

@app.post("/api/chat")
async def chat(
    message: str = Form(...),
    model: str = Form(...),
    api_key: str = Form(...),
    files: List[UploadFile] = File([])
):
    try:
        if not api_key:
            custom_log("API Key không được cung cấp")
            raise HTTPException(status_code=400, detail="API Key không được cung cấp")
        
        # Log để debug
        custom_log(f"Received message: {message}")
        custom_log(f"Model selected: {model}")
        custom_log(f"API key length: {len(api_key)}")
        custom_log(f"Number of files: {len(files)}")
        
        # Xử lý file đính kèm nếu có
        attached_contents = []
        file_names = []
        
        for file in files:
            try:
                content = await file.read()
                file_name = file.filename
                file_names.append(file_name)
                
                # Log thông tin file
                custom_log(f"Processing file: {file_name}, size: {len(content)} bytes")
                
                # Kiểm tra kích thước file (giới hạn 5MB)
                if len(content) > 5 * 1024 * 1024:  # 5MB
                    return {"error": f"File {file_name} vượt quá giới hạn 5MB"}
                
                # Xử lý theo loại file
                if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    # Encode ảnh sang base64
                    encoded = base64.b64encode(content).decode('utf-8')
                    file_ext = file_name.split('.')[-1].lower()
                    attached_contents.append(f"<IMAGE:{file_name}>data:image/{file_ext};base64,{encoded}</IMAGE>")
                else:
                    # Xử lý file text
                    try:
                        text_content = content.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            text_content = content.decode('latin-1')
                        except Exception as e:
                            custom_log(f"Error decoding file {file_name}: {str(e)}")
                            return {"error": f"Không thể đọc file {file_name}: {str(e)}"}
                    
                    attached_contents.append(f"File: {file_name}\n{text_content}")
            
            except Exception as e:
                custom_log(f"Error processing file {file.filename}: {str(e)}")
                return {"error": f"Lỗi xử lý file {file.filename}: {str(e)}"}
        
        # Thêm nội dung file vào tin nhắn nếu có
        user_message = message
        if attached_contents:
            user_message += "\n\nAttached files content:\n" + "\n\n".join(attached_contents)
        
        # Log message đã xử lý
        custom_log(f"Final message length: {len(user_message)}")
        
        # Gọi API OpenRouter
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://chatrouter-mu.vercel.app/"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": user_message}]
        }

        custom_log("Sending request to OpenRouter API...")
        
        # Tăng timeout để tránh lỗi timeout
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        custom_log(f"OpenRouter API response status: {response.status_code}")
        
        if response.status_code != 200:
            error_text = response.text
            custom_log(f"API Error: {error_text}")
            return {"error": f"OpenRouter API Error ({response.status_code}): {error_text}"}
            
        response_data = response.json()
        if 'choices' not in response_data or len(response_data['choices']) == 0:
            custom_log(f"Unexpected API response: {json.dumps(response_data)}")
            return {"error": "OpenRouter API trả về định dạng không hợp lệ"}
            
        response_text = response_data['choices'][0]['message']['content']
        
        # Lưu log
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        custom_log(f"Successful response at {timestamp}")
        
        # Trả về kết quả
        return {
            "response": response_text,
            "timestamp": timestamp,
            "files": file_names
        }
    
    except requests.exceptions.Timeout:
        custom_log("Request to OpenRouter API timed out")
        return {"error": "Kết nối đến OpenRouter API bị timeout"}
    except requests.exceptions.ConnectionError as e:
        custom_log(f"Connection error: {str(e)}")
        return {"error": f"Lỗi kết nối đến OpenRouter API: {str(e)}"}
    except Exception as e:
        import traceback
        custom_log(f"Unexpected error: {str(e)}")
        custom_log(traceback.format_exc())
        return {"error": f"Lỗi không xác định: {str(e)}"}