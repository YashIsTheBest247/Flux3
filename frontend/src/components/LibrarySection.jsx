import { VideoCard } from './VideoCard.jsx';
import { titleFromFilename } from '../lib/payload.js';

export function LibrarySection({
    videos,
    searchQuery,
    onSearchChange,
    isGenerating,
    isPolling,
    newFilename,
    onRequestDelete,
    onPlay,
    onShowProvenance,
    storageStatus,
}) {
    const b2 = storageStatus?.backblaze_b2;
    const genblaze = storageStatus?.genblaze;
    const query = (searchQuery || '').trim().toLowerCase();
    const filtered = query
        ? videos.filter(
              (video) =>
                  video.name.toLowerCase().includes(query) ||
                  (video.topic || '').toLowerCase().includes(query) ||
                  titleFromFilename(video.name).toLowerCase().includes(query)
          )
        : videos;

    const showAwaiting = isGenerating || isPolling;

    return (
        <section id="library" className="mx-auto w-full max-w-[1560px] scroll-mt-6 px-5 py-16 sm:px-10">
            <div className="flex flex-wrap items-end justify-between gap-5">
                <div>
                    <span className="eyebrow">Your library</span>
                    <h2 className="display mt-3 text-display-md">
                        Everything <span className="text-accentsoft">published</span>
                    </h2>
                    <p className="mt-3 max-w-md text-sm leading-relaxed text-muted">
                        Finished renders, stored on Backblaze B2 with a signed manifest each.
                    </p>
                </div>

                {/* The search moved here from the old top bar - it only ever
                    filtered this list, so it belongs beside it. */}
                <label className="relative flex w-full max-w-sm items-center">
                    <span className="sr-only">Search your library</span>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="pointer-events-none absolute left-4 h-4 w-4 text-faint">
                        <circle cx="11" cy="11" r="7" />
                        <path d="m20 20-3.5-3.5" />
                    </svg>
                    <input
                        type="search"
                        value={searchQuery}
                        onChange={(event) => onSearchChange?.(event.target.value)}
                        placeholder="Search by topic…"
                        className="field-input rounded-full py-2.5 pl-11 pr-4 text-sm"
                    />
                </label>
            </div>

            {/* Where the media actually lives — durable storage + provenance status. */}
            {storageStatus && (
                <div className="mt-3 flex flex-wrap items-center gap-2">
                    <span className="chip">
                        <span
                            className={`h-1.5 w-1.5 rounded-full ${
                                b2?.available ? 'bg-accent' : 'bg-amber-400'
                            }`}
                        />
                        {b2?.available
                            ? `Backblaze B2 · ${b2.bucket}`
                            : 'Backblaze B2 not configured — storing locally'}
                    </span>
                    {genblaze?.enabled && (
                        <span className="chip">
                            <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                            Genblaze provenance
                            {genblaze.visual_flow ? ` · visuals: ${genblaze.visual_flow}` : ''}
                        </span>
                    )}
                </div>
            )}

            <div className="mt-6 border-t border-tint/10 pt-8">
                {filtered.length === 0 && !showAwaiting ? (
                    <div className="rounded-2xl border border-tint/10 p-14 text-center">
                        <p className="display text-xl font-semibold text-txt">No videos yet</p>
                        <p className="mt-2 text-sm text-muted">
                            {query
                                ? 'Nothing matches that search.'
                                : 'Run the automation above to generate your first video.'}
                        </p>
                    </div>
                ) : (
                    /* Two columns from the smallest screen up. A single-column
                       grid gave each phone-width card the full viewport, so one
                       video filled the screen and the library read as a feed
                       rather than a library. */
                    <div className="grid grid-cols-2 gap-x-3 gap-y-6 sm:gap-x-6 sm:gap-y-8 md:grid-cols-3 xl:grid-cols-4">
                        {showAwaiting && (
                            <article className="flex flex-col">
                                <div className="grid aspect-[9/16] w-full place-items-center rounded-xl border border-tint/10 bg-tint/[0.03]">
                                    <div className="flex flex-col items-center gap-2">
                                        <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-accent" />
                                        <p className="text-xs font-semibold text-txt sm:text-sm">Rendering</p>
                                    </div>
                                </div>
                                <p className="mt-2 truncate text-xs font-semibold text-muted sm:mt-3 sm:text-sm">
                                    Generating…
                                </p>
                            </article>
                        )}
                        {filtered.map((video) => (
                            <VideoCard
                                key={video.name}
                                video={video}
                                isNew={video.name === newFilename}
                                onRequestDelete={onRequestDelete}
                                onPlay={onPlay}
                                onShowProvenance={onShowProvenance}
                            />
                        ))}
                    </div>
                )}
            </div>
        </section>
    );
}
