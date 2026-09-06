import { media } from '../data/media.js';
import { navLinks } from '../data/options.js';
import { ThemeToggle } from './ThemeToggle.jsx';
import { ReelsMark, ShortsMark, YouTubeMark } from './Visuals.jsx';

/**
 * The hero: one dark photographic card inset from the cream page.
 *
 * The nav lives inside the card rather than above it, so the top of the page
 * is a single object sitting on paper instead of a bar plus a banner. The
 * wordmark is set enormous along the bottom edge and deliberately clipped by
 * it — a full word floating in the middle would read as a heading, whereas a
 * cropped one reads as print.
 */
export function Hero({ onNavigate, profileName, channelTitle, channelUrl, publishMode, onReplayIntro }) {
    return (
        <section id="top" className="px-3 pt-3 sm:px-4 sm:pt-4">
            <div className="relative mx-auto w-full max-w-[1560px] overflow-hidden rounded-[1.5rem] bg-[#12100E] grain sm:rounded-[2rem]">
                {/* the photograph */}
                <img
                    src={media.hero}
                    alt=""
                    fetchPriority="high"
                    className="absolute inset-0 h-full w-full object-cover object-center opacity-[0.72]"
                />
                {/* warm key light from the left, then a bottom scrim for the type */}
                <div className="absolute inset-0 bg-[radial-gradient(120%_90%_at_15%_20%,rgba(255,190,120,0.16),transparent_60%)]" />
                <div className="absolute inset-0 scrim" />

                <div className="relative flex min-h-[max(520px,82svh)] flex-col">
                    {/* ---------------- nav ---------------- */}
                    <nav className="flex items-center justify-between gap-4 px-4 py-4 sm:px-7 sm:py-6">
                        <button
                            type="button"
                            onClick={() => onNavigate?.('top')}
                            className="flex items-center gap-2.5 text-white"
                        >
                            <span className="grid h-8 w-8 place-items-center rounded-full bg-white/95 text-[#12100E]">
                                <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                                    <path d="M17.5 10.5A6.5 6.5 0 1 1 14 5.4" />
                                    <path d="M12.4 4.6 15.9 3.6 16.8 7.2Z" fill="currentColor" stroke="none" />
                                    <path d="M9.5 9.2 14 12l-4.5 2.8Z" fill="currentColor" stroke="none" />
                                </svg>
                            </span>
                            <span className="display text-[1.05rem] tracking-tight">Flux</span>
                        </button>

                        <div className="hidden items-center gap-8 lg:flex">
                            {navLinks.slice(1).map((link) => (
                                <button
                                    key={link.id}
                                    type="button"
                                    onClick={() => onNavigate?.(link.id)}
                                    className="text-[0.7rem] font-medium uppercase tracking-[0.16em] text-white/75 transition-colors hover:text-white"
                                >
                                    {link.label}
                                </button>
                            ))}
                        </div>

                        <div className="flex items-center gap-2">
                            {/* Only offered where the intro would actually play —
                                a Replay button for something that never ran on
                                this device is worse than no button. */}
                            {onReplayIntro ? (
                                <button
                                    type="button"
                                    onClick={onReplayIntro}
                                    title="Replay the intro"
                                    className="hidden items-center gap-1.5 rounded-full border border-white/25 px-3.5 py-2 text-[0.62rem] font-medium uppercase tracking-[0.14em] text-white/75 transition-colors hover:border-white/50 hover:text-white lg:inline-flex"
                                >
                                    <svg viewBox="0 0 24 24" className="h-3 w-3" fill="none" stroke="currentColor"
                                         strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                                        <path d="M3 12a9 9 0 1 0 3-6.7" />
                                        <path d="M3 4v5h5" />
                                    </svg>
                                    Replay intro
                                </button>
                            ) : null}
                            {/* Scoped dark so the toggle reads against the photo
                                rather than inheriting the cream page palette. */}
                            <span className="dark hidden sm:block">
                                <ThemeToggle />
                            </span>
                            <button
                                type="button"
                                onClick={() => onNavigate?.('channel')}
                                className="inline-flex items-center gap-2 rounded-full bg-white/95 px-4 py-2.5 text-[0.68rem] font-semibold uppercase tracking-[0.12em] text-[#12100E] transition-transform hover:scale-[1.03] sm:px-5"
                            >
                                <span className="text-accent">+</span> Start automating
                            </button>
                        </div>
                    </nav>

                    {/* ---------------- copy ---------------- */}
                    <div className="flex flex-1 items-end px-4 pb-2 sm:px-7">
                        <div className="ml-auto max-w-sm pb-8 text-right sm:pb-12">
                            <p className="text-[0.82rem] leading-relaxed text-white/80 sm:text-sm">
                                Filming and editing is half the job. Uploading, tagging,
                                scheduling, thumbnails, captions and cutting clips for socials
                                is the other half — and it eats hours every week. Flux runs
                                that half for you.
                            </p>
                            <div className="mt-5 flex flex-wrap items-center justify-end gap-4 text-white/55">
                                <span className="flex items-center gap-1.5 text-[0.62rem] uppercase tracking-[0.16em]">
                                    <YouTubeMark className="h-3.5 w-3.5" /> YouTube
                                </span>
                                <span className="flex items-center gap-1.5 text-[0.62rem] uppercase tracking-[0.16em]">
                                    <ShortsMark className="h-3.5 w-3.5" /> Shorts
                                </span>
                                <span className="flex items-center gap-1.5 text-[0.62rem] uppercase tracking-[0.16em]">
                                    <ReelsMark className="h-3.5 w-3.5" /> Reels
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* ---------------- wordmark ---------------- */}
                    <div className="relative px-2 sm:px-4">
                        <span
                            className="wordmark block translate-y-[0.14em] select-none bg-gradient-to-b from-white via-white/90 to-white/35 bg-clip-text text-center text-wordmark text-transparent"
                            aria-hidden="true"
                        >
                            Flux
                        </span>
                    </div>
                </div>

                {/* the round badge, overlapping the wordmark like a sticker */}
                <button
                    type="button"
                    onClick={() => onNavigate?.('channel')}
                    className="group absolute bottom-6 left-4 grid h-[5.5rem] w-[5.5rem] place-items-center rounded-full bg-white text-center text-[0.58rem] font-semibold uppercase leading-[1.35] tracking-[0.1em] text-[#12100E] transition-transform duration-300 hover:scale-105 sm:bottom-10 sm:left-8 sm:h-24 sm:w-24"
                >
                    <span>
                        Start
                        <br />
                        your
                        <br />
                        channel
                    </span>
                </button>

                {/* live state, top-right of the card's lower half */}
                <div className="absolute right-4 top-[4.75rem] flex flex-col items-end gap-1.5 sm:right-7 sm:top-24">
                    {profileName ? (
                        <span className="rounded-full bg-black/35 px-3 py-1 text-[0.62rem] uppercase tracking-[0.14em] text-white/80 backdrop-blur">
                            {profileName}
                        </span>
                    ) : null}
                    {channelTitle ? (
                        // A link when we know where the channel lives, plain text
                        // otherwise - a badge that looks clickable and is not is
                        // worse than one that never invited the click.
                        channelUrl ? (
                            <a
                                href={channelUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                title={`Open ${channelTitle} on YouTube`}
                                className="flex items-center gap-1.5 rounded-full bg-black/35 px-3 py-1 text-[0.62rem] uppercase tracking-[0.14em] text-white/80 backdrop-blur transition-colors hover:bg-black/55 hover:text-white"
                            >
                                <YouTubeMark className="h-3 w-3" />
                                {publishMode === 'own' ? channelTitle : `via ${channelTitle}`}
                            </a>
                        ) : (
                            <span className="flex items-center gap-1.5 rounded-full bg-black/35 px-3 py-1 text-[0.62rem] uppercase tracking-[0.14em] text-white/80 backdrop-blur">
                                <YouTubeMark className="h-3 w-3" />
                                {publishMode === 'own' ? channelTitle : `via ${channelTitle}`}
                            </span>
                        )
                    ) : null}
                </div>
            </div>
        </section>
    );
}
