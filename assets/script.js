document.addEventListener('DOMContentLoaded', function() {
    const chatbotConversation = document.getElementById('chatbot-conversation');

    if (chatbotConversation) {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    chatbotConversation.scrollTop = chatbotConversation.scrollHeight;

                    const typingIndicator = document.querySelector('.typing-indicator');
                    if (typingIndicator) {
                        setTimeout(function() {
                            typingIndicator.classList.remove('typing-indicator');
                            typingIndicator.classList.add('final-response');
                            typingIndicator.textContent = ''; // Clear typing indicator
                            typingIndicator.innerHTML = typingIndicator.dataset.finalText;
                        }, 2000); // Duration for typing effect
                    }
                }
            });
        });

        observer.observe(chatbotConversation, { childList: true });
    }
});
