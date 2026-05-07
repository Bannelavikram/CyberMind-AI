document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chat-container');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const modeBtns = document.querySelectorAll('.mode-btn');
    const connectionStatus = document.getElementById('connection-status');
    
    let currentMode = 'chat';

    // Auto-resize textarea
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if(this.value === '') this.style.height = 'auto';
    });

    // Mode Selection
    modeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            modeBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentMode = btn.dataset.mode;
            addSystemMessage(`Mode switched to: ${btn.innerText}`);
        });
    });

    // Send Message Function
    async function sendMessage() {
        const text = userInput.value.trim();
        if (!text) return;

        // Add User Message
        addMessage(text, 'user');
        userInput.value = '';
        userInput.style.height = 'auto';

        // Show Typing Indicator
        const typingId = showTypingIndicator();

        try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 60000);

    const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, mode: currentMode }),
        signal: controller.signal
    });

    clearTimeout(timeout);

    if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
    }

    const data = await response.json();
    removeTypingIndicator(typingId);

   if (data.response) {
    let safeText = data.response.substring(0, 300);  // 🔥 limit size
    addMessage(safeText, 'ai');
} else if (data.error) {
        addMessage(`Backend Error: ${data.error}`, 'ai');
    } else {
        addMessage("Unexpected response from server.", 'ai');
    }

} catch (error) {
    removeTypingIndicator(typingId);

    if (error.name === "AbortError") {
        addMessage("Request timed out. Try again.", 'ai');
    } else {
        addMessage(`Error: ${error.message}`, 'ai');
    }

    console.error("Frontend Error:", error);

    connectionStatus.innerText = "Offline";
    connectionStatus.style.color = "#ff4444";
    document.querySelector('.dot').style.backgroundColor = "#ff4444";
    document.querySelector('.dot').style.boxShadow = "0 0 8px #ff4444";
}
    }

    // Event Listeners
    sendBtn.addEventListener('click', sendMessage);

    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // UI Helpers
    function addMessage(text, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', sender === 'user' ? 'user-message' : 'ai-message');
        
        const avatar = document.createElement('div');
        avatar.classList.add('avatar');
        avatar.innerText = sender === 'user' ? 'YOU' : 'AI';
        
        const bubble = document.createElement('div');
        bubble.classList.add('bubble');
        
        // Simple formatting for structured output
        let formattedText = text;
        if (sender === 'ai') {
    formattedText = text;   // 🔥 disable heavy formatting
}
        
        bubble.innerText = formattedText;
        
        msgDiv.appendChild(avatar);
        msgDiv.appendChild(bubble);
        chatContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    function addSystemMessage(text) {
        const msgDiv = document.createElement('div');
        msgDiv.style.textAlign = 'center';
        msgDiv.style.fontSize = '12px';
        msgDiv.style.color = 'var(--text-muted)';
        msgDiv.style.margin = '10px 0';
        msgDiv.innerText = text;
        chatContainer.appendChild(msgDiv);
        scrollToBottom();
    }

    function showTypingIndicator() {
        const id = 'typing-' + Date.now();
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', 'ai-message');
        msgDiv.id = id;
        
        const avatar = document.createElement('div');
        avatar.classList.add('avatar');
        avatar.innerText = 'AI';
        
        const bubble = document.createElement('div');
        bubble.classList.add('bubble');
        bubble.innerHTML = '<span class="typing-indicator">Analyzing...</span>';
        
        msgDiv.appendChild(avatar);
        msgDiv.appendChild(bubble);
        chatContainer.appendChild(msgDiv);
        scrollToBottom();
        return id;
    }

    function removeTypingIndicator(id) {
        const element = document.getElementById(id);
        if (element) element.remove();
    }

    function scrollToBottom() {
       setTimeout(() => {
    chatContainer.appendChild(msgDiv);
    scrollToBottom();
}, 0);
    }

    function formatStructuredOutput(text) {
        // Basic markdown-like formatting for security output
        let html = text;
        const sections = ['[Analysis]', '[Attack Path]', '[Risk Level]', '[Fix]', '[Potential Vulnerability Chain]', '[Mitigation]', '[Surface Analysis]', '[Security Flaws]', '[Refactored Secure Code]'];
        
        sections.forEach(sec => {
            const regex = new RegExp(`(${sec})`, 'g');
            html = html.replace(regex, '<strong>$1</strong>');
        });

        // Convert newlines to breaks
        html = html.replace(/\n/g, '<br>');
        
        return html;
    }
});
