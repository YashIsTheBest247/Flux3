import { mediaUrl } from '../api/client.js';
import { titleFromFilename } from '../lib/payload.js';

export function VideoCard({ index, video, isNew, onRequestDelete }) {
    const number = String(index + 1).padStart(2, '0');
    const title = titleFromFilename(video.name);
    const src = mediaUrl(video.path);
    const poster = video.thumbnail ? mediaUrl(video.thumbnail) : undefined;

    return (
        <article className="group relative h-[5cm] w-[3cm] shrink-0 origin-center overflow-hidden rounded-xl border border-tint/10 bg-black/50 shadow-card transition-all duration-300 ease-out hover:z-30 hover:scale-[1.7] hover:border-tint/30">
            <video
                controls
                preload="metadata"
                src={src}
                poster={poster}
                className="h-full w-full object-cover"
            >
                Your browser does not support embedded video.
            </video>

            {/* gradient + title overlay */}
            <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/85 via-black/30 to-transparent p-2 pt-6">
                <p className="line-clamp-2 text-[0.55rem] font-medium leading-tight text-white">
                    {title}
                </p>
            </div>

            {/* index */}
            <span className="pointer-events-none absolute left-1.5 top-1.5 rounded bg-black/50 px-1 text-[0.5rem] font-semibold text-white/80">
                {number}
            </span>

            {isNew && (
                <span className="pointer-events-none absolute right-1.5 top-1.5 rounded-full bg-accent px-1.5 py-0.5 text-[0.45rem] font-bold uppercase tracking-wider text-onprimary">
                    New
                </span>
            )}

            {/* hover actions */}
            <div className="absolute inset-x-0 top-0 flex justify-end gap-1 p-1.5 opacity-0 transition-opacity duration-200 group-hover:opacity-100">
                <a
                    href={src}
                    download
                    onClick={(e) => e.stopPropagation()}
                    title="Download"
                    className="grid h-5 w-5 place-items-center rounded-md bg-black/60 text-white backdrop-blur transition-colors hover:bg-black/80"
                >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-3 w-3" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M12 3v12M7 10l5 5 5-5M5 21h14" />
                    </svg>
                </a>
                <button
                    type="button"
                    title="Delete"
                    onClick={(e) => {
                        e.stopPropagation();
                        onRequestDelete?.({ name: video.name, title });
                    }}
                    className="grid h-5 w-5 place-items-center rounded-md bg-red-500/80 text-white backdrop-blur transition-colors hover:bg-red-500"
                >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-3 w-3" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M6 6v14a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V6" />
                    </svg>
                </button>
            </div>
        </article>
    );
}
