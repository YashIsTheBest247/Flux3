import { useState } from 'react';
import { navLinks } from '../data/options.js';
import { ThemeToggle } from './ThemeToggle.jsx';

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
                    <button
                        type="button"
                        onClick={() => handleNav('creator')}
                        className="flex items-center gap-2.5 text-sm font-medium text-txt transition-opacity hover:opacity-80"
                    >
                        <span className="grid h-8 w-8 place-items-center rounded-full border border-tint/15 bg-tint/[0.06] text-txt">
                            <svg viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
                                <circle cx="12" cy="8" r="3.6" />
                                <path d="M4.5 20a7.5 7.5 0 0 1 15 0 1 1 0 0 1-1 1h-13a1 1 0 0 1-1-1z" />
                            </svg>
                        </span>
                        Create Account
                    </button>
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
                    <button
                        type="button"
                        onClick={() => handleNav('creator')}
                        className="btn-light mt-2 w-full"
                    >
                        Create Account
                    </button>
                </div>
            )}
        </header>
    );
}
