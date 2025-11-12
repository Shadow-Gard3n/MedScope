document.addEventListener('DOMContentLoaded', () => {
    const chatWindow = document.getElementById('chat-window');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');

    function appendMessage(text, sender) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');
        // msgDiv.textContent = text;

        if (sender === 'bot') {
            // Renders HTML tags like <b> and <ul>
            msgDiv.innerHTML = text;
        } else {
            // Keeps user input safe as plain text
            msgDiv.textContent = text;
        }
        chatWindow.appendChild(msgDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight; // Auto-scroll to bottom
    }

    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.classList.add('typing-indicator');
        typingDiv.textContent = 'MediAware is typing...';
        chatWindow.appendChild(typingDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function removeTypingIndicator() {
        const typingDiv = document.getElementById('typing-indicator');
        if (typingDiv) {
            typingDiv.remove();
        }
    }

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = userInput.value.trim();
        if (!message) return;

        // 1. Show user message
        appendMessage(message, 'user');
        userInput.value = '';

        // 2. Show typing indicator
        showTypingIndicator();

        try {
            // 3. Send to backend
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message })
            });

            // 4. Remove typing indicator
            removeTypingIndicator();

            if (response.ok) {
                const data = await response.json();
                appendMessage(data.response['answer'], 'bot');
            } else {
                appendMessage("Sorry, I'm having trouble connecting right now. Please try again.", 'bot');
            }
        } catch (error) {
            console.error("Chat error:", error);
            removeTypingIndicator();
            appendMessage("Network error. Please check your connection.", 'bot');
        }
    });
});