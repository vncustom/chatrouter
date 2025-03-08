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
    
    // Functions
    function saveApiKey() {
        const key = apiKeyInput.value.trim();
        if (key) {
            apiKey = key;
            localStorage.setItem('openrouter_api_key', key);
            apiKeyInput.value = '********';
            apiStatus.textContent = '✅ Đã lưu';
            apiStatus.className = 'status-success';
        } else {
            alert('Vui lòng nhập API Key');
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
        
        let filesHtml = '';
        if (files && files.length > 0) {
            filesHtml = `<div class="files-info">Files: ${files.join(', ')}</div>`;
        }
        
        messageDiv.innerHTML = `
            <div class="message-header">${headerText} ${timestamp}</div>
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
            const response = await fetch('/api/chat', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.error) {
                addMessage('system', `Lỗi: ${data.error}`);
            } else {
                addMessage('assistant', data.response, data.timestamp, data.files);
            }
        } catch (error) {
            addMessage('system', `Lỗi kết nối: ${error.message}`);
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