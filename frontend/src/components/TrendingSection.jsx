import { useCallback, useEffect, useState } from 'react';
import { fetchTrending } from '../api/trends.js';

const COLLAPSED_COUNT = 3;

function RefreshIcon({ spinning }) {
    return (
        <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            className={`h-4 w-4 transition-transform ${spinning ? 'animate-spin' : 'group-hover:rotate-90'}`}
        >
            <path d="M21 12a9 9 0 1 1-2.64-6.36M21 3v5h-5" />
        </svg>
    );
}

function SkeletonCard({ index }) {
    return (
        <div
            className="glass animate-fadeup p-5"
            style={{ animationDelay: `${index * 50}ms`, animationFillMode: 'backwards' }}
        >
            <div className="h-3 w-20 animate-pulse rounded bg-tint/10" />
            <div className="mt-4 h-4 w-full animate-pulse rounded bg-tint/10" />
            <div className="mt-2 h-4 w-2/3 animate-pulse rounded bg-tint/10" />
            <div className="mt-6 h-1.5 w-full animate-pulse rounded-full bg-tint/10" />
        </div>
    );
}

function TrendCard({ article, index, onGenerate, isGenerating }) {
    const scorePct = Math.round((article.score ?? 0) * 100);
    const keywords = (article.keywords ?? []).slice(0, 4);
    const [revealed, setRevealed] = useState(false);

    // Animate the score bar from 0 -> score on mount.
    useEffect(() => {
        const t = window.setTimeout(() => setRevealed(true), 80);
        return () => window.clearTimeout(t);
    }, []);

    return (
        <div
            className="group glass relative flex animate-fadeup flex-col gap-3 overflow-hidden p-5 transition-all duration-300 ease-out hover:-translate-y-1.5 hover:border-tint/30 hover:shadow-card"
            style={{ animationDelay: `${(index % COLLAPSED_COUNT) * 70}ms`, animationFillMode: 'backwards' }}
        >
            {/* sweep glow on hover */}
            <span className="pointer-events-none absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/[0.04] to-transparent transition-transform duration-700 group-hover:translate-x-full" />

            <div className="flex items-center justify-between gap-2">
                <span className="grid h-7 w-7 place-items-center rounded-full border border-tint/15 bg-tint/[0.06] text-xs font-semibold text-txt">
                    {index + 1}
                </span>
                <span className="chip max-w-[60%] truncate text-[0.65rem]">{article.source}</span>
            </div>

            <a
                href={article.link}
                target="_blank"
                rel="noopener noreferrer"
                className="line-clamp-3 text-sm font-medium leading-snug text-txt transition-colors hover:text-accent"
            >
                {article.title}
            </a>

            {keywords.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                    {keywords.map((kw) => (
                        <span
                            key={kw}
                            className="rounded-full border border-tint/10 bg-tint/[0.04] px-2 py-0.5 text-[0.6rem] text-muted"
                        >
                            {kw}
                        </span>
                    ))}
                </div>
            )}

            <div className="mt-auto pt-2">
                <div className="mb-1 flex items-center justify-between text-[0.65rem] text-faint">
                    <span className="uppercase tracking-widest">Trend score</span>
                    <span className="font-semibold text-txt">{scorePct}</span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-tint/10">
                    <div
                        className="h-full rounded-full bg-accent transition-all duration-[900ms] ease-out"
                        style={{ width: revealed ? `${scorePct}%` : '0%' }}
                    />
                </div>
            </div>

            <div className="flex items-center justify-between gap-2 pt-1">
                <a
                    href={article.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs font-medium text-muted transition-colors hover:text-txt"
                >
                    Read on ET ↗
                </a>
                <button
                    type="button"
                    onClick={() => onGenerate?.(article)}
                    disabled={isGenerating}
                    className="btn-light px-3 py-1.5 text-xs disabled:opacity-60"
                >
                    Generate video
                </button>
            </div>
        </div>
    );
}

export function TrendingSection({ onGenerate, isGenerating }) {
    const [articles, setArticles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [expanded, setExpanded] = useState(false);

    const load = useCallback(async () => {
        setLoading(true);
        setError('');
        try {
            const data = await fetchTrending(9);
            setArticles(data);
        } catch (err) {
            setError(err.message || 'Could not load trending articles.');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        void load();
    }, [load]);

    const visible = expanded ? articles : articles.slice(0, COLLAPSED_COUNT);
    const hiddenCount = Math.max(0, articles.length - COLLAPSED_COUNT);

    return (
        <section id="trending" className="mx-auto max-w-7xl px-5 py-12 lg:px-8">
            <div className="mb-10 flex flex-wrap items-end justify-between gap-4">
                <div>
                    <span className="eyebrow">Live feed</span>
                    <h2 className="display mt-2 text-3xl font-semibold sm:text-4xl">
                        Trending on Economic Times
                    </h2>
                    <p className="mt-2 max-w-xl text-sm text-muted">
                        Ranked by recency and cross-feed momentum. Hit “Generate video” to turn a
                        headline into a short.
                    </p>
                </div>
                <button
                    type="button"
                    onClick={load}
                    disabled={loading}
                    className="group flex items-center gap-2 rounded-full border border-tint/15 bg-tint/[0.04] px-4 py-2 text-sm font-medium text-txt transition-colors hover:bg-tint/[0.1] disabled:opacity-60"
                >
                    <RefreshIcon spinning={loading} />
                    Refresh
                </button>
            </div>

            {error ? (
                <div className="glass animate-fadeup p-8 text-center">
                    <p className="text-sm text-red-300">{error}</p>
                    <button
                        type="button"
                        onClick={load}
                        className="btn-light mt-4 inline-flex px-5 py-2 text-sm"
                    >
                        Try again
                    </button>
                </div>
            ) : (
                <>
                    <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
                        {loading
                            ? Array.from({ length: COLLAPSED_COUNT }).map((_, i) => (
                                  <SkeletonCard key={i} index={i} />
                              ))
                            : visible.map((article, i) => (
                                  <TrendCard
                                      key={article.link || i}
                                      article={article}
                                      index={i}
                                      onGenerate={onGenerate}
                                      isGenerating={isGenerating}
                                  />
                              ))}

                        {!loading && articles.length === 0 && (
                            <div className="glass col-span-full animate-fadeup p-8 text-center text-sm text-muted">
                                No fresh trending articles right now. Check back soon.
                            </div>
                        )}
                    </div>

                    {!loading && hiddenCount > 0 && (
                        <div className="mt-8 flex justify-center">
                            <button
                                type="button"
                                onClick={() => setExpanded((v) => !v)}
                                className="group flex items-center gap-2 rounded-full border border-tint/15 bg-tint/[0.04] px-6 py-2.5 text-sm font-medium text-txt transition-all hover:bg-tint/[0.1]"
                            >
                                {expanded ? 'Show less' : `Show ${hiddenCount} more`}
                                <svg
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="2"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    className={`h-4 w-4 transition-transform duration-300 ${expanded ? 'rotate-180' : ''}`}
                                >
                                    <path d="m6 9 6 6 6-6" />
                                </svg>
                            </button>
                        </div>
                    )}
                </>
            )}
        </section>
    );
}
