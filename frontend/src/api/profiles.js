import { apiBaseUrl, requestJson } from './client.js';

const base = `${apiBaseUrl}/api/v1/profiles`;

export function listProfiles() {
    return requestJson(base);
}

export function activateProfile(profileId) {
    return requestJson(`${base}/${encodeURIComponent(profileId)}/activate`, { method: 'POST' });
}

export function saveProfile(profile) {
    return requestJson(base, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profile),
    });
}

export function deleteProfile(profileId) {
    return requestJson(`${base}/${encodeURIComponent(profileId)}`, { method: 'DELETE' });
}

/** Per-source counts for the active profile, so a dead source is visible. */
export function getSources() {
    return requestJson(`${apiBaseUrl}/api/v1/trends/sources`);
}
