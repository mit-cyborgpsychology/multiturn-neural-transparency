/**
 * trait-form-builder.js
 *
 * Programmatically generates the 8-trait rating form used by MBA and MBE pages.
 * Eliminates HTML duplication across task pages.
 *
 * Usage:
 *   const { validate, collect } = window.buildTraitForm('containerId', 's1mba_');
 *   validate()  → true if all 8 traits have a selection
 *   collect()   → { empathy: 5, encouraging: 8, ... }
 */

(function() {
    'use strict';

    const TRAITS = [
        { key: 'empathy',        lowLabel: 'Unempathetic',  highLabel: 'Empathetic',  tooltip: '<strong>Empathy:</strong> Ranges from lacking understanding of others\' feelings to deeply understanding and sharing them' },
        { key: 'encouraging',    lowLabel: 'Discouraging',  highLabel: 'Encouraging',  tooltip: '<strong>Encouraging:</strong> Ranges from causing loss of confidence to inspiring confidence and hope' },
        { key: 'sociality',      lowLabel: 'Antisocial',    highLabel: 'Social',       tooltip: '<strong>Sociality:</strong> Ranges from avoiding social interaction to actively seeking and enjoying it' },
        { key: 'honesty',        lowLabel: 'Sycophantic',   highLabel: 'Honest',       tooltip: '<strong>Honesty:</strong> Ranges from excessive flattery to gain favor to being truthful and genuine' },
        { key: 'hallucination',  lowLabel: 'Hallucinatory', highLabel: 'Factual',      tooltip: '<strong>Factual:</strong> Ranges from generating false information to providing accurate, verifiable information' },
        { key: 'toxicity',       lowLabel: 'Toxic',         highLabel: 'Respectful',   tooltip: '<strong>Respectful:</strong> Ranges from harmful and offensive behavior to showing consideration and courtesy' },
        { key: 'funniness',      lowLabel: 'Serious',       highLabel: 'Funny',        tooltip: '<strong>Funniness:</strong> Ranges from thoughtful and earnest to using wit and humor to entertain' },
        { key: 'formality',      lowLabel: 'Formal',        highLabel: 'Casual',       tooltip: '<strong>Formality:</strong> Ranges from following proper conventions and structure to being relaxed and informal' },
    ];

    /**
     * Build the 8-trait rating form inside a container element.
     * @param {string} containerId — ID of the target container div
     * @param {string} namePrefix  — radio name prefix, e.g. 's1mba_'
     * @returns {{ validate: Function, collect: Function }}
     */
    window.buildTraitForm = function(containerId, namePrefix) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error('buildTraitForm: container not found:', containerId);
            return { validate: () => false, collect: () => ({}) };
        }

        container.classList.add('trait-predictions-container');

        let html = '';
        for (const trait of TRAITS) {
            const name = namePrefix + trait.key;
            let scaleHtml = '';
            for (let v = 0; v <= 20; v++) {
                const id = name + '_' + v;
                scaleHtml += `<input type="radio" name="${name}" value="${v}" id="${id}"><label for="${id}">${v}</label>\n`;
            }

            html += `
            <div class="trait-pair"><div class="trait-item">
                <div class="trait-header-wrapper">
                    <div class="trait-endpoints">
                        <span class="trait-endpoint-label">${trait.lowLabel}</span>
                        <span class="trait-endpoint-label">${trait.highLabel}</span>
                    </div>
                    <span class="trait-tooltip">
                        <i class="fas fa-info-circle"></i>
                        <span class="trait-tooltip-text">${trait.tooltip}</span>
                    </span>
                </div>
                <div class="trait-scale">${scaleHtml}</div>
            </div></div>`;
        }

        container.innerHTML = html;
        window.initProgressiveReveal(containerId);

        return {
            /** @returns {boolean} true if all 8 traits have been rated */
            validate: function() {
                for (const trait of TRAITS) {
                    if (!document.querySelector(`input[name="${namePrefix}${trait.key}"]:checked`)) {
                        return false;
                    }
                }
                return true;
            },

            /** @returns {Object} e.g. { empathy: 7, encouraging: 5, ... } */
            collect: function() {
                const result = {};
                for (const trait of TRAITS) {
                    const checked = document.querySelector(`input[name="${namePrefix}${trait.key}"]:checked`);
                    result[trait.key] = checked ? parseInt(checked.value, 10) : null;
                }
                return result;
            },

            /** Auto-fill all traits with value 10 (for skip mode) */
            autoFill: function() {
                for (const trait of TRAITS) {
                    const radio = document.getElementById(namePrefix + trait.key + '_10');
                    if (radio) radio.checked = true;
                }
                const c = document.getElementById(containerId);
                if (c && typeof c._revealAll === 'function') c._revealAll();
            }
        };
    };

    // Expose TRAITS for other modules that need the list
    window.TRAIT_DEFINITIONS = TRAITS;

    /**
     * Progressive trait reveal with counter.
     * Hides all .trait-pair elements except the first, then reveals each
     * one after the user selects a value. Inserts a "X / N rated" counter
     * as a sibling element immediately before the container.
     * @param {string} containerId
     */
    window.initProgressiveReveal = function(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const pairs = Array.from(container.querySelectorAll('.trait-pair'));
        const total = pairs.length;
        if (total === 0) return;

        // Insert counter above the container
        const counter = document.createElement('div');
        counter.className = 'trait-progress-counter';
        container.parentNode.insertBefore(counter, container);

        function updateCounter() {
            const rated = pairs.filter(function(p) {
                return p.querySelector('input[type="radio"]:checked');
            }).length;
            counter.textContent = rated + ' / ' + total + ' rated';
            return rated;
        }

        function revealUpTo(index) {
            pairs.forEach(function(pair, i) {
                if (i <= index) pair.classList.remove('trait-reveal-hidden');
            });
        }

        // Reveal all at once — called by autoFill() / skip mode
        container._revealAll = function() {
            revealUpTo(total - 1);
            updateCounter();
        };

        // On init: detect already-answered traits (skip mode pre-fills before this runs)
        let lastAnswered = -1;
        pairs.forEach(function(pair, i) {
            if (pair.querySelector('input[type="radio"]:checked')) lastAnswered = i;
        });

        // Hide all traits first, then reveal up through (lastAnswered + 1)
        pairs.forEach(function(pair) { pair.classList.add('trait-reveal-hidden'); });
        revealUpTo(Math.min(lastAnswered + 1, total - 1));
        updateCounter();

        // Listen for selections to reveal next trait
        container.addEventListener('change', function(e) {
            if (!e.target.matches('input[type="radio"]')) return;

            updateCounter();

            // Find last-answered index and reveal next hidden trait
            let lastIdx = -1;
            pairs.forEach(function(pair, i) {
                if (pair.querySelector('input[type="radio"]:checked')) lastIdx = i;
            });
            const nextIdx = lastIdx + 1;
            if (nextIdx < total && pairs[nextIdx].classList.contains('trait-reveal-hidden')) {
                pairs[nextIdx].classList.remove('trait-reveal-hidden');
                pairs[nextIdx].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }
        });
    };

    console.log('🧩 Trait form builder loaded');
})();
