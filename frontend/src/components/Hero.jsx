import { useEffect, useState } from 'react';
import { brandLogos, heroNodes } from '../data/options.js';
import { BrandIcon } from './BrandIcon.jsx';

const HEADLINES = [
    'One-click Production',
    'Video Creation Simplified',
    'Automated Pipeline',
    'From Prompt to Publish',
];

function Node({ label, code, icon, position }) {
    return (
        <div className={`absolute ${position} hidden animate-floaty items-center gap-2 lg:flex`}>
            <span className="grid h-9 w-9 place-items-center rounded-full border border-tint/15 bg-tint/[0.06] text-txt">
                <BrandIcon name={icon} className="h-4 w-4" />
            </span>
            <div className="leading-tight">
                <p className="text-xs font-medium text-txt">{label}</p>
                <p className="text-[0.65rem] text-faint">{code}</p>
            </div>
        </div>
    );
}

export function Hero({ onOpenApp, onDiscover }) {
    // Show "Flux" once on load, then cross-fade through the headlines on repeat.
    const [headline, setHeadline] = useState('Flux');
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        const FADE_MS = 600;
        const HOLD_MS = 2600;
        const timers = [];
        let index = -1; // -1 = the intro "Flux"

        // fade the intro word in
        timers.push(window.setTimeout(() => setVisible(true), 60));

        const swapTo = (text) => {
            setVisible(false); // fade current out
            timers.push(
                window.setTimeout(() => {
                    setHeadline(text);
                    setVisible(true); // fade next in
                }, FADE_MS)
            );
        };

        const interval = window.setInterval(() => {
            index = (index + 1) % HEADLINES.length;
            swapTo(HEADLINES[index]);
        }, HOLD_MS);

        return () => {
            window.clearInterval(interval);
            timers.forEach(window.clearTimeout);
        };
    }, []);

    return (
        <section className="px-4 pt-4 lg:px-8">
            <div className="relative mx-auto max-w-7xl overflow-hidden rounded-4xl border border-tint/10 bg-panel shadow-card">
                {/* Ambient glows */}
                <div className="glow-radial pointer-events-none absolute left-1/2 top-[42%] h-[640px] w-[640px] -translate-x-1/2 -translate-y-1/2 rounded-full" />
                <div className="glow-cool pointer-events-none absolute right-0 top-0 h-[420px] w-[420px] rounded-full" />

                {/* Curved connector lines toward the floating labels */}
                <svg
                    className="pointer-events-none absolute inset-0 z-0 hidden h-full w-full stroke-tint/20 lg:block"
                    viewBox="0 0 100 100"
                    preserveAspectRatio="none"
                    fill="none"
                    aria-hidden="true"
                >
                    <path d="M0 9 C 10 16, 4 26, 18 31" vectorEffect="non-scaling-stroke" />
                    <path d="M100 8 C 90 15, 96 24, 82 30" vectorEffect="non-scaling-stroke" />
                    <path d="M0 87 C 10 80, 4 73, 18 70" vectorEffect="non-scaling-stroke" />
                    <path d="M100 86 C 90 79, 96 72, 82 69" vectorEffect="non-scaling-stroke" />
                </svg>

                {/* Floating labels */}
                {heroNodes.map((node) => (
                    <Node key={node.label} {...node} />
                ))}

                {/* Center content */}
                <div className="relative z-10 flex flex-col items-center px-6 pb-10 pt-16 text-center lg:pt-28">
                    <h1 className="display mx-auto flex min-h-[2.2em] max-w-4xl items-center justify-center text-4xl font-semibold leading-[1.05] sm:text-6xl lg:min-h-[1.2em] lg:text-7xl">
                        <span
                            className={`gradient-text transition-all duration-[600ms] ease-out ${
                                visible
                                    ? 'translate-y-0 opacity-100 blur-0'
                                    : 'translate-y-3 opacity-0 blur-[6px]'
                            }`}
                        >
                            {headline}
                        </span>
                    </h1>

                    <p className="mx-auto mt-6 max-w-xl text-sm text-txt/80 lg:text-base">
                        Hand Flux a topic and it writes the script, sources the imagery, narrates the
                        voiceover, times the subtitles, and assembles a finished cut.
                    </p>

                    <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
                        <button type="button" onClick={onOpenApp} className="btn-ghost">
                            Run App
                        </button>
                        <button type="button" onClick={onDiscover} className="btn-light">
                            Discover More
                        </button>
                    </div>
                </div>
            </div>

            {/* Brand strip — continuous right-to-left marquee */}
            <div
                className="group relative mx-auto mt-8 max-w-6xl overflow-hidden px-4 pb-2"
                style={{
                    maskImage:
                        'linear-gradient(to right, transparent, #000 12%, #000 88%, transparent)',
                    WebkitMaskImage:
                        'linear-gradient(to right, transparent, #000 12%, #000 88%, transparent)',
                }}
            >
                <div className="flex w-max animate-marquee items-center gap-x-12">
                    {[...brandLogos, ...brandLogos].map((brand, index) => (
                        <span
                            key={`${brand}-${index}`}
                            className="flex shrink-0 items-center gap-2 text-sm font-medium tracking-wide text-muted"
                            aria-hidden={index >= brandLogos.length}
                        >
                            <BrandIcon name={brand} className="h-4 w-4" />
                            {brand}
                        </span>
                    ))}
                </div>
            </div>
        </section>
    );
}
