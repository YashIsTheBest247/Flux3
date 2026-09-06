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
}) {
    const query = searchQuery.trim().toLowerCase();
    const filtered = query
        ? videos.filter(
              (video) =>
                  video.name.toLowerCase().includes(query) ||
                  titleFromFilename(video.name).toLowerCase().includes(query)
          )
        : videos;

    const showAwaiting = isGenerating || isPolling;

    return (
        <section id="library" className="mx-auto max-w-7xl px-5 py-12 lg:px-8">
            <div className="mb-10 flex flex-wrap items-end justify-between gap-4">
                <div>
                    <span className="eyebrow">Output</span>
                    <h2 className="display mt-2 text-3xl font-semibold sm:text-4xl">Library</h2>
                </div>
                <div className="flex items-center gap-4">
                    <span className="chip">
                        {filtered.length} {filtered.length === 1 ? 'render' : 'renders'}
                    </span>
                    <input
                        type="search"
                        value={searchQuery}
                        onChange={(event) => onSearchChange(event.target.value)}
                        placeholder="Search library…"
                        className="field-input w-48 rounded-full py-2 text-sm"
                    />
                </div>
            </div>

            {filtered.length === 0 && !showAwaiting ? (
                <div className="glass grid place-items-center p-14 text-center">
                    <p className="display text-2xl font-semibold text-txt">No renders yet</p>
                    <p className="mt-2 text-sm text-muted">
                        {query
                            ? 'Nothing matches that search.'
                            : 'Generate your first video from the creator above.'}
                    </p>
                </div>
            ) : (
                <div className="flex flex-wrap justify-center gap-6 sm:justify-start">
                    {showAwaiting && (
                        <article className="glass flex h-[5cm] w-[3cm] flex-col items-center justify-center gap-2 p-3 text-center">
                            <span className="h-2.5 w-2.5 animate-pulse rounded-full bg-accent" />
                            <p className="display text-sm font-semibold text-txt">Rendering</p>
                            <p className="text-[0.6rem] text-muted">Appears here when ready</p>
                        </article>
                    )}
                    {filtered.map((video, index) => (
                        <VideoCard
                            key={video.name}
                            index={index}
                            video={video}
                            isNew={video.name === newFilename}
                            onRequestDelete={onRequestDelete}
                        />
                    ))}
                </div>
            )}
        </section>
    );
}
