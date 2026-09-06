import { apiBaseUrl, requestJson } from './client.js';

const base = `${apiBaseUrl}/api/v1/ingest`;

/**
 * Upload a finished video for packaging and (optionally) publishing.
 *
 * Uses XMLHttpRequest rather than fetch for one reason: fetch still cannot
 * report upload progress, and a creator sending a 300 MB file with no progress
 * bar assumes the app has hung.
 */
export function uploadVideo(file, options = {}, onProgress) {
    const form = new FormData();
    form.append('file', file);
    form.append('publish', options.publish ? 'true' : 'false');
    form.append('suggest_clips', options.suggestClips === false ? 'false' : 'true');
    if (options.privacy) form.append('privacy', options.privacy);
    if (options.title) form.append('title', options.title);

    return new Promise((resolve, reject) => {
        const request = new XMLHttpRequest();
        request.open('POST', base);

        request.upload.onprogress = (event) => {
            if (event.lengthComputable) {
                onProgress?.(Math.round((event.loaded / event.total) * 100));
            }
        };

        request.onload = () => {
            let payload;
            try {
                payload = JSON.parse(request.responseText);
            } catch {
                reject(new Error('The server returned an unreadable response.'));
                return;
            }
            if (request.status >= 200 && request.status < 300) resolve(payload);
            else reject(new Error(payload?.detail || payload?.error || 'Upload failed.'));
        };

        request.onerror = () => reject(new Error('Network error during upload.'));
        request.onabort = () => reject(new Error('Upload cancelled.'));
        request.send(form);
    });
}

export function getIngestJob(jobId) {
    return requestJson(`${base}/${encodeURIComponent(jobId)}`);
}

export function listIngestJobs() {
    return requestJson(base);
}
