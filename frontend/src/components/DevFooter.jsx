function PortfolioIcon() {
    return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" className="h-4 w-4">
            <circle cx="12" cy="12" r="9" />
            <path d="M3 12h18M12 3c2.5 2.5 3.8 5.7 3.8 9S14.5 18.5 12 21c-2.5-2.5-3.8-5.7-3.8-9S9.5 5.5 12 3z" />
        </svg>
    );
}

function GitHubIcon() {
    return (
        <svg viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
            <path d="M12 2C6.48 2 2 6.58 2 12.25c0 4.53 2.87 8.37 6.84 9.73.5.1.68-.22.68-.49 0-.24-.01-.87-.01-1.71-2.78.62-3.37-1.37-3.37-1.37-.45-1.18-1.11-1.5-1.11-1.5-.91-.64.07-.62.07-.62 1 .07 1.53 1.06 1.53 1.06.9 1.57 2.36 1.12 2.94.86.09-.67.35-1.12.63-1.38-2.22-.26-4.56-1.14-4.56-5.05 0-1.12.39-2.03 1.03-2.74-.1-.26-.45-1.3.1-2.71 0 0 .84-.27 2.75 1.05a9.3 9.3 0 0 1 2.5-.34c.85 0 1.71.12 2.5.34 1.91-1.32 2.75-1.05 2.75-1.05.55 1.41.2 2.45.1 2.71.64.71 1.03 1.62 1.03 2.74 0 3.92-2.34 4.78-4.57 5.04.36.32.68.94.68 1.9 0 1.37-.01 2.47-.01 2.81 0 .27.18.6.69.49A10.02 10.02 0 0 0 22 12.25C22 6.58 17.52 2 12 2z" />
        </svg>
    );
}

function LinkedInIcon() {
    return (
        <svg viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4">
            <path d="M4.98 3.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5zM3 9h4v12H3zM9 9h3.8v1.7h.05c.53-1 1.83-2.05 3.77-2.05 4.03 0 4.78 2.65 4.78 6.1V21h-4v-5.3c0-1.26-.02-2.9-1.77-2.9-1.77 0-2.04 1.38-2.04 2.8V21H9z" />
        </svg>
    );
}

const links = [
    { href: 'https://yash-munshi.vercel.app/', label: 'Portfolio', Icon: PortfolioIcon },
    { href: 'https://github.com/YashIsTheBest247', label: 'GitHub', Icon: GitHubIcon },
    { href: 'https://www.linkedin.com/in/yash-munshi-a0408b337/', label: 'LinkedIn', Icon: LinkedInIcon },
];

export function DevFooter() {
    return (
        <footer className="mt-8 border-t border-tint/10">
            <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-5 py-6 text-xs text-faint lg:px-8">
                <span>© {new Date().getFullYear()} Flux Studio</span>
                <div className="flex items-center gap-3">
                    <span className="uppercase tracking-widest">Connect with developer</span>
                    <div className="flex items-center gap-2">
                        {links.map(({ href, label, Icon }) => (
                            <a
                                key={label}
                                href={href}
                                target="_blank"
                                rel="noopener noreferrer"
                                aria-label={label}
                                title={label}
                                className="grid h-8 w-8 place-items-center rounded-full border border-tint/15 bg-tint/[0.06] text-txt transition-colors hover:bg-tint/[0.12]"
                            >
                                <Icon />
                            </a>
                        ))}
                    </div>
                </div>
            </div>
        </footer>
    );
}
