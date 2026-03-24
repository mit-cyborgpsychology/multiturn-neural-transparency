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

console.log('✅ task-writer.js loaded, firebaseUserId:', firebaseUserId);
