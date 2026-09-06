import { useCallback, useEffect, useState } from 'react';
import {
    disconnectYouTube,
    getPublishing,
    openYouTubeConsent,
    saveCredentials,
    setPublishMode,
    startYouTubeAuth,
} from '../api/connect.js';
import { media } from '../data/media.js';
import { YouTubeMark } from './Visuals.jsx';

/**
 * Where finished videos go.
 *
 * Two states, and the default matters: a first-time visitor publishes to the
 * channel this deployment owns and needs to configure nothing at all. Turning
 * that off is what reveals the OAuth fields — asking for a Google Cloud project
 * up front is the step most people would bounce off.
 *
 * Only the OAuth client is asked for. The model and stock-library keys are the
 * operator's and come from the environment; there is no form for them here.
 */
export function PublishingSection({ onChanged }) {
    const [state, setState] = useState(null);
    const [drafts, setDrafts] = useState({});
    const [busy, setBusy] = useState('');
    const [error, setError] = useState('');
    const [notice, setNotice] = useState('');

    const refresh = useCallback(async () => {
        try {
            setState(await getPublishing());
        } catch (err) {
            setError(err.message || 'Could not load your publishing settings.');
        }
    }, []);

    useEffect(() => {
        refresh();
    }, [refresh]);

    const mode = state?.mode ?? 'default';
    const own = mode === 'own';
    const dirty = Object.keys(drafts).length > 0;

    async function choose(nextMode) {
        if (nextMode === mode || busy) return;
        setBusy('mode');
        setError('');
        setNotice('');
        try {
            setState(await setPublishMode(nextMode));
            onChanged?.();
        } catch (err) {
            setError(err.message || 'Could not switch the publishing target.');
        } finally {
            setBusy('');
        }
    }

    async function saveClient() {
        if (!dirty) return;
        setBusy('save');
        setError('');
        try {
            await saveCredentials(drafts);
            setDrafts({});
            await refresh();
            setNotice('Saved. Now connect the channel.');
        } catch (err) {
            setError(err.message || 'Could not save.');
        } finally {
            setBusy('');
        }
    }

    async function connect() {
        setBusy('connect');
        setError('');
        setNotice('');
        try {
            const { authorize_url: url } = await startYouTubeAuth();
            const outcome = await openYouTubeConsent(url);
            await refresh();
            onChanged?.();
            if (outcome.ok) setNotice('Channel connected.');
            else if (outcome.ok === false && !outcome.blocked) {
                setError('The connection was not completed.');
            }
        } catch (err) {
            setError(err.message || 'Could not start the connection.');
        } finally {
            setBusy('');
        }
    }

    async function disconnect() {
        setBusy('connect');
        try {
            await disconnectYouTube();
            await refresh();
            onChanged?.();
            setNotice('Disconnected, and the token was revoked at Google.');
        } catch (err) {
            setError(err.message || 'Could not disconnect.');
        } finally {
            setBusy('');
        }
    }

    return (
        <section id="publishing" className="px-3 sm:px-4">
            <div className="sheet mx-auto mt-6 w-full max-w-[1560px] px-5 py-16 sm:px-10 sm:py-20">
                <div className="flex flex-wrap items-end justify-between gap-4">
                    <div className="max-w-2xl">
                        <span className="eyebrow">Step two</span>
                        <h2 className="display reveal mt-3 text-display-md">
                            Where does it <span className="text-accentsoft">publish?</span>
                        </h2>
                        <p className="mt-4 max-w-lg text-sm leading-relaxed text-muted">
                            By default everything lands on our demo channel, so you can try the
                            whole pipeline without setting anything up. Switch it off and your
                            videos go to your own channel instead.
                        </p>
                    </div>
                </div>

                {error ? <Banner tone="error">{error}</Banner> : null}
                {notice ? <Banner tone="ok">{notice}</Banner> : null}

                <div className="mt-10 grid gap-3 lg:grid-cols-2">
                    {/* ---------------- default ---------------- */}
                    <button
                        type="button"
                        onClick={() => choose('default')}
                        disabled={Boolean(busy)}
                        className={`reveal relative overflow-hidden rounded-[1.25rem] border p-6 text-left transition-all sm:p-8 ${
                            !own
                                ? 'border-accent/45 bg-accent/[0.05]'
                                : 'border-tint/10 hover:border-tint/25'
                        }`}
                    >
                        <div className="flex items-start justify-between gap-4">
                            <span className="grid h-11 w-11 place-items-center rounded-full bg-panel2">
                                <YouTubeMark className="h-5 w-5 text-accent" />
                            </span>
                            <Radio on={!own} />
                        </div>
                        <h3 className="display mt-5 text-xl">Our channel</h3>
                        <p className="mt-2 text-sm leading-relaxed text-muted">
                            Publishes to{' '}
                            <span className="text-txt">{state?.default_channel_title || 'the demo channel'}</span>.
                            Nothing to configure — this works the moment you pick a channel type.
                        </p>
                        {state && !state.default_available ? (
                            <p className="mt-3 text-xs leading-relaxed text-amber-600">
                                This deployment has no default channel configured yet, so
                                publishing will fail until one is set or you use your own.
                            </p>
                        ) : null}
                    </button>

                    {/* ---------------- own ---------------- */}
                    <button
                        type="button"
                        onClick={() => choose('own')}
                        disabled={Boolean(busy)}
                        className={`reveal relative overflow-hidden rounded-[1.25rem] border p-6 text-left transition-all sm:p-8 ${
                            own ? 'border-accent/45 bg-accent/[0.05]' : 'border-tint/10 hover:border-tint/25'
                        }`}
                    >
                        <div className="flex items-start justify-between gap-4">
                            <span className="media h-11 w-11 shrink-0 rounded-full">
                                <img src={media.gear} alt="" />
                            </span>
                            <Radio on={own} />
                        </div>
                        <h3 className="display mt-5 text-xl">My own channel</h3>
                        <p className="mt-2 text-sm leading-relaxed text-muted">
                            {state?.connected && own
                                ? `Connected to ${state.channel_title || 'your channel'}.`
                                : 'Uploads land on your account and use your own quota. Needs a Google Cloud OAuth client.'}
                        </p>
                    </button>
                </div>

                {/* ---------------- own-channel setup ---------------- */}
                {own ? (
                    <div className="mt-3 grid gap-3 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
                        <div className="rounded-[1.25rem] border border-tint/10 p-6 sm:p-8">
                            <h3 className="display text-lg">Your OAuth client</h3>
                            <div className="mt-6 space-y-6">
                                {(state?.fields ?? []).map((field) => (
                                    <Field
                                        key={field.key}
                                        field={field}
                                        value={drafts[field.key]}
                                        onChange={(value) =>
                                            setDrafts((current) => ({ ...current, [field.key]: value }))
                                        }
                                    />
                                ))}
                            </div>

                            <div className="mt-7 flex flex-wrap gap-2">
                                <button
                                    type="button"
                                    onClick={saveClient}
                                    disabled={!dirty || Boolean(busy)}
                                    className="btn-light"
                                >
                                    {busy === 'save' ? 'Saving…' : 'Save client'}
                                </button>
                                {state?.connected ? (
                                    <button
                                        type="button"
                                        onClick={disconnect}
                                        disabled={Boolean(busy)}
                                        className="btn-ghost"
                                    >
                                        Disconnect
                                    </button>
                                ) : (
                                    <button
                                        type="button"
                                        onClick={connect}
                                        disabled={Boolean(busy) || !state?.client_configured}
                                        className="btn-accent"
                                    >
                                        {busy === 'connect' ? 'Waiting for Google…' : 'Connect channel'}
                                    </button>
                                )}
                            </div>
                        </div>

                        <div className="glass-strong rounded-[1.25rem] p-6 sm:p-8">
                            <h4 className="display text-base">Setting it up</h4>
                            <ol className="mt-4 space-y-3 text-xs leading-relaxed text-muted">
                                <li>
                                    <span className="text-faint">1.</span> In Google Cloud, enable the{' '}
                                    <span className="text-txt">YouTube Data API v3</span>.
                                </li>
                                <li>
                                    <span className="text-faint">2.</span> Create an OAuth client of type{' '}
                                    <span className="text-txt">Web application</span>.
                                </li>
                                <li>
                                    <span className="text-faint">3.</span> Add this redirect URI exactly.
                                    Google compares it character for character, and a mismatch here
                                    is the usual reason connecting fails:
                                    <code className="mt-2 block break-all rounded-lg border border-tint/10 bg-panel px-3 py-2 text-[0.68rem] text-txt">
                                        {state?.redirect_uri || '…'}
                                    </code>
                                </li>
                                <li>
                                    <span className="text-faint">4.</span> Paste the ID and secret, save,
                                    then connect.
                                </li>
                            </ol>
                            <p className="mt-5 border-t border-tint/10 pt-4 text-[0.7rem] leading-relaxed text-faint">
                                While your consent screen is in Testing, add your own Google
                                account under Test users or Google refuses the sign-in.
                            </p>
                        </div>
                    </div>
                ) : null}
            </div>
        </section>
    );
}

function Radio({ on }) {
    return (
        <span
            className={`grid h-5 w-5 shrink-0 place-items-center rounded-full border transition-colors ${
                on ? 'border-accent bg-accent' : 'border-tint/25'
            }`}
        >
            {on ? <span className="h-1.5 w-1.5 rounded-full bg-white" /> : null}
        </span>
    );
}

function Banner({ tone, children }) {
    const styles =
        tone === 'error'
            ? 'border-red-500/25 bg-red-500/[0.07] text-red-700'
            : 'border-accent/30 bg-accent/[0.07] text-accent';
    return <p className={`mt-6 rounded-xl border px-4 py-3 text-sm ${styles}`}>{children}</p>;
}

function Field({ field, value, onChange }) {
    const editing = value !== undefined;
    return (
        <label className="block">
            <span className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-medium text-txt">{field.label}</span>
                {field.configured && !editing ? (
                    <span className="chip py-0.5 text-[0.65rem]">
                        {field.secret ? field.hint : 'set'}
                    </span>
                ) : null}
            </span>
            <input
                type={field.secret ? 'password' : 'text'}
                value={editing ? value : ''}
                onChange={(event) => onChange(event.target.value)}
                placeholder={field.configured ? 'Saved — type to replace' : field.placeholder}
                autoComplete="off"
                spellCheck="false"
                className="field-input mt-2 text-sm"
            />
            <span className="mt-2 block text-xs leading-relaxed text-faint">
                {field.help}
                {field.docs_url ? (
                    <>
                        {' '}
                        <a
                            href={field.docs_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-muted underline underline-offset-2 hover:text-txt"
                        >
                            Open console
                        </a>
                    </>
                ) : null}
            </span>
        </label>
    );
}
