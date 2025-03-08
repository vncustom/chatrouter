from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
import base64
import os
import hashlib
from typing import List, Optional
from datetime import datetime
import json

app = FastAPI()

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

@app.post("/api/chat")
async def chat(
    message: str = Form(...),
    model: str = Form(...),
    api_key: str = Form(...),
    files: List[UploadFile] = File([])
):
    if not api_key:
        raise HTTPException(status_code=400, detail="API Key không được cung cấp")
    
    # Xử lý file đính kèm nếu có
    attached_contents = []
    file_names = []
    
    for file in files:
        try:
            content = await file.read()
            file_name = file.filename
            file_names.append(file_name)
            
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
                        return {"error": f"Không thể đọc file {file_name}: {str(e)}"}
                
                attached_contents.append(f"File: {file_name}\n{text_content}")
        
        except Exception as e:
            return {"error": f"Lỗi xử lý file {file.filename}: {str(e)}"}
    
    # Thêm nội dung file vào tin nhắn nếu có
    user_message = message
    if attached_contents:
        user_message += "\n\nAttached files content:\n" + "\n\n".join(attached_contents)
    
    # Gọi API OpenRouter
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://yourdomain.vercel.app"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": user_message}]
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code != 200:
            return {"error": f"API Error: {response.text}"}
            
        response_text = response.json()['choices'][0]['message']['content']
        
        # Lưu log
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_data = {
            "timestamp": timestamp,
            "user_message": message,
            "files": file_names,
            "assistant_response": response_text
        }
        
        # Trả về kết quả
        return {
            "response": response_text,
            "timestamp": timestamp,
            "files": file_names
        }
    
    except Exception as e:
        return {"error": str(e)}