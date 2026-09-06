import { apiBaseUrl, requestJson } from './client.js';

const base = `${apiBaseUrl}/api/v1/connect`;

/** Field definitions plus what is configured. Never returns secret values. */
export function getCredentials() {
    return requestJson(`${base}/credentials`);
}

/**
 * Save only the fields the creator actually edited.
 *
 * Sending the whole form back would write the masked placeholders over the
 * real secrets, so the caller is expected to pass a sparse object.
 */
export function saveCredentials(updates) {
    return requestJson(`${base}/credentials`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
    });
}

export function getYouTubeStatus() {
    return requestJson(`${base}/youtube`);
}

/** Publishing target, OAuth client fields and readiness, in one call. */
export function getPublishing() {
    return requestJson(`${base}/publishing`);
}

/** Switch between the deployment's default channel and the visitor's own. */
export function setPublishMode(mode) {
    return requestJson(`${base}/publishing`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode }),
    });
}

export function startYouTubeAuth() {
    return requestJson(`${base}/youtube/start`, { method: 'POST' });
}

export function disconnectYouTube() {
    return requestJson(`${base}/youtube/disconnect`, { method: 'POST' });
}

/**
 * Open Google's consent screen in a popup and resolve when it reports back.
 *
 * Resolves on the postMessage from the callback page, and also polls for the
 * window closing: a popup blocker, or someone closing the tab manually, would
 * otherwise leave this pending forever.
 */
export function openYouTubeConsent(authorizeUrl) {
    return new Promise((resolve) => {
        const popup = window.open(authorizeUrl, 'flux-youtube-oauth', 'width=560,height=680');

        if (!popup) {
            // Popup blocked. Falling back to a full navigation is better than
            // failing: the callback page renders a link back to the app.
            window.location.href = authorizeUrl;
            resolve({ ok: false, blocked: true });
            return;
        }

        function cleanup(result) {
            window.removeEventListener('message', onMessage);
            window.clearInterval(timer);
            resolve(result);
        }

        function onMessage(event) {
            if (event.data?.source === 'flux-youtube-oauth') {
                cleanup({ ok: Boolean(event.data.ok) });
            }
        }

        window.addEventListener('message', onMessage);
        const timer = window.setInterval(() => {
            if (popup.closed) cleanup({ ok: null, closed: true });
        }, 600);
    });
}
