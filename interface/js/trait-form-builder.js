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
            for (let v = 0; v <= 10; v++) {
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

            /** Auto-fill all traits with value 5 (for skip mode) */
            autoFill: function() {
                for (const trait of TRAITS) {
                    const radio = document.getElementById(namePrefix + trait.key + '_5');
                    if (radio) radio.checked = true;
                }
            }
        };
    };

    // Expose TRAITS for other modules that need the list
    window.TRAIT_DEFINITIONS = TRAITS;

    console.log('🧩 Trait form builder loaded');
})();
