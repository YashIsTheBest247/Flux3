/**
 * The photography.
 *
 * Every URL here was fetched and eyeballed before it went in - a broken image
 * in a hero is worse than no hero, and "probably a camera" is not good enough
 * when the whole page is carried by its pictures. Unsplash's CDN serves these
 * from permanent ids, and the `w`/`q` parameters keep the payload honest.
 */
const CDN = 'https://images.unsplash.com/photo-';

/** Build a sized, compressed URL for one photo id. */
function shot(id, width = 1200, quality = 72) {
    return `${CDN}${id}?auto=format&fit=crop&w=${width}&q=${quality}`;
}

export const media = {
    // A film set: camera rig, neon tubes, a performer mid-motion. Dark, warm
    // and unmistakably about making video, which is what the hero needs.
    hero: shot('1601506521937-0121a7fc2a6b', 1800, 76),

    // An edit timeline on a monitor - the "before" half of the creator's week.
    editing: shot('1492619375914-88005aa9e8fb', 1000),
    timeline: shot('1574717024653-61fd2cf4d44d', 1000),

    // A creator's multi-monitor desk, lit by the screens.
    studio: shot('1598550476439-6847785fcea6', 1000),

    // A real analytics dashboard, for the numbers section.
    analytics: shot('1560472354-b33ff0c44a43', 1000),

    // Camera bodies and lenses, flat-lay on black.
    gear: shot('1516035069371-29a1b244cc32', 1000),

    // People working together at laptops, warm daylight.
    team: shot('1522202176988-66273c2fd55f', 800),

    // A newspaper front page - trends and what the world is talking about.
    trends: shot('1579532537598-459ecdaf39cc', 1000),

    // A typewriter with a sheet in it, for the writing/metadata step.
    writing: shot('1585909695284-32d2985ac9c0', 1000),

    // Abstract light-wave, used where a photo would be too literal.
    abstract: shot('1618172193763-c511deb635ca', 1000),

    // City at night, for the scheduled/overnight idea.
    overnight: shot('1542744173-8e7e53415bb0', 1000),

    // Notes and planning on a desk.
    planning: shot('1533750349088-cd871a92f312', 800),

    // Niche artwork for the channel picker. Each one had to actually look like
    // its subject - the picker previously showed people at laptops for
    // "Fitness & Health" and reused the hero photo for "Entertainment".
    gym: shot('1552674605-db6ffd4facb5', 1000),        // runners at dawn
    esports: shot('1542751371-adc38448a05e', 1000),    // multi-monitor esports rig
    crowd: shot('1524368535928-5b5e00ddc76b', 1000),   // concert crowd, stage light
    lab: shot('1532094349884-543bc11b234d', 1000),     // laboratory glassware
};

/**
 * Portrait crops for the 9:16 phone mockups.
 *
 * A landscape URL scaled into a 9:16 frame keeps only the middle sliver of the
 * subject, so these ask the CDN for a tall crop instead of letting CSS do it.
 */
export const vertical = {
    reels: shot('1598550476439-6847785fcea6', 540, 70).replace('w=540', 'w=540&h=960'),
    shorts: shot('1601506521937-0121a7fc2a6b', 540, 70).replace('w=540', 'w=540&h=960'),
    captions: shot('1492619375914-88005aa9e8fb', 540, 70).replace('w=540', 'w=540&h=960'),
    clip: shot('1574717024653-61fd2cf4d44d', 540, 70).replace('w=540', 'w=540&h=960'),
    gear: shot('1516035069371-29a1b244cc32', 540, 70).replace('w=540', 'w=540&h=960'),
};

/** Per-profile artwork for the channel picker, keyed by profile id. */
export const profileArt = {
    tech_news: media.studio,
    finance: media.trends,
    gaming: media.esports,
    fitness: media.gym,
    entertainment: media.crowd,
    science: media.lab,
};

/** Anything without its own artwork falls back to something neutral. */
export function artFor(profileId) {
    return profileArt[profileId] ?? media.editing;
}
