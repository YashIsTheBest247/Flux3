// Order must match the order the sections actually appear in App.jsx,
// otherwise the nav jumps backwards up the page.
export const navLinks = [
    { id: 'top', label: 'Home' },
    { id: 'channel', label: 'Channel' },
    { id: 'publishing', label: 'Publishing' },
    { id: 'automation', label: 'Automate' },
    { id: 'upload', label: 'Upload' },
    { id: 'library', label: 'Library' },
];

export const pipelineSteps = [
    { key: 'fetch', label: 'Find', statusText: 'Scanning your channel’s trend sources', durationMs: 3000 },
    { key: 'trend', label: 'Rank', statusText: 'Scoring stories by recency and momentum', durationMs: 3000 },
    { key: 'script', label: 'Script', statusText: 'Writing the script in your channel’s voice', durationMs: 4000 },
    { key: 'image', label: 'Visuals', statusText: 'Sourcing footage and photography', durationMs: 7000 },
    { key: 'voice', label: 'Narration', statusText: 'Generating narration audio', durationMs: 6000 },
    { key: 'subtitles', label: 'Captions', statusText: 'Timing captions to the audio', durationMs: 5000 },
    { key: 'assembly', label: 'Assembly', statusText: 'Assembling the final cut', durationMs: 5000 },
    { key: 'provenance', label: 'Provenance', statusText: 'Signing the Genblaze manifest', durationMs: 2000 },
    { key: 'storage', label: 'Backblaze B2', statusText: 'Uploading artefacts to Backblaze B2', durationMs: 3000 },
    { key: 'publish', label: 'Publish', statusText: 'Publishing to YouTube', durationMs: 0 },
];
