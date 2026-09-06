import { apiBaseUrl, requestJson } from './client.js';

const trendsBaseUrl = `${apiBaseUrl}/api/v1/trends`;

// Fetch the ranked Economic Times trending articles (no generation).
export async function fetchTrending(topN = 9) {
    const response = await requestJson(`${trendsBaseUrl}/preview?top_n=${topN}`);
    return Array.isArray(response?.articles) ? response.articles : [];
}
