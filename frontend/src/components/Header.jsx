import { useState } from 'react';
import { navLinks } from '../data/options.js';
import { ThemeToggle } from './ThemeToggle.jsx';

const channelUrl =
    import.meta.env.VITE_FLUX_CHANNEL_URL?.trim() ||
    'https://youtube.com/@echoesofmyindia?si=q-RwYc6p1VVCCtD_';

function YouTubeIcon({ className }) {
    return (
        <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
            <path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.6 12 3.6 12 3.6s-7.5 0-9.4.5A3 3 0 0 0 .5 6.2 31.4 31.4 0 0 0 0 12a31.4 31.4 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.9.5 9.4.5 9.4.5s7.5 0 9.4-.5a3 3 0 0 0 2.1-2.1A31.4 31.4 0 0 0 24 12a31.4 31.4 0 0 0-.5-5.8zM9.6 15.6V8.4l6.2 3.6-6.2 3.6z" />
        </svg>
    );
}

function Logo() {
    return (
        <span className="grid h-9 w-9 place-items-center rounded-full border border-tint/15 bg-tint/[0.06] text-txt">
            <svg viewBox="0 0 24 24" className="h-5 w-5">
                <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" strokeWidth="1.6" />
                <path
                    d="M14.5 5.5a7 7 0 1 0 0 13 5.6 5.6 0 0 1 0-13z"
                    fill="currentColor"
                />
                <circle cx="9" cy="12" r="1.3" fill="currentColor" />
            </svg>
        </span>
    );
}

export function Header({ onNavigate }) {
    const [menuOpen, setMenuOpen] = useState(false);

    function handleNav(id) {
        setMenuOpen(false);
        onNavigate?.(id);
    }

    return (
        <header className="sticky top-0 z-50 border-b border-tint/10 bg-panel/70 backdrop-blur-xl">
            <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-5 py-3 lg:px-8 lg:py-4">
                <button
                    type="button"
                    onClick={() => handleNav('top')}
                    className="flex items-center gap-2.5"
                >
                    <Logo />
                    <span className="display text-lg font-semibold">Flux</span>
                </button>

                {/* Center pill nav */}
                <nav className="hidden items-center gap-1 rounded-full border border-tint/10 bg-tint/[0.04] px-2 py-1.5 backdrop-blur-xl lg:flex">
                    {navLinks.map((link) => (
                        <button
                            key={link.id}
                            type="button"
                            onClick={() => handleNav(link.id)}
                            className="rounded-full px-4 py-1.5 text-sm font-medium text-muted transition-colors hover:bg-tint/[0.06] hover:text-txt"
                        >
                            {link.label}
                        </button>
                    ))}
                </nav>

                <div className="hidden items-center gap-3 lg:flex">
                    <ThemeToggle />
                    <a
                        href={channelUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2.5 text-sm font-medium text-txt transition-opacity hover:opacity-80"
                    >
                        <span className="grid h-8 w-8 place-items-center rounded-full border border-tint/15 bg-tint/[0.06] text-txt">
                            <YouTubeIcon className="h-4 w-4" />
                        </span>
                        Flux Channel
                    </a>
                </div>

                <div className="flex items-center gap-2 lg:hidden">
                    <ThemeToggle />
                    <button
                        type="button"
                        aria-label="Toggle menu"
                        onClick={() => setMenuOpen((open) => !open)}
                        className="grid h-10 w-10 place-items-center rounded-full border border-tint/15 bg-panel"
                    >
                        <span className="flex flex-col gap-1.5">
                            <span className="h-0.5 w-4 bg-txt" />
                            <span className="h-0.5 w-4 bg-txt" />
                            <span className="h-0.5 w-4 bg-txt" />
                        </span>
                    </button>
                </div>
            </div>

            {menuOpen && (
                <div className="mx-5 mb-2 glass p-3 lg:hidden">
                    {navLinks.map((link) => (
                        <button
                            key={link.id}
                            type="button"
                            onClick={() => handleNav(link.id)}
                            className="block w-full rounded-xl px-4 py-2.5 text-left text-sm font-medium text-muted hover:bg-tint/[0.06] hover:text-txt"
                        >
                            {link.label}
                        </button>
                    ))}
                    <a
                        href={channelUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-light mt-2 flex w-full items-center justify-center gap-2"
                    >
                        <YouTubeIcon className="h-4 w-4" />
                        Flux Channel
                    </a>
                </div>
            )}
        </header>
    );
}
