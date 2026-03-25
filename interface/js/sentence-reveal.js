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

        // Disable button
        buttonEl.disabled = true;

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

        // Mark first sentence as next
        wrapper.querySelector('[data-index="0"]').classList.add('next');
    }

    // Expose globally
    window.buildSentenceReveal = buildSentenceReveal;
})();
