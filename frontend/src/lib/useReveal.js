import { useEffect } from 'react';

/**
 * Reveal `.reveal` elements as they enter the viewport.
 *
 * One observer for the whole document rather than one per component, and each
 * element is unobserved once it has appeared - the animation is a first
 * impression, not a state, and re-running it on every scroll past is the thing
 * that makes these effects feel cheap.
 *
 * Elements are re-scanned whenever `deps` change, because most of this page's
 * content arrives from the API after the first paint.
 */
export function useReveal(deps = []) {
    useEffect(() => {
        const nodes = Array.from(document.querySelectorAll('.reveal:not(.is-in)'));
        if (!nodes.length) return undefined;

        // No IntersectionObserver, or the visitor asked for less motion: show
        // everything immediately rather than leaving the page blank.
        const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
        if (reduced || typeof IntersectionObserver === 'undefined') {
            nodes.forEach((node) => node.classList.add('is-in'));
            return undefined;
        }

        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (!entry.isIntersecting) return;
                    entry.target.classList.add('is-in');
                    observer.unobserve(entry.target);
                });
            },
            // A little before the element arrives, so it is already settled by
            // the time it is properly in view.
            { rootMargin: '0px 0px -12% 0px', threshold: 0.08 },
        );

        nodes.forEach((node) => observer.observe(node));
        return () => observer.disconnect();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, deps);
}
