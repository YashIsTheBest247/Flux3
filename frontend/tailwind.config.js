import forms from '@tailwindcss/forms';

/** @type {import('tailwindcss').Config} */
export default {
    content: ['./index.html', './src/**/*.{js,jsx}'],
    theme: {
        extend: {
            colors: {
                // All theme-aware, backed by CSS variables (see index.css).
                panel: 'rgb(var(--panel) / <alpha-value>)',
                panel2: 'rgb(var(--panel-2) / <alpha-value>)',
                txt: 'rgb(var(--fg) / <alpha-value>)',
                muted: 'rgb(var(--muted) / <alpha-value>)',
                faint: 'rgb(var(--faint) / <alpha-value>)',
                tint: 'rgb(var(--tint) / <alpha-value>)',
                accent: 'rgb(var(--accent) / <alpha-value>)',
                primary: 'rgb(var(--primary) / <alpha-value>)',
                onprimary: 'rgb(var(--on-primary) / <alpha-value>)',
            },
            fontFamily: {
                display: ['"Space Grotesk"', 'system-ui', 'sans-serif'],
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
            borderRadius: {
                '4xl': '2rem',
            },
            boxShadow: {
                glow: 'var(--glow-shadow)',
                card: '0 24px 60px -30px rgba(0, 0, 0, 0.85)',
            },
            backgroundImage: {
                'accent-grad': 'var(--accent-grad)',
            },
            keyframes: {
                floaty: {
                    '0%, 100%': { transform: 'translateY(0)' },
                    '50%': { transform: 'translateY(-8px)' },
                },
                beam: {
                    '0%': { opacity: '0', transform: 'translateY(-28px) scaleY(0.6)' },
                    '25%': { opacity: '0.9' },
                    '70%': { opacity: '0.5' },
                    '100%': { opacity: '0', transform: 'translateY(26px) scaleY(1)' },
                },
                marquee: {
                    from: { transform: 'translateX(0)' },
                    to: { transform: 'translateX(-50%)' },
                },
                fadeup: {
                    '0%': { opacity: '0', transform: 'translateY(12px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
            },
            animation: {
                floaty: 'floaty 6s ease-in-out infinite',
                beam: 'beam 5s ease-in-out infinite',
                marquee: 'marquee 30s linear infinite',
                fadeup: 'fadeup 0.6s ease',
            },
        },
    },
    plugins: [forms],
};
