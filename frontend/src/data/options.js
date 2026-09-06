export const navLinks = [
    { id: 'top', label: 'Home' },
    { id: 'creator', label: 'Creator' },
    { id: 'pipeline', label: 'Pipeline' },
    { id: 'library', label: 'Library' },
];

export const formatOptions = [
    { value: 'video', label: 'Video', hint: 'Per-scene visuals + narration' },
    { value: 'podcast', label: 'Podcast', hint: 'One cover + long-form audio' },
];

export const privacyOptions = [
    { value: 'unlisted', label: 'Unlisted', hint: 'Anyone with the link' },
    { value: 'public', label: 'Public', hint: 'Listed & searchable' },
];

export const durationOptions = [
    { value: 15, label: '15s' },
    { value: 30, label: '30s' },
    { value: 60, label: '1m' },
    { value: 90, label: '1m 30s' },
    { value: 120, label: '2m' },
];

export const visibilityOptions = [
    { value: 'unlisted', label: 'Unlisted' },
    { value: 'public', label: 'Public' },
    { value: 'private', label: 'Private' },
];

export const pipelineSteps = [
    { key: 'script', label: 'Script', statusText: 'Writing the scene-by-scene script', durationMs: 4000 },
    { key: 'image', label: 'Image', statusText: 'Sourcing images (Pexels → Gemini)', durationMs: 7000 },
    { key: 'voice', label: 'Voice', statusText: 'Generating narration audio', durationMs: 6000 },
    { key: 'subtitles', label: 'Subtitles', statusText: 'Timing subtitles to audio', durationMs: 5000 },
    { key: 'assembly', label: 'Assembly', statusText: 'Assembling the final cut', durationMs: 5000 },
    { key: 'publish', label: 'Publish', statusText: 'Publishing to YouTube', durationMs: 0 },
];

// Floating capability labels around the hero — what Flux actually does.
export const heroNodes = [
    { label: 'Scripts', code: 'Gemini', icon: 'Gemini', position: 'left-[6%] top-[24%]' },
    { label: 'Imagery', code: 'Pexels', icon: 'Pexels', position: 'right-[8%] top-[20%]' },
    { label: 'Voiceover', code: 'Kokoro', icon: 'KokoroTTS', position: 'left-[9%] bottom-[26%]' },
    { label: 'Subtitles', code: 'Auto-synced', icon: 'Subtitles', position: 'right-[7%] bottom-[28%]' },
];

export const brandLogos = ['YouTube', 'KokoroTTS', 'Render', 'Vercel', 'Pexels', 'Gemini', 'Pillow'];
