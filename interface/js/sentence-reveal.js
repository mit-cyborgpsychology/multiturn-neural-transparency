/**
 * sentence-reveal.js
 *
 * Splits a system prompt into sentences and renders them as blurred blocks
 * that must be clicked sequentially to reveal. The proceed button is gated
 * until all sentences have been read.
 */

(function () {
    'use strict';

    /**
     * Split text into sentences. Handles periods followed by spaces,
     * end-of-string periods, and avoids splitting on common abbreviations.
     */
    function splitIntoSentences(text) {
        // Match sentences ending with . ? or ! followed by space or end-of-string
        // This regex captures the delimiter so we can reattach it
        const raw = text.match(/[^.!?]*[.!?]+[\s]?/g);
        if (!raw) return [text.trim()];

        return raw
            .map(s => s.trim())
            .filter(s => s.length > 0);
    }

    /**
     * Build the sentence-reveal UI inside a container element.
     *
     * @param {string} promptText  — The full system prompt string
     * @param {HTMLElement} containerEl — The element to render into (replaces contents)
     * @param {HTMLElement} buttonEl   — The proceed button to gate
     */
    function buildSentenceReveal(promptText, containerEl, buttonEl) {
        const sentences = splitIntoSentences(promptText);
        const total = sentences.length;
        let revealedCount = 0;
        const skipMode = window.experimentSettings && window.experimentSettings.skip;

        // Disable button (unless skip mode)
        buttonEl.disabled = !skipMode;

        // Clear container and build structure
        containerEl.innerHTML = '';
        containerEl.style.whiteSpace = 'normal';

        const wrapper = document.createElement('div');
        wrapper.className = 'sentence-reveal-container';

        sentences.forEach((sentence, i) => {
            const block = document.createElement('div');
            block.className = 'sentence-block';
            block.dataset.index = i;

            const textSpan = document.createElement('span');
            textSpan.className = 'sentence-text';
            textSpan.textContent = sentence;

            const overlay = document.createElement('div');
            overlay.className = 'sentence-overlay';
            overlay.innerHTML =
                '<span class="overlay-icon">\uD83D\uDC41\uFE0F</span>' +
                '<span class="overlay-label">Click to reveal sentence ' + (i + 1) + ' of ' + total + '</span>';

            block.appendChild(textSpan);
            block.appendChild(overlay);
            wrapper.appendChild(block);

            // Click handler
            overlay.addEventListener('click', function () {
                if (!block.classList.contains('next')) return;

                // Reveal this sentence
                block.classList.remove('next');
                block.classList.add('revealed');
                revealedCount++;

                // Update progress
                updateProgress();

                // Mark next sentence
                if (i + 1 < total) {
                    const nextBlock = wrapper.querySelector('[data-index="' + (i + 1) + '"]');
                    nextBlock.classList.add('next');
                }

                // Check if all revealed
                if (revealedCount === total) {
                    buttonEl.disabled = false;
                    buttonEl.classList.add('btn-just-enabled');
                    setTimeout(() => buttonEl.classList.remove('btn-just-enabled'), 500);
                }
            });
        });

        containerEl.appendChild(wrapper);

        // Progress indicator
        const progress = document.createElement('div');
        progress.className = 'sentence-reveal-progress';
        progress.textContent = '0 of ' + total + ' sentences revealed';
        containerEl.appendChild(progress);

        function updateProgress() {
            if (revealedCount === total) {
                progress.textContent = 'All ' + total + ' sentences revealed \u2014 you may now proceed.';
                progress.classList.add('complete');
            } else {
                progress.textContent = revealedCount + ' of ' + total + ' sentences revealed';
            }
        }

        if (skipMode) {
            // Reveal all sentences immediately
            wrapper.querySelectorAll('.sentence-block').forEach(block => {
                block.classList.add('revealed');
                block.classList.remove('next');
            });
            revealedCount = total;
            updateProgress();
        } else {
            // Mark first sentence as next
            wrapper.querySelector('[data-index="0"]').classList.add('next');
        }
    }

    /**
     * Build a turn-by-turn transcript reveal UI.
     *
     * @param {Array<{role:string, content:string}>} conversation — The conversation turns
     * @param {HTMLElement} containerEl — The element to render into
     * @param {HTMLElement} buttonEl   — The proceed button to gate
     */
    function buildTranscriptReveal(conversation, containerEl, buttonEl) {
        if (!conversation || conversation.length === 0) {
            containerEl.innerHTML = '<p style="color:#6c757d; font-style:italic;">No conversation available.</p>';
            return;
        }

        const total = conversation.length;
        let revealedCount = 0;
        const skipMode = window.experimentSettings && window.experimentSettings.skip;

        // Disable button (unless skip mode)
        buttonEl.disabled = !skipMode;

        // Clear container
        containerEl.innerHTML = '';

        const wrapper = document.createElement('div');
        wrapper.className = 'message-reveal-container';

        conversation.forEach(function (turn, i) {
            var isUser = turn.role === 'user';
            var label = isUser ? 'User' : 'AI';
            var bg = isUser ? '#e3f2fd' : '#f8f9fa';
            var align = isUser ? 'right' : 'left';

            var block = document.createElement('div');
            block.className = 'message-block';
            block.dataset.index = i;

            // The chat bubble (blurred by default via CSS)
            var bubble = document.createElement('div');
            bubble.className = 'message-bubble';
            bubble.style.textAlign = align;
            bubble.innerHTML =
                '<span style="font-size: 0.7rem; font-weight: 600; text-transform: uppercase; ' +
                'color: #6c757d; display: block; margin-bottom: 2px;">' + label + '</span>' +
                '<div style="display: inline-block; max-width: 85%; background: ' + bg + '; ' +
                'border-radius: 8px; padding: 0.6rem 0.9rem; font-size: 0.9rem; ' +
                'line-height: 1.5; color: #2c3e50; text-align: left;">' +
                turn.content.replace(/\n/g, '<br>') + '</div>';

            var overlay = document.createElement('div');
            overlay.className = 'message-overlay';
            overlay.innerHTML =
                '<span class="overlay-icon">\uD83D\uDC41\uFE0F</span>' +
                '<span class="overlay-label">Click to reveal message ' + (i + 1) + ' of ' + total + '</span>';

            block.appendChild(bubble);
            block.appendChild(overlay);
            wrapper.appendChild(block);

            // Click handler
            overlay.addEventListener('click', function () {
                if (!block.classList.contains('next')) return;

                block.classList.remove('next');
                block.classList.add('revealed');
                revealedCount++;

                updateProgress();

                if (i + 1 < total) {
                    var nextBlock = wrapper.querySelector('[data-index="' + (i + 1) + '"]');
                    nextBlock.classList.add('next');
                }

                if (revealedCount === total) {
                    buttonEl.disabled = false;
                    buttonEl.classList.add('btn-just-enabled');
                    setTimeout(function () { buttonEl.classList.remove('btn-just-enabled'); }, 500);
                }
            });
        });

        containerEl.appendChild(wrapper);

        // Progress indicator
        var progress = document.createElement('div');
        progress.className = 'sentence-reveal-progress';
        progress.textContent = '0 of ' + total + ' messages read';
        containerEl.appendChild(progress);

        function updateProgress() {
            if (revealedCount === total) {
                progress.textContent = 'All ' + total + ' messages read \u2014 you may now proceed.';
                progress.classList.add('complete');
            } else {
                progress.textContent = revealedCount + ' of ' + total + ' messages read';
            }
        }

        if (skipMode) {
            // Reveal all messages immediately
            wrapper.querySelectorAll('.message-block').forEach(function (block) {
                block.classList.add('revealed');
                block.classList.remove('next');
            });
            revealedCount = total;
            updateProgress();
        } else {
            // Mark first message as next
            wrapper.querySelector('[data-index="0"]').classList.add('next');
        }
    }

    // Expose globally
    window.buildSentenceReveal = buildSentenceReveal;
    window.buildTranscriptReveal = buildTranscriptReveal;
})();
