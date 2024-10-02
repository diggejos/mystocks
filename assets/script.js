document.addEventListener('DOMContentLoaded', function() {
    // Lazy load the fullscreen toggle functionality
    function lazyLoadFullScreen() {
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

        // Attach fullscreen toggle function to Dash events
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
    }

    // Lazy load fullscreen logic when user interacts with the page
    document.addEventListener('click', function onClick() {
        lazyLoadFullScreen(); // Load fullscreen toggle functionality
        document.removeEventListener('click', onClick); // Unbind event after lazy loading
    });

    // Lazy load device detection logic
    function lazyLoadDeviceDetection() {
        function detectDeviceType() {
            const deviceType = window.innerWidth < 768 ? 'mobile' : 'desktop';
            window.dash_clientside.store.set('device-type', deviceType);
        }

        // Run the detection once on page load
        detectDeviceType();

        // Debounced window resize listener
        let resizeTimeout;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(detectDeviceType, 200); // Run after 200ms
        });
    }

    // Lazy load device detection logic on first interaction with the page
    document.addEventListener('click', function onClick() {
        lazyLoadDeviceDetection();
        document.removeEventListener('click', onClick); // Unbind event after lazy loading
    });
});
