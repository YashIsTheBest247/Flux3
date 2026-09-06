import { requestJson, videosBaseUrl } from './client.js';

export async function generateVideo(payload) {
    return requestJson(`${videosBaseUrl}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
}

export async function listVideos() {
    const response = await requestJson(`${videosBaseUrl}/list`);
    if (!Array.isArray(response)) {
        throw new Error('Video list response was not a valid array.');
    }
    return response;
}

export async function deleteVideo(name) {
    return requestJson(`${videosBaseUrl}/${encodeURIComponent(name)}`, {
        method: 'DELETE',
    });
}
