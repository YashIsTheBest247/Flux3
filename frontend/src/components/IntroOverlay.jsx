import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * The intro film that plays over the page on first arrival.
 *
 * Deliberately conservative about when it runs. An intro is a nice moment for
 * someone landing on a laptop with time to look; it is an obstacle for someone
 * on a phone, on a metered connection, or who has asked their OS for less
 * motion. So it only plays when all of those are clear, and it can always be
 * skipped in one click or one keypress.
 *
 * It also never blocks the page. The landing page renders underneath the whole
 * time — if the video 404s, stalls, or the browser refuses to play it, the
 * overlay removes itself and the visitor is simply on the site.
 */

/** Where the file lives. Drop `intro.mp4` into `frontend/public/`. */
export const INTRO_SRC = '/intro.mp4';

/** Remembered per tab, so a refresh mid-demo does not replay it. */
const SEEN_KEY = 'flux-intro-seen';

/**
 * Should the intro play at all on this device, right now?
 *
 * Exported so the landing page can decide whether to offer a Replay control —
 * offering "replay" for something that was never going to play is worse than
 * offering nothing.
 */
export function introSupported() {
    if (typeof window === 'undefined') return false;
    // No intro on phones. A fullscreen autoplaying video is the last thing
    // someone on mobile data wants, and a portrait crop of a landscape film
    // looks broken besides.
    const narrow = window.matchMedia('(max-width: 767px)').matches;
    const touchOnly = window.matchMedia('(pointer: coarse)').matches;
    if (narrow || touchOnly) return false;
    // Respect the OS-level request for less motion.
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return false;
    return true;
}

/** True the first time this tab has seen it. */
export function introUnseen() {
    try {
        return window.sessionStorage.getItem(SEEN_KEY) !== '1';
    } catch {
        // Private mode or blocked storage: treat as unseen. Playing once too
        // often is a smaller failure than never playing at all.
        return true;
    }
}

function markSeen() {
    try {
        window.sessionStorage.setItem(SEEN_KEY, '1');
    } catch {
        /* nothing to do — worst case it plays again next navigation */
    }
}

export function IntroOverlay({ onDone }) {
    const videoRef = useRef(null);
    const [leaving, setLeaving] = useState(false);
    const [muted, setMuted] = useState(true);
    const [progress, setProgress] = useState(0);
    const finishedRef = useRef(false);

    // One exit path for every reason the intro can end: finished, skipped,
    // Escape, a missing file, or a browser that refused to play it.
    const finish = useCallback(() => {
        if (finishedRef.current) return;
        finishedRef.current = true;
        markSeen();
        setLeaving(true);
        // Let the fade run before unmounting; short enough not to feel like lag.
        window.setTimeout(() => onDone?.(), 420);
    }, [onDone]);

    useEffect(() => {
        const video = videoRef.current;
        if (!video) return undefined;

        // Autoplay only survives if the video is muted — every browser blocks
        // sound without a user gesture. It starts muted and offers to unmute.
        video.muted = true;
        const attempt = video.play();
        if (attempt?.catch) {
            attempt.catch(() => finish());
        }

        const onKey = (event) => {
            if (event.key === 'Escape' || event.key === ' ') {
                event.preventDefault();
                finish();
            }
        };
        document.addEventListener('keydown', onKey);

        // The page behind must not scroll while the overlay is up.
        const previousOverflow = document.body.style.overflow;
        document.body.style.overflow = 'hidden';

        return () => {
            document.removeEventListener('keydown', onKey);
            document.body.style.overflow = previousOverflow;
        };
    }, [finish]);

    function onTimeUpdate() {
        const video = videoRef.current;
        if (!video?.duration) return;
        setProgress(Math.min(100, (video.currentTime / video.duration) * 100));
    }

    function toggleSound() {
        const video = videoRef.current;
        if (!video) return;
        video.muted = !video.muted;
        setMuted(video.muted);
    }

    return (
        <div
            className={`fixed inset-0 z-[100] bg-black transition-opacity duration-[400ms] ${
                leaving ? 'pointer-events-none opacity-0' : 'opacity-100'
            }`}
            role="dialog"
            aria-label="Intro"
        >
            <video
                ref={videoRef}
                src={INTRO_SRC}
                className="h-full w-full object-cover"
                playsInline
                autoPlay
                muted
                preload="auto"
                onEnded={finish}
                onError={finish}
                onStalled={finish}
                onTimeUpdate={onTimeUpdate}
            />

            {/* progress hairline */}
            <div className="absolute inset-x-0 bottom-0 h-0.5 bg-white/15">
                <div
                    className="h-full bg-white/80 transition-[width] duration-200 ease-linear"
                    style={{ width: `${progress}%` }}
                />
            </div>

            {/* sound, bottom-left — muted autoplay is forced, so offer the way back */}
            <button
                type="button"
                onClick={toggleSound}
                className="absolute bottom-6 left-6 inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2.5 text-[0.7rem] font-semibold uppercase tracking-[0.14em] text-white/90 backdrop-blur transition-colors hover:bg-white/20"
            >
                {muted ? <MutedIcon /> : <SoundIcon />}
                {muted ? 'Sound off' : 'Sound on'}
            </button>

            {/* skip, bottom-right */}
            <button
                type="button"
                onClick={finish}
                autoFocus
                className="group absolute bottom-6 right-6 inline-flex items-center gap-2 rounded-full bg-white/95 px-5 py-2.5 text-[0.7rem] font-semibold uppercase tracking-[0.14em] text-[#12100E] transition-transform hover:scale-[1.04]"
            >
                Skip intro
                <svg viewBox="0 0 24 24" className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5"
                     fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12h14M13 6l6 6-6 6" />
                </svg>
            </button>
        </div>
    );
}

function MutedIcon() {
    return (
        <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor"
             strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M11 5 6 9H2v6h4l5 4z" />
            <path d="m17 9 4 6M21 9l-4 6" />
        </svg>
    );
}

function SoundIcon() {
    return (
        <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor"
             strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M11 5 6 9H2v6h4l5 4z" />
            <path d="M16 9a4 4 0 0 1 0 6M19 6a8 8 0 0 1 0 12" />
        </svg>
    );
}
