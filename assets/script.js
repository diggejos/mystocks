document.addEventListener('DOMContentLoaded', function() {
    // Fullscreen toggle logic
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

    // Device detection logic
    function detectDeviceType() {
        const deviceType = window.innerWidth < 768 ? 'mobile' : 'desktop';
        window.dash_clientside.store.set('device-type', deviceType);
    }

    // Lazy load the fullscreen toggle and device detection functionality
    function lazyLoadInteractions() {
        // Attach fullscreen toggle function to Dash clientside events
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

        // Detect device type once on page load
        detectDeviceType();

        // Debounced resize listener for detecting device type on window resize
        let resizeTimeout;
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(detectDeviceType, 200);  // Debounce window resize event
        });
    }

    // Lazy load logic on first interaction using requestIdleCallback
    requestIdleCallback(function() {
        document.addEventListener('click', function onClick() {
            lazyLoadInteractions();  // Load fullscreen toggle and device detection logic
            document.removeEventListener('click', onClick);  // Unbind the event after lazy loading
        });
    });
});
