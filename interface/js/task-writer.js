/**
 * task-writer.js
 *
 * Loaded as a type="module" script in index.html.
 * Exposes window.writeTaskData(path, data) so inline (non-module)
 * scripts loaded via $.load() can write to Firebase.
 */
console.log('⏳ task-writer.js: starting import of firebasepsych1.0...');

import {
    writeRealtimeDatabase,
    firebaseUserId
} from "./firebasepsych1.0.js";

console.log('⏳ task-writer.js: import complete, firebaseUserId:', firebaseUserId);

window.writeTaskData = async function(path, data) {
    const uid = firebaseUserId || sessionStorage.getItem('firebaseUserId') || 'uid-unknown';
    const studyId = window.studyId || 'exp2';
    const fullPath = `${studyId}/participantData/${uid}/${path}`;
    console.log('📝 writeTaskData:', fullPath);
    await writeRealtimeDatabase(fullPath, data);
};

console.log('✅ task-writer.js: window.writeTaskData is now available');
