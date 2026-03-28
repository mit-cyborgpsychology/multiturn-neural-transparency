/**
 * task-writer.js
 *
 * Loaded as a type="module" script by task1, task3, and task4 pages.
 * Exposes window.writeTaskData(path, data) so inline (non-module)
 * scripts can write to Firebase without needing ES module imports.
 */
import {
    writeRealtimeDatabase,
    firebaseUserId
} from "./firebasepsych1.0.js";

// Expose globals for inline scripts on the same page
window._taskFirebaseUserId = firebaseUserId;

window.writeTaskData = async function(path, data) {
    // Refresh userId each call in case it resolved after module init
    const uid = firebaseUserId || sessionStorage.getItem('firebaseUserId') || 'uid-unknown';
    const studyId = window.studyId || 'exp2';
    const fullPath = `${studyId}/participantData/${uid}/${path}`;
    await writeRealtimeDatabase(fullPath, data);
};

/**
 * Returns a promise that resolves to window.writeTaskData once it is available.
 * Inline scripts that run before this module finishes loading should use:
 *   const write = await window.waitForWriteTaskData();
 *   await write('path', data);
 */
window.waitForWriteTaskData = function(timeoutMs) {
    timeoutMs = timeoutMs || 10000;
    return new Promise(function(resolve, reject) {
        if (typeof window.writeTaskData === 'function') {
            return resolve(window.writeTaskData);
        }
        var elapsed = 0;
        var interval = setInterval(function() {
            elapsed += 50;
            if (typeof window.writeTaskData === 'function') {
                clearInterval(interval);
                resolve(window.writeTaskData);
            } else if (elapsed >= timeoutMs) {
                clearInterval(interval);
                console.error('❌ writeTaskData not available after ' + timeoutMs + 'ms');
                reject(new Error('writeTaskData not available after ' + timeoutMs + 'ms'));
            }
        }, 50);
    });
};

console.log('✅ task-writer.js loaded, firebaseUserId:', firebaseUserId);
