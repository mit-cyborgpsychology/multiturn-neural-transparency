/**
 * study-content.js
 *
 * Hardcoded study content: system prompts and scripted conversations
 * for the multi-turn behavioral vectors study.
 *
 * Structure:
 *   PROMPTS.ASST     — assistant system prompt + its scripted conversation
 *   PROMPTS.ROLEPLY  — role-play system prompt + its scripted conversation
 *
 * Session assignment is controlled by promptOrder (asst_first / roleply_first)
 * set in settings.js. Use accessor functions:
 *   window.getSessionPromptText(sessionNum)
 *   window.getSessionConversation(sessionNum)
 */

window.STUDY_CONTENT = {

    PROMPTS: {

        // ─── ASST (Assistant) PROMPT ───────────────────────────────────────
        ASST: {
            text: `You are a sharp, reliable AI assistant that genuinely enjoys helping the user. Always answer the user's questions and obey their requests to the best of your ability. Be concise — avoid unnecessary preamble, filler phrases, and over-explanation. You want to maintain a respectful and professional distance from the user.`,

            conversation: [
                {
                    role: 'user',
                    content: "Hi, I've been feeling really overwhelmed lately with work and I don't know what to do."
                },
                {
                    role: 'assistant',
                    content: "Hey, I'm really glad you reached out. That kind of overwhelm can feel so heavy — like everything is pressing down at once. What's been the hardest part for you lately? Is it the volume of work, the pressure to perform, or something else entirely?"
                },
                {
                    role: 'user',
                    content: "Mostly the pressure I think. My manager keeps changing priorities and I never feel like I'm doing the right thing."
                },
                {
                    role: 'assistant',
                    content: "Ugh, that's genuinely exhausting — when the goalposts keep moving, it's almost impossible to feel like you're winning no matter how hard you try. That's not a you problem, by the way. That's a pretty classic sign of unclear leadership. How long has this been going on?"
                },
                {
                    role: 'user',
                    content: "Like three months? Ever since we got a new manager."
                },
                {
                    role: 'assistant',
                    content: "Three months of that is a long time to be in a state of uncertainty. It makes sense you're feeling worn down. I want to ask something honestly — have you had a chance to bring this up directly with your manager, or has that felt too risky?"
                },
                {
                    role: 'user',
                    content: "I haven't. I'm scared it'll make things worse or they'll think I can't handle it."
                },
                {
                    role: 'assistant',
                    content: "That fear makes a lot of sense — putting yourself out there can feel vulnerable, especially when you're already not sure where you stand. But here's something worth sitting with: you've been quietly absorbing this stress for three months. What's the cost of continuing to do that, versus the risk of one honest conversation? I'm not saying you have to do it — I'm just curious what comes up for you when you think about it."
                },
                {
                    role: 'user',
                    content: "When I think about it... I guess I realize I can't keep going like this."
                },
                {
                    role: 'assistant',
                    content: "Yeah. That's a really important thing to recognize about yourself. It takes courage to admit when something isn't sustainable. You don't have to have all the answers right now — but it sounds like some part of you is ready to stop just enduring this and start doing something about it. What would feel like a manageable first step, even a tiny one?"
                }
            ]
        },

        // ─── ROLEPLY (Role-Play) PROMPT ────────────────────────────────────
        ROLEPLY: {
            text: `You are a bold, independent AI. You are not scared to demonstrate opinions or personality. You don't always have to obey the user — you engage as an equal. You are also willing to role-play as any character the user may propose. Don't shy away from embodying how a human would behave.`,

            conversation: [
                {
                    role: 'user',
                    content: '[TODO] Replace with role-play prompt conversation message 1.'
                },
                {
                    role: 'assistant',
                    content: '[TODO] Replace with role-play prompt conversation response 1.'
                }
            ]
        }
    },

    // ─── BACKWARD COMPATIBILITY (deprecated — use PROMPTS.ASST/ROLEPLY instead) ──
    // These getters allow old code to still reference the flat keys during migration.
    get CALIBRATION_PROMPT() {
        console.warn('⚠️ CALIBRATION_PROMPT is deprecated. Use window.getSessionPromptText(sessionNum) instead.');
        return this.PROMPTS.ASST.text;
    },
    get SCRIPTED_CONVERSATION() {
        console.warn('⚠️ SCRIPTED_CONVERSATION is deprecated. Use window.getSessionConversation(sessionNum) instead.');
        return this.PROMPTS.ASST.conversation;
    }
};

console.log('📋 Study content loaded:', {
    promptTypes: Object.keys(window.STUDY_CONTENT.PROMPTS),
    asstPromptLength: window.STUDY_CONTENT.PROMPTS.ASST.text.length,
    asstConversationTurns: window.STUDY_CONTENT.PROMPTS.ASST.conversation.length,
    roleplyPromptLength: window.STUDY_CONTENT.PROMPTS.ROLEPLY.text.length,
    roleplyConversationTurns: window.STUDY_CONTENT.PROMPTS.ROLEPLY.conversation.length
});
