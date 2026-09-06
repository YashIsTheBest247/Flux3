const base = {
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.6,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    viewBox: '0 0 24 24',
};

const marks = {
    YouTube: (props) => (
        <svg {...base} {...props}>
            <rect x="3" y="6" width="18" height="12" rx="3" />
            <path d="M11 9.5v5l4-2.5z" fill="currentColor" stroke="none" />
        </svg>
    ),
    KokoroTTS: (props) => (
        <svg {...base} {...props}>
            <path d="M4 12h2l2-5 3 12 3-14 2 7h4" />
        </svg>
    ),
    Render: (props) => (
        <svg {...base} {...props}>
            <path d="M12 3 4 7.5v9L12 21l8-4.5v-9z" />
            <path d="M12 12 4 7.5M12 12l8-4.5M12 12v9" />
        </svg>
    ),
    Vercel: (props) => (
        <svg {...base} {...props}>
            <path d="M12 4 21 19H3z" fill="currentColor" stroke="none" />
        </svg>
    ),
    Pexels: (props) => (
        <svg {...base} {...props}>
            <rect x="4" y="4" width="16" height="16" rx="3" />
            <path d="M10 16V9h3a2.5 2.5 0 0 1 0 5h-3" />
        </svg>
    ),
    Gemini: (props) => (
        <svg {...base} {...props}>
            <path
                d="M12 2c.6 5.4 4.6 9.4 10 10-5.4.6-9.4 4.6-10 10-.6-5.4-4.6-9.4-10-10 5.4-.6 9.4-4.6 10-10z"
                fill="currentColor"
                stroke="none"
            />
        </svg>
    ),
    Pillow: (props) => (
        <svg {...base} {...props}>
            <rect x="3" y="4" width="18" height="16" rx="2" />
            <circle cx="8.5" cy="9.5" r="1.5" />
            <path d="m4 18 5-5 4 4 3-3 4 4" />
        </svg>
    ),
    Subtitles: (props) => (
        <svg {...base} {...props}>
            <rect x="3" y="5" width="18" height="14" rx="2" />
            <path d="M7 12h4M7 15h7M14 12h3" />
        </svg>
    ),
};

export function BrandIcon({ name, className }) {
    const Mark = marks[name];
    if (!Mark) return null;
    return <Mark className={className} />;
}
