class ZUSChatBot {
    constructor() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatForm = document.getElementById('chatForm');
        this.loadingIndicator = document.getElementById('loadingIndicator');
        
        this.init();
    }
    
    init() {
        // Form submission handler
        this.chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });
        
        // Enter key handler
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-focus input
        this.messageInput.focus();
        
        // Auto-scroll to bottom on load
        this.scrollToBottom();
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Clear input immediately
        this.messageInput.value = '';
        this.setLoading(true);
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        try {
            // Send to API
            const response = await fetch('/rag/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: message })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Add bot response
            this.addMessage(data.answer, 'bot', data.sources);
            
        } catch (error) {
            console.error('Chat error:', error);
            
            let errorMessage = "I'm sorry, I'm having trouble connecting right now. ";
            
            if (error.message.includes('500')) {
                errorMessage += "The server encountered an error. Please try again in a moment.";
            } else if (error.message.includes('timeout') || error.name === 'TimeoutError') {
                errorMessage += "The request timed out. This might happen on the first request as I wake up. Please try again.";
            } else if (!navigator.onLine) {
                errorMessage += "Please check your internet connection.";
            } else {
                errorMessage += "Please try again later.";
            }
            
            this.addMessage(errorMessage, 'bot');
        } finally {
            this.setLoading(false);
            this.messageInput.focus();
        }
    }
    
    addMessage(content, sender, sources = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const avatar = sender === 'bot' ? '🤖' : '👤';
        
        let sourcesHtml = '';
        if (sources && sources.length > 0) {
            const sourcesList = sources
                .filter(source => source && source.trim())
                .map(source => source.replace('data/', ''))
                .join(', ');
            
            if (sourcesList) {
                sourcesHtml = `<div class="sources">📚 Sources: ${sourcesList}</div>`;
            }
        }
        
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <p>${this.formatMessage(content)}</p>
                ${sourcesHtml}
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    formatMessage(message) {
        // Basic text formatting
        return message
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
    }
    
    setLoading(isLoading) {
        if (isLoading) {
            this.loadingIndicator.style.display = 'flex';
            this.sendButton.disabled = true;
            this.messageInput.disabled = true;
        } else {
            this.loadingIndicator.style.display = 'none';
            this.sendButton.disabled = false;
            this.messageInput.disabled = false;
        }
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 100);
    }
    
    // Add some sample questions for users
    addSampleQuestions() {
        const samples = [
            "What drinkware products do you have?",
            "Where is the nearest ZUS outlet?",
            "What are the opening hours?",
            "Tell me about your tumblers"
        ];
        
        const sampleDiv = document.createElement('div');
        sampleDiv.className = 'message bot-message';
        sampleDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <p>Here are some things you can ask me:</p>
                <div class="sample-questions">
                    ${samples.map(q => `<button class="sample-question" onclick="chatBot.askSample('${q}')">${q}</button>`).join('')}
                </div>
            </div>
        `;
        
        this.chatMessages.appendChild(sampleDiv);
        this.scrollToBottom();
    }
    
    askSample(question) {
        this.messageInput.value = question;
        this.sendMessage();
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatBot = new ZUSChatBot();
});

// Add sample questions styling
const style = document.createElement('style');
style.textContent = `
    .sample-questions {
        display: flex;
        flex-direction: column;
        gap: 8px;
        margin-top: 12px;
    }
    
    .sample-question {
        background: rgba(139, 69, 19, 0.1);
        border: 1px solid rgba(139, 69, 19, 0.2);
        border-radius: 8px;
        padding: 8px 12px;
        text-align: left;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 14px;
        color: #8B4513;
    }
    
    .sample-question:hover {
        background: rgba(139, 69, 19, 0.2);
        transform: translateY(-1px);
    }
    
    code {
        background: rgba(0, 0, 0, 0.1);
        padding: 2px 4px;
        border-radius: 4px;
        font-family: 'Monaco', 'Menlo', monospace;
        font-size: 0.9em;
    }
`;
document.head.appendChild(style); 