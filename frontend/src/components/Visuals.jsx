import { vertical } from '../data/media.js';

/**
 * The visual language: platform marks, vertical-video mockups, and the
 * automation loop.
 *
 * The chrome is drawn rather than photographed - no stock library has a picture
 * of a Shorts player, and a drawn one cannot 404 or need a licence. Real
 * footage goes *inside* the frames, because an empty gradient in a phone
 * mockup reads as a component that failed to load rather than as a video.
 */

export function YouTubeMark({ className = 'h-4 w-4' }) {
    return (
        <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
            <path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.6 12 3.6 12 3.6s-7.5 0-9.4.5A3 3 0 0 0 .5 6.2 31.4 31.4 0 0 0 0 12a31.4 31.4 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1A31.4 31.4 0 0 0 24 12a31.4 31.4 0 0 0-.5-5.8zM9.6 15.6V8.4l6.2 3.6-6.2 3.6z" />
        </svg>
    );
}

export function ShortsMark({ className = 'h-4 w-4' }) {
    return (
        <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
            <path d="M14.6 2.6a5.1 5.1 0 0 1 2 7l-1.3.8-2.1-3.6 1.3-.8a1 1 0 0 0-1-1.7L6.7 8.6a1 1 0 0 0 1 1.7l.7-.4 2.1 3.6-.7.4a5.1 5.1 0 0 1-5.1-8.8l6.8-3.9a5.1 5.1 0 0 1 3.1-.6z" opacity=".55" />
            <path d="M9.4 21.4a5.1 5.1 0 0 1-2-7l1.3-.8 2.1 3.6-1.3.8a1 1 0 0 0 1 1.7l6.8-3.9a1 1 0 0 0-1-1.7l-.7.4-2.1-3.6.7-.4a5.1 5.1 0 0 1 5.1 8.8l-6.8 3.9a5.1 5.1 0 0 1-3.1.2z" />
            <path d="M10.3 9.1 15 12l-4.7 2.9z" />
        </svg>
    );
}

export function ReelsMark({ className = 'h-4 w-4' }) {
    return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
             strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
            <rect x="2.5" y="2.5" width="19" height="19" rx="5" />
            <path d="m8.2 2.8 3 5.2M14.2 2.8l3 5.2M2.6 8h18.8" />
            <path d="m10.4 12.2 4.4 2.5-4.4 2.5z" fill="currentColor" stroke="none" />
        </svg>
    );
}

/**
 * A 9:16 phone showing a vertical video with captions and the side rail.
 *
 * `variant` only changes the palette of the "footage" behind the chrome, so a
 * row of these reads as three different videos rather than one repeated three
 * times.
 */
export function ShortsPhone({
    variant = 'warm',
    caption = 'Markets moved 4% today',
    label = 'Shorts',
    image,
    className = '',
    style,
}) {
    const footage = {
        warm: 'from-[#8A5A32] via-[#3E2A1C] to-[#120E0A]',
        cool: 'from-[#2F5670] via-[#1E2E3C] to-[#0B0F14]',
        violet: 'from-[#5B3A72] via-[#33223F] to-[#0F0A14]',
        green: 'from-[#2F6B52] via-[#1D3B2E] to-[#0A120E]',
    }[variant] ?? 'from-[#8A5A32] via-[#3E2A1C] to-[#120E0A]';

    return (
        // No width here on purpose. A `w-full` in the base class collides with
        // whatever width the caller passes, and Tailwind resolves that by
        // stylesheet order rather than class order - which silently blew these
        // up to full width wherever a `w-24` was passed. Width is the caller's.
        <div
            className={`relative aspect-[9/16] overflow-hidden rounded-[1.6rem] border border-tint/15 bg-panel shadow-card grain ${className}`}
            style={style}
        >
            {/* Gradient first: it is the backdrop when no image is given, and
                the thing that shows through if one fails to load. */}
            <div className={`absolute inset-0 bg-gradient-to-b ${footage}`} />
            {image ? (
                <img
                    src={image}
                    alt=""
                    loading="lazy"
                    className="absolute inset-0 h-full w-full object-cover opacity-90"
                    onError={(event) => {
                        event.currentTarget.style.display = 'none';
                    }}
                />
            ) : null}
            {/* a soft key light, so it reads as a lit scene rather than a swatch */}
            <div className="absolute -left-1/4 top-[-15%] h-2/3 w-3/4 rounded-full bg-white/10 blur-3xl" />
            <div className="absolute inset-0 scrim" />

            {/* platform chip. Sits top-LEFT and the rail sits bottom-right, so
                the two can never collide however narrow the frame gets. */}
            <div className="absolute left-3 top-3 flex items-center gap-1.5 rounded-full bg-black/50 px-2.5 py-1 text-[0.62rem] font-semibold uppercase tracking-[0.12em] text-white backdrop-blur">
                {label === 'Reels' ? <ReelsMark className="h-3 w-3" /> : <ShortsMark className="h-3 w-3" />}
                {label}
            </div>

            {/* side rail, anchored to the lower half so it clears the chip */}
            <div className="absolute bottom-[22%] right-2.5 flex flex-col items-center gap-3 text-white/90">
                {['heart', 'chat', 'share'].map((icon) => (
                    <span key={icon} className="grid h-8 w-8 place-items-center rounded-full bg-black/35 backdrop-blur">
                        <RailIcon name={icon} />
                    </span>
                ))}
            </div>

            {/* burned-in caption line */}
            <div className="absolute inset-x-3 bottom-7">
                <p className="text-[0.72rem] font-semibold leading-snug text-white drop-shadow-[0_2px_6px_rgba(0,0,0,0.9)]">
                    {caption}
                </p>
            </div>

            {/* scrubber */}
            <div className="absolute inset-x-3 bottom-4 h-[3px] overflow-hidden rounded-full bg-white/25">
                <div className="h-full w-2/3 rounded-full bg-white/85" />
            </div>
        </div>
    );
}

function RailIcon({ name }) {
    const common = {
        viewBox: '0 0 24 24',
        fill: 'none',
        stroke: 'currentColor',
        strokeWidth: 2,
        strokeLinecap: 'round',
        strokeLinejoin: 'round',
        className: 'h-3.5 w-3.5',
        'aria-hidden': true,
    };
    if (name === 'heart') {
        return <svg {...common}><path d="M12 20s-7-4.4-7-9a4 4 0 0 1 7-2.6A4 4 0 0 1 19 11c0 4.6-7 9-7 9z" /></svg>;
    }
    if (name === 'chat') {
        return <svg {...common}><path d="M20 15a2 2 0 0 1-2 2H8l-4 3V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2z" /></svg>;
    }
    return <svg {...common}><path d="M4 12v7a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-7M12 3v13M8 7l4-4 4 4" /></svg>;
}

/** Three phones, fanned. The hero and the upload screen both use this. */
export function PhoneCluster({ className = '' }) {
    return (
        <div className={`relative ${className}`} aria-hidden="true">
            <div className="flex items-end justify-center gap-3 sm:gap-5">
                <ShortsPhone
                    variant="cool"
                    label="Reels"
                    image={vertical.clip}
                    caption="3 clips cut from one upload"
                    className="w-[26%] -rotate-6 opacity-90"
                />
                <ShortsPhone
                    variant="warm"
                    label="Shorts"
                    image={vertical.shorts}
                    caption="Titled, tagged and scheduled while you slept"
                    className="z-10 w-[34%]"
                />
                <ShortsPhone
                    variant="violet"
                    label="Shorts"
                    image={vertical.captions}
                    caption="Captions written from your own audio"
                    className="w-[26%] rotate-6 opacity-90"
                />
            </div>
        </div>
    );
}

/**
 * The automation loop, as a ring of labelled stops.
 *
 * Drawn as a real cycle rather than a left-to-right pipeline because the point
 * of the product is that it comes back around tomorrow without being asked.
 */
export function AutomationLoop({ className = '' }) {
    const stops = ['Find', 'Write', 'Voice', 'Caption', 'Thumbnail', 'Publish'];
    const radius = 86;
    const centre = 110;

    return (
        <div className={`relative ${className}`}>
            <svg viewBox="0 0 220 220" className="h-full w-full" role="img"
                 aria-label="The automation loop: find, write, voice, caption, thumbnail, publish">
                <defs>
                    <linearGradient id="loop-stroke" x1="0" y1="0" x2="1" y2="1">
                        <stop offset="0%" stopColor="currentColor" stopOpacity="0.65" />
                        <stop offset="100%" stopColor="currentColor" stopOpacity="0.12" />
                    </linearGradient>
                </defs>

                <circle cx={centre} cy={centre} r={radius} fill="none"
                        stroke="url(#loop-stroke)" strokeWidth="1.25" strokeDasharray="3 5" />

                {stops.map((stop, index) => {
                    // -90deg so the first stop sits at the top, where a reader starts.
                    const angle = (index / stops.length) * Math.PI * 2 - Math.PI / 2;
                    const x = centre + Math.cos(angle) * radius;
                    const y = centre + Math.sin(angle) * radius;
                    const isFirst = index === 0;
                    return (
                        <g key={stop}>
                            <circle cx={x} cy={y} r={isFirst ? 5 : 3.5} fill="currentColor"
                                    opacity={isFirst ? 0.95 : 0.5} />
                            <text
                                x={x} y={y - 12}
                                textAnchor="middle"
                                className="fill-current text-[9px] uppercase"
                                style={{ letterSpacing: '0.14em', opacity: isFirst ? 0.95 : 0.55 }}
                            >
                                {stop}
                            </text>
                        </g>
                    );
                })}

                <text x={centre} y={centre - 4} textAnchor="middle"
                      className="fill-current text-[13px]" style={{ opacity: 0.9 }}>
                    every day
                </text>
                <text x={centre} y={centre + 13} textAnchor="middle"
                      className="fill-current text-[9px] uppercase"
                      style={{ letterSpacing: '0.18em', opacity: 0.45 }}>
                    unattended
                </text>
            </svg>
        </div>
    );
}

/**
 * A photographic slot that degrades into a designed gradient.
 *
 * Any remote image can fail - a blocked host, an expired link, an offline
 * demo - and a broken-image icon in the middle of a hero is worse than no
 * image at all. The fallback is built to look deliberate.
 */
export function ImageFrame({ src, alt = '', tone = 'warm', className = '', children }) {
    const tones = {
        warm: 'from-[#7A4F2E] via-[#2E2018] to-[#100C09]',
        cool: 'from-[#2B4C63] via-[#1B2833] to-[#0A0E12]',
        neutral: 'from-[#4A4136] via-[#241F1A] to-[#0D0B09]',
    };
    return (
        <div className={`relative overflow-hidden rounded-3xl border border-tint/10 bg-panel grain ${className}`}>
            <div className={`absolute inset-0 bg-gradient-to-br ${tones[tone] ?? tones.warm}`} />
            <div className="absolute -right-1/4 -top-1/4 h-2/3 w-2/3 rounded-full bg-white/10 blur-3xl" />
            {src ? (
                <img
                    src={src}
                    alt={alt}
                    loading="lazy"
                    className="absolute inset-0 h-full w-full object-cover"
                    onError={(event) => {
                        // Reveal the gradient underneath rather than the browser's
                        // broken-image glyph.
                        event.currentTarget.style.display = 'none';
                    }}
                />
            ) : null}
            {children ? <div className="relative">{children}</div> : null}
        </div>
    );
}
