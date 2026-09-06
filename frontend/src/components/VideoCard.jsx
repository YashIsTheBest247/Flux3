import { mediaUrl } from '../api/client.js';
import { titleFromFilename } from '../lib/payload.js';

export function VideoCard({ index, video, isNew }) {
    const number = String(index + 1).padStart(2, '0');
    const title = titleFromFilename(video.name);
    const src = mediaUrl(video.path);

    return (
        <article className="group glass overflow-hidden transition-all hover:border-tint/20">
            <div className="flex items-start justify-between gap-3 px-5 pt-5">
                <span className="display text-2xl font-semibold text-muted">{number}</span>
                <div className="flex flex-col items-end text-right">
                    {isNew && (
                        <span className="mb-1 rounded-full bg-accent/15 px-2 py-0.5 text-[0.6rem] font-semibold uppercase tracking-widest text-accent">
                            New
                        </span>
                    )}
                    <h3 className="max-w-[12rem] text-sm font-medium text-txt">{title}</h3>
                </div>
            </div>

            <div className="mt-4 aspect-video w-full overflow-hidden bg-black/40">
                <video controls preload="metadata" src={src} className="h-full w-full object-cover">
                    Your browser does not support embedded video.
                </video>
            </div>

            <div className="flex items-center justify-between gap-3 px-5 py-4">
                <span className="truncate text-xs text-faint">{video.name}</span>
                <a
                    href={src}
                    download
                    className="shrink-0 text-xs font-medium text-accent underline-offset-4 hover:underline"
                >
                    Download
                </a>
            </div>
        </article>
    );
}
