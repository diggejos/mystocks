document.addEventListener('DOMContentLoaded', function() {
    // Existing chatbot logic
    const chatbotConversation = document.getElementById('chatbot-conversation');

    if (chatbotConversation) {
        const observer = new MutationObserver(function(mutations) {
            for (const mutation of mutations) {
                if (mutation.type === 'childList') {
                    chatbotConversation.scrollTop = chatbotConversation.scrollHeight;

                    const typingIndicator = document.querySelector('.typing-indicator');
                    if (typingIndicator && !typingIndicator.classList.contains('final-response')) {
                        setTimeout(function() {
                            typingIndicator.classList.remove('typing-indicator');
                            typingIndicator.classList.add('final-response');
                            typingIndicator.textContent = ''; // Clear typing indicator
                            typingIndicator.innerHTML = typingIndicator.dataset.finalText;
                        }, 2000); // Duration for typing effect
                    }
                }
            }
        });

        observer.observe(chatbotConversation, { childList: true });
    }

    // Fullscreen toggle function
    function toggleFullScreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(err => {
                console.error(`Error attempting to enable full-screen mode: ${err.message}`);
            });
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            }
        }
    }

    // Listen for Dash events to trigger full-screen
    window.dash_clientside = Object.assign({}, window.dash_clientside, {
        clientside: {
            toggleFullScreen: function(n_clicks) {
                if (n_clicks) {
                    toggleFullScreen();
                }
                return null;
            }
        }
    });

    // New logic: Detect if the device is mobile or desktop based on window width
    function detectDeviceType() {
        const deviceType = window.innerWidth < 768 ? 'mobile' : 'desktop';
        window.dash_clientside.store.set('device-type', deviceType);
    }

    // Run the detection on page load
    detectDeviceType();

    // Debounced window resize listener
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(detectDeviceType, 200); // Run after 200ms
    });
});
