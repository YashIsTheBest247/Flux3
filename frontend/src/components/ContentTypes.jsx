import { useEffect, useState } from 'react';
import { activateProfile, getSources, listProfiles } from '../api/profiles.js';
import { artFor } from '../data/media.js';

/**
 * Choose the kind of channel this is.
 *
 * The profile is the only thing that differs between a gaming channel and a
 * markets channel: the trend sources scanned, the ranking weights, the voice
 * the script is written in, the visual vocabulary, the category and the publish
 * schedule. The pipeline underneath is identical.
 *
 * Presented as photographs rather than a select, because this is the one
 * decision the whole product hangs on and it deserves the space.
 */
export function ContentTypes({ onActivated, onReady }) {
    const [profiles, setProfiles] = useState([]);
    const [active, setActive] = useState('');
    const [busy, setBusy] = useState('');
    const [error, setError] = useState('');
    const [expanded, setExpanded] = useState('');
    const [sources, setSources] = useState(null);
    const [checking, setChecking] = useState(false);

    useEffect(() => {
        listProfiles()
            .then((data) => {
                setProfiles(data.profiles ?? []);
                setActive(data.active ?? '');
                onReady?.();
            })
            .catch((err) => setError(err.message || 'Could not load the channel types.'));
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    async function choose(profileId) {
        if (profileId === active || busy) return;
        setBusy(profileId);
        setError('');
        try {
            await activateProfile(profileId);
            setActive(profileId);
            setSources(null); // those belonged to the previous profile
            onActivated?.(profileId);
        } catch (err) {
            setError(err.message || 'Could not switch channel type.');
        } finally {
            setBusy('');
        }
    }

    async function checkSources() {
        setChecking(true);
        setError('');
        try {
            setSources(await getSources());
        } catch (err) {
            setError(err.message || 'Could not reach the trend sources.');
        } finally {
            setChecking(false);
        }
    }

    return (
        <section id="channel" className="px-3 sm:px-4">
            <div className="sheet mx-auto mt-6 w-full max-w-[1560px] px-5 py-16 sm:px-10 sm:py-20">
                <div className="flex flex-wrap items-end justify-between gap-5">
                    <div className="max-w-2xl">
                        <span className="eyebrow">Step one</span>
                        <h2 className="display reveal mt-3 text-display-md">
                            What kind of channel <span className="text-accentsoft">is this?</span>
                        </h2>
                        <p className="mt-4 max-w-lg text-sm leading-relaxed text-muted">
                            It decides where trends come from, how stories are ranked, the voice
                            the script is written in, and when it publishes.
                        </p>
                    </div>
                    <button
                        type="button"
                        onClick={checkSources}
                        disabled={checking}
                        className="btn-ghost"
                    >
                        {checking ? 'Checking…' : 'Check sources'}
                    </button>
                </div>

                {error ? (
                    <p className="mt-6 rounded-xl border border-red-500/25 bg-red-500/[0.07] px-4 py-3 text-sm text-red-700">
                        {error}
                    </p>
                ) : null}

                <div className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    {profiles.map((profile, index) => {
                        const isActive = profile.id === active;
                        const isOpen = expanded === profile.id;
                        return (
                            <article
                                key={profile.id}
                                style={{ transitionDelay: `${(index % 3) * 70}ms` }}
                                className={`reveal group relative flex flex-col overflow-hidden rounded-[1.25rem] border transition-all duration-300 ${
                                    isActive
                                        ? 'border-accent/50 shadow-[0_18px_50px_-30px_rgba(43,36,30,0.6)]'
                                        : 'border-tint/10 hover:border-tint/25'
                                }`}
                            >
                                <button
                                    type="button"
                                    onClick={() => choose(profile.id)}
                                    disabled={isActive || Boolean(busy)}
                                    className="media aspect-[16/10] w-full text-left"
                                    aria-label={`Use the ${profile.name} channel type`}
                                >
                                    <img src={artFor(profile.id)} alt="" />
                                    <span className="absolute inset-0 scrim" />
                                    {isActive ? (
                                        <span className="absolute right-4 top-4 rounded-full bg-accent px-3 py-1 text-[0.6rem] font-semibold uppercase tracking-[0.12em] text-white">
                                            Active
                                        </span>
                                    ) : (
                                        <span className="absolute right-4 top-4 rounded-full bg-white/90 px-3 py-1 text-[0.6rem] font-semibold uppercase tracking-[0.12em] text-[#12100E] opacity-0 transition-opacity duration-300 group-hover:opacity-100">
                                            {busy === profile.id ? 'Switching…' : 'Use this'}
                                        </span>
                                    )}
                                    <span className="absolute inset-x-0 bottom-0 p-4">
                                        <span className="display block text-lg text-white">{profile.name}</span>
                                        <span className="mt-0.5 block text-xs text-white/70">{profile.tagline}</span>
                                    </span>
                                </button>

                                <div className="flex flex-1 flex-col p-5">
                                    <dl className="space-y-1.5 text-xs text-faint">
                                        <Row label="Sources" value={(profile.sources ?? []).map((s) => s.type).join(', ') || 'none'} />
                                        <Row label="Length" value={`${profile.format?.duration}s`} />
                                        <Row
                                            label="Publishes"
                                            value={`${(profile.schedule?.hours ?? [])
                                                .map((h) => `${String(h).padStart(2, '0')}:00`)
                                                .join(', ')} ${profile.schedule?.timezone ?? ''}`}
                                        />
                                    </dl>

                                    {isOpen ? (
                                        <div className="mt-4 space-y-2 border-t border-tint/10 pt-4 text-xs leading-relaxed text-muted">
                                            <p><span className="text-faint">Voice.</span> {profile.persona?.voice}</p>
                                            <p><span className="text-faint">For.</span> {profile.persona?.audience}</p>
                                            <p><span className="text-faint">Hook.</span> {profile.persona?.hook_style}</p>
                                            {profile.persona?.avoid ? (
                                                <p className="text-faint">
                                                    <span className="text-red-500/80">Never.</span> {profile.persona.avoid}
                                                </p>
                                            ) : null}
                                        </div>
                                    ) : null}

                                    <button
                                        type="button"
                                        onClick={() => setExpanded(isOpen ? '' : profile.id)}
                                        aria-expanded={isOpen}
                                        className="mt-4 self-start text-[0.7rem] font-medium uppercase tracking-[0.12em] text-muted transition-colors hover:text-txt"
                                    >
                                        {isOpen ? 'Hide voice' : 'Read its voice'}
                                    </button>
                                </div>
                            </article>
                        );
                    })}
                </div>

                {/* Source health. Its own control because "found nothing" and
                    "Reddit is unreachable" look identical from the outside. */}
                {sources ? (
                    <div className="mt-8 rounded-[1.25rem] border border-tint/10 p-6 sm:p-8">
                        <h3 className="display text-lg">Where today’s ideas come from</h3>
                        <ul className="mt-5 divide-y divide-tint/10 border-t border-tint/10">
                            {sources.sources.map((source, index) => (
                                <li key={`${source.type}-${index}`} className="flex flex-wrap items-start gap-3 py-3">
                                    <span
                                        className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${
                                            source.error ? 'bg-red-500' : source.count ? 'bg-accent' : 'bg-faint'
                                        }`}
                                    />
                                    <span className="w-32 shrink-0 text-sm text-txt">{source.type}</span>
                                    <span className="w-20 shrink-0 text-sm text-muted">
                                        {source.count} item{source.count === 1 ? '' : 's'}
                                    </span>
                                    <span className="min-w-0 flex-1 truncate text-xs text-faint">
                                        {source.error || source.sample?.[0] || 'nothing returned'}
                                    </span>
                                </li>
                            ))}
                        </ul>
                    </div>
                ) : null}
            </div>
        </section>
    );
}

function Row({ label, value }) {
    return (
        <div className="flex justify-between gap-3">
            <dt>{label}</dt>
            <dd className="truncate text-right text-muted">{value}</dd>
        </div>
    );
}
