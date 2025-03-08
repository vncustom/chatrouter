document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatHistory = document.getElementById('chat-history');
    const modelSelect = document.getElementById('model');
    const apiKeyInput = document.getElementById('api-key');
    const apiStatus = document.getElementById('api-status');
    const saveApiKeyBtn = document.getElementById('save-api-key');
    const attachBtn = document.getElementById('attach-btn');
    const fileInput = document.getElementById('file-input');
    const attachmentArea = document.getElementById('attachment-area');
    
    // State
    let apiKey = localStorage.getItem('openrouter_api_key') || '';
    let attachedFiles = [];
    
    // Initialize
    if (apiKey) {
        apiKeyInput.value = '********';
        apiStatus.textContent = '✅ Đã lưu';
        apiStatus.className = 'status-success';
    }
    
    // Event Listeners
    saveApiKeyBtn.addEventListener('click', saveApiKey);
    chatForm.addEventListener('submit', sendMessage);
    attachBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);
    
    // Kiểm tra kết nối API
    checkApiStatus();
    
    // Xác thực API key nếu đã lưu
    if (apiKey) {
        validateApiKey();
    }
    
    // Functions
    function saveApiKey() {
        const key = apiKeyInput.value.trim();
        if (key) {
            apiKey = key;
            localStorage.setItem('openrouter_api_key', key);
            apiKeyInput.value = '********';
            apiStatus.textContent = '✅ Đã lưu';
            apiStatus.className = 'status-success';
            
            // Hiển thị thông báo về API key đã lưu
            addMessage('system', 'API Key đã được lưu thành công');
            
            // Xác thực API key
            validateApiKey();
        } else {
            alert('Vui lòng nhập API Key');
        }
    }
    
    function validateApiKey() {
        if (apiKey) {
            addMessage('system', 'Đang xác thực API key...');
            
            fetch('https://openrouter.ai/api/v1/auth/key', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${apiKey}`,
                    'HTTP-Referer': window.location.origin
                }
            })
            .then(response => {
                if (response.ok) {
                    return response.json();
                }
                throw new Error(`API key verification failed: ${response.status}`);
            })
            .then(data => {
                // Xóa thông báo "Đang xác thực API key..."
                const loadingMessage = document.querySelector('.system-message:last-child');
                if (loadingMessage && loadingMessage.querySelector('.message-content').textContent === 'Đang xác thực API key...') {
                    loadingMessage.remove();
                }
                
                addMessage('system', 'API key hợp lệ ✅');
            })
            .catch(error => {
                // Xóa thông báo "Đang xác thực API key..."
                const loadingMessage = document.querySelector('.system-message:last-child');
                if (loadingMessage && loadingMessage.querySelector('.message-content').textContent === 'Đang xác thực API key...') {
                    loadingMessage.remove();
                }
                
                addMessage('system', `Lỗi xác thực API key: ${error.message}. Vui lòng kiểm tra lại.`);
                apiStatus.textContent = '❌ Không hợp lệ';
                apiStatus.className = 'status-error';
                apiKey = '';
                localStorage.removeItem('openrouter_api_key');
            });
        }
    }
    
    async function checkApiStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (data.status === "ok") {
                console.log("API connection successful: ", data);
                addMessage('system', `Kết nối tới server thành công. Thời gian server: ${data.timestamp}`);
            } else {
                console.error("API returned unexpected status", data);
                addMessage('system', 'API trả về trạng thái không mong đợi');
            }
        } catch (error) {
            console.error("Error checking API status:", error);
            addMessage('system', `Không thể kết nối đến API: ${error.message}`);
        }
    }
    
    function handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            // Check file sizes
            for (let i = 0; i < files.length; i++) {
                if (files[i].size > 5 * 1024 * 1024) { // 5MB limit
                    alert(`File ${files[i].name} vượt quá giới hạn 5MB`);
                    return;
                }
                attachedFiles.push(files[i]);
            }
            updateAttachmentDisplay();
        }
    }
    
    function updateAttachmentDisplay() {
        if (attachedFiles.length === 0) {
            attachmentArea.innerHTML = '';
            return;
        }
        
        let html = '<div class="attachment-list">';
        attachedFiles.forEach((file, index) => {
            html += `
                <div class="attachment-item">
                    <span>${file.name}</span>
                    <span class="remove-attachment" data-index="${index}">×</span>
                </div>
            `;
        });
        html += '</div>';
        
        attachmentArea.innerHTML = html;
        
        // Add event listeners to remove buttons
        document.querySelectorAll('.remove-attachment').forEach(btn => {
            btn.addEventListener('click', function() {
                const index = parseInt(this.getAttribute('data-index'));
                attachedFiles.splice(index, 1);
                updateAttachmentDisplay();
            });
        });
    }
    
    function addMessage(type, content, timestamp = '', files = []) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        let headerText = '';
        switch (type) {
            case 'user':
                headerText = 'Bạn';
                break;
            case 'assistant':
                headerText = 'Assistant';
                break;
            case 'system':
                headerText = 'Hệ thống';
                break;
        }
        
        let timestampText = timestamp ? timestamp : new Date().toLocaleTimeString();
        
        let filesHtml = '';
        if (files && files.length > 0) {
            filesHtml = `<div class="files-info">Files: ${files.join(', ')}</div>`;
        }
        
        messageDiv.innerHTML = `
            <div class="message-header">${headerText} ${timestampText}</div>
            ${filesHtml}
            <div class="message-content">${content}</div>
        `;
        
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }
    
    async function sendMessage(e) {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        const model = modelSelect.value;
        
        if (!message && attachedFiles.length === 0) {
            alert('Vui lòng nhập tin nhắn hoặc đính kèm file');
            return;
        }
        
        if (!apiKey) {
            alert('Vui lòng nhập API Key');
            return;
        }
        
        // Disable input while processing
        messageInput.disabled = true;
        document.getElementById('send-btn').disabled = true;
        
        // Show loading indicator
        const loadingId = 'loading-' + Date.now();
        addMessage('system', 'Đang xử lý...');
        const loadingMessage = chatHistory.lastElementChild;
        loadingMessage.id = loadingId;
        loadingMessage.querySelector('.message-content').classList.add('loading-dots');
        
        // Add user message to chat
        const timestamp = new Date().toLocaleTimeString();
        addMessage('user', message, timestamp);
        
        // Create form data
        const formData = new FormData();
        formData.append('message', message);
        formData.append('model', model);
        formData.append('api_key', apiKey);
        
        // Add files if any
        const fileNames = [];
        if (attachedFiles.length > 0) {
            attachedFiles.forEach(file => {
                formData.append('files', file);
                fileNames.push(file.name);
            });
            
            // Add files info message
            if (fileNames.length > 0) {
                addMessage('system', `Đã đính kèm: ${fileNames.join(', ')}`);
            }
        }
        
        try {
            // Thêm timeout dài hơn (60 giây)
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 60000);
            
            const response = await fetch('/api/chat', {
                method: 'POST',
                body: formData,
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            // Xóa thông báo loading
            const loadingElement = document.getElementById(loadingId);
            if (loadingElement) {
                loadingElement.remove();
            }
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.error) {
                addMessage('system', `Lỗi: ${data.error}`);
            } else {
                addMessage('assistant', data.response, data.timestamp, data.files);
            }
        } catch (error) {
            // Xóa thông báo loading
            const loadingElement = document.getElementById(loadingId);
            if (loadingElement) {
                loadingElement.remove();
            }
            
            if (error.name === 'AbortError') {
                addMessage('system', 'Yêu cầu bị hủy do mất quá nhiều thời gian');
            } else {
                addMessage('system', `Lỗi kết nối: ${error.message}`);
            }
        } finally {
            // Re-enable input
            messageInput.disabled = false;
            document.getElementById('send-btn').disabled = false;
            messageInput.value = '';
            attachedFiles = [];
            updateAttachmentDisplay();
            messageInput.focus();
        }
    }
});