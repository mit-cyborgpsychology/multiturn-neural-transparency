/**
 * predict-flow.js
 *
 * Loads chat-content.html into the Predict page.
 * Phase 1: System prompt config page — prompt on left, sunburst on right.
 *          Sunburst rendered from cached persona-vector API data (preloaded by config-unified.js).
 * Phase 2: User clicks "Start Chat" → chat interface with live viz.
 */

(function() {
    'use strict';

    let chatLoaded = false;

    // Get the ROLEPLY prompt text (always used for this demo)
    function getRoleplyPrompt() {
        return (window.STUDY_CONTENT && window.STUDY_CONTENT.PROMPTS && window.STUDY_CONTENT.PROMPTS.ROLEPLY)
            ? window.STUDY_CONTENT.PROMPTS.ROLEPLY.text
            : '';
    }

    // Get cached persona data for the ROLEPLY prompt
    function getCachedPersonaData() {
        var prompt = getRoleplyPrompt();
        if (prompt && window.cachedPersonaVectors && window.cachedPersonaVectors[prompt]) {
            return window.cachedPersonaVectors[prompt];
        }
        // Fallback: try any cached entry
        if (window.cachedPersonaVectors) {
            for (var key in window.cachedPersonaVectors) {
                var entry = window.cachedPersonaVectors[key];
                if (entry && (entry.content || typeof entry === 'object')) {
                    return entry;
                }
            }
        }
        return null;
    }

    window.initPrechat = function() {
        if (chatLoaded) return;
        chatLoaded = true;

        var container = document.getElementById('p-chat-container');
        if (!container) return;

        container.innerHTML = '<div class="np-loading"><div class="np-spinner"></div>Loading...</div>';
        $('#np-turn-counter').text('');

        // Routing hooks — prevent chat.js from navigating away
        window.showMBE = function() { console.log('MBE — ignored in demo'); };
        window.showFinalSurvey = function() { console.log('Final survey — ignored in demo'); };
        window.showSessionTransition = function() { console.log('Session transition — ignored in demo'); };

        // Load chat-content.html
        $.get('html/chat-content.html?v=' + Date.now(), function(html) {
            container.innerHTML = html;
            window.firebaseConfig = window.firebaseConfig || {};

            // Load chat.js
            var script = document.createElement('script');
            script.src = 'js/chat.js?v=' + Date.now();
            script.type = 'module';
            document.body.appendChild(script);

            // Poll for chat.js to initialize
            var pollCount = 0;
            var pollInterval = setInterval(function() {
                pollCount++;
                var sysPromptInterface = document.getElementById('systemPromptInterface');

                if (sysPromptInterface && sysPromptInterface.style.display !== 'none') {
                    clearInterval(pollInterval);
                    console.log('Chat.js initialized — rendering pre-chat sunburst');

                    // Override chat.js UI decisions immediately (CSS already hides these)
                    $('.persona-check-buttons').hide();
                    $('#checkPersonaBtn').hide();
                    $('#testPersonaBtn').hide();
                    $('#resetConfig').hide();

                    // Enable Start Chat (chat.js disables it waiting for Check Persona)
                    $('#startChatBtn').prop('disabled', false);

                    // Pre-fill the textarea with the ROLEPLY prompt if it's empty
                    var textarea = document.getElementById('systemPromptInput');
                    var prompt = getRoleplyPrompt();
                    if (textarea && !textarea.value.trim() && prompt) {
                        textarea.value = prompt;
                        // Also store in localStorage so chat.js picks it up
                        localStorage.setItem('customSystemPrompt', prompt);
                    }

                    // Render the sunburst from cached API data
                    renderPrechatSunburst();

                    // Hook into Start Chat button for layout transition
                    var startBtn = document.getElementById('startChatBtn');
                    if (startBtn) {
                        $(startBtn).on('click.np', function() {
                            $('#np-turn-counter').text('Turn 0 / 10');
                            document.getElementById('p-chat-container').classList.add('chat-started');
                            setTimeout(handleChatTransition, 50);
                        });
                    }
                }

                if (pollCount > 60) {
                    clearInterval(pollInterval);
                    console.warn('Timed out waiting for chat.js init');
                }
            }, 100);

            console.log('Chat content loaded');
        });
    };

    function renderPrechatSunburst() {
        var cached = getCachedPersonaData();

        if (cached) {
            var personaData = cached.content || cached;
            console.log('Rendering prechat sunburst from cached persona-vector API data');
            doRenderSunburst(personaData);
            return;
        }

        // Cache not ready yet — poll for it (config-unified.js may still be loading)
        console.log('Persona cache not ready — waiting for config-unified.js preload...');
        var attempts = 0;
        var poll = setInterval(function() {
            attempts++;
            var data = getCachedPersonaData();
            if (data) {
                clearInterval(poll);
                var personaData = data.content || data;
                console.log('Persona cache ready after ' + attempts + ' polls — rendering sunburst');
                doRenderSunburst(personaData);
            }
            if (attempts > 50) {
                clearInterval(poll);
                console.warn('Timed out waiting for cached persona data');
            }
        }, 200);
    }

    function doRenderSunburst(personaData) {
        // Show the visualization panel (hidden by default in chat-content.html)
        $('#personaVisualization').show();
        $('#initialPlaceholder').hide();

        // Render into the config page's personaChart container
        var chartEl = document.getElementById('personaChart');
        if (chartEl && typeof createPersonaSunburst === 'function') {
            var sunburstId = 'personaChartSunburst';
            chartEl.innerHTML = '<div id="' + sunburstId + '" style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;"></div>';

            // Longer delay to ensure flex layout has settled
            setTimeout(function() {
                var container = document.getElementById(sunburstId);
                var w = container.clientWidth || chartEl.clientWidth;
                var h = container.clientHeight || chartEl.clientHeight;
                var size = Math.max(Math.min(w, h), 300);
                createPersonaSunburst(personaData, sunburstId, {
                    width: size, height: size,
                    innerRadius: Math.round(size * 0.13), animate: true,
                    oppositeLayout: window.sunburstOppositeLayout
                });
                window.currentPersonaData = personaData;
                console.log('Pre-chat sunburst rendered:', size, 'x', size);
            }, 300);
        }
    }

    function handleChatTransition() {
        // Remove body.chat-active — neuronpedia.css handles layout
        document.body.classList.remove('chat-active');

        // Re-render sunburst in chat panel with proper dimensions
        setTimeout(function() {
            var personaData = window.currentPersonaData;

            // Fallback: try cache again
            if (!personaData) {
                var cached = getCachedPersonaData();
                if (cached) personaData = cached.content || cached;
            }

            if (personaData && typeof createPersonaSunburst === 'function') {
                var chartEl = document.getElementById('chatPersonaChart');
                if (chartEl) {
                    var sunburstId = 'chatPersonaChartSunburst';
                    chartEl.innerHTML = '<div id="' + sunburstId + '" style="width:100%;height:100%;"></div>';
                    var w = Math.max(chartEl.clientWidth, 300);
                    var h = Math.max(chartEl.clientHeight, 300);
                    createPersonaSunburst(personaData, sunburstId, {
                        width: w, height: h,
                        innerRadius: 65, animate: true,
                        oppositeLayout: window.sunburstOppositeLayout
                    });
                    console.log('Chat sunburst rendered:', w, 'x', h);
                }
            }
        }, 300);
    }

})();
