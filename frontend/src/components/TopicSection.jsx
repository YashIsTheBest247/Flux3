import { useState } from 'react';
import { media } from '../data/media.js';

const DURATIONS = [30, 45, 60, 90];

/**
 * Make a video about anything you type.
 *
 * The trend pipeline answers "what should I post today?". This answers the
 * other half of the question — you already know what you want to say, you just
 * do not want to spend the evening producing it. Same pipeline, same signed
 * output, same publish path; the only difference is that the topic comes from
 * a text box instead of a ranked feed.
 */
export function TopicSection({ onGenerate, isGenerating, channelReady, channelTitle }) {
    const [topic, setTopic] = useState('');
    const [keyPoints, setKeyPoints] = useState('');
    const [duration, setDuration] = useState(60);
    const [autoPublish, setAutoPublish] = useState(false);
    const [privacy, setPrivacy] = useState('unlisted');
    const [error, setError] = useState('');
    const [notice, setNotice] = useState('');

    const trimmed = topic.trim();
    const tooLong = trimmed.length > 200;
    const ready = trimmed.length >= 3 && !tooLong && !isGenerating;

    async function submit(event) {
        event.preventDefault();
        if (!ready) return;
        setError('');
        setNotice('');
        try {
            await onGenerate?.({
                topic: trimmed,
                duration,
                keyPoints,
                autoPublish: autoPublish && channelReady,
                privacy,
            });
            setNotice(
                autoPublish && channelReady
                    ? `Making it now — it will publish to ${channelTitle || 'your channel'} as ${privacy}.`
                    : 'Making it now. It will land in your library when it is done.',
            );
        } catch (err) {
            setError(err.message || 'Could not start the render.');
        }
    }

    return (
        <section id="create" className="px-3 sm:px-4">
            <div className="sheet mx-auto mt-6 w-full max-w-[1560px] overflow-hidden">
                <div className="grid gap-0 lg:grid-cols-[minmax(0,1fr)_minmax(0,0.85fr)]">
                    {/* -------------------------------- the form -------------------------------- */}
                    <form onSubmit={submit} className="p-6 sm:p-10">
                        <span className="eyebrow">Know what you want to say?</span>
                        <h2 className="display reveal mt-3 text-display-md">
                            Type it. <span className="text-accentsoft">We&rsquo;ll make it.</span>
                        </h2>
                        <p className="mt-4 max-w-lg text-sm leading-relaxed text-muted">
                            One line is enough. Flux writes the script in your channel&rsquo;s
                            voice, finds the visuals, narrates it, burns the captions and
                            publishes it.
                        </p>

                        <label className="mt-8 block">
                            <span className="text-sm font-medium text-txt">
                                What should the video be about?
                            </span>
                            <textarea
                                value={topic}
                                onChange={(event) => setTopic(event.target.value)}
                                rows={2}
                                maxLength={240}
                                placeholder="Why India's UPI system handles more transactions than Visa"
                                className="field-input mt-2 resize-none text-sm"
                            />
                            <span className="mt-1.5 flex justify-between text-xs">
                                <span className="text-faint">
                                    Be specific. &ldquo;AI&rdquo; makes a vague video; a claim with a
                                    number in it makes a good one.
                                </span>
                                <span className={tooLong ? 'text-red-600' : 'text-faint'}>
                                    {trimmed.length}/200
                                </span>
                            </span>
                        </label>

                        <label className="mt-6 block">
                            <span className="text-sm font-medium text-txt">
                                Points it must cover <span className="text-faint">— optional</span>
                            </span>
                            <textarea
                                value={keyPoints}
                                onChange={(event) => setKeyPoints(event.target.value)}
                                rows={3}
                                placeholder={'One per line, or comma separated.\nVolume overtook Visa in 2023\nZero merchant fees'}
                                className="field-input mt-2 resize-none text-sm"
                            />
                            <span className="mt-1.5 block text-xs text-faint">
                                Leave it empty and the model decides what matters.
                            </span>
                        </label>

                        <div className="mt-6">
                            <span className="eyebrow">Length</span>
                            <div className="mt-2 flex flex-wrap gap-2">
                                {DURATIONS.map((seconds) => (
                                    <button
                                        key={seconds}
                                        type="button"
                                        onClick={() => setDuration(seconds)}
                                        className={`rounded-full border px-4 py-1.5 text-xs transition-colors ${
                                            duration === seconds
                                                ? 'border-accent/50 bg-accent/10 text-accent'
                                                : 'border-tint/15 text-muted hover:text-txt'
                                        }`}
                                    >
                                        {seconds}s
                                    </button>
                                ))}
                            </div>
                        </div>

                        <label className="mt-7 flex items-start gap-3">
                            <input
                                type="checkbox"
                                checked={autoPublish && channelReady}
                                onChange={(event) => setAutoPublish(event.target.checked)}
                                disabled={!channelReady}
                                className="mt-1 rounded border-tint/25 bg-panel2 text-accent focus:ring-0 disabled:opacity-40"
                            />
                            <span>
                                <span className="text-sm text-txt">Publish it when it&rsquo;s done</span>
                                <span className="mt-0.5 block text-xs text-faint">
                                    {channelReady
                                        ? `Uploads to ${channelTitle || 'your connected channel'}.`
                                        : 'No channel connected — it will be saved to your library instead.'}
                                </span>
                            </span>
                        </label>

                        {autoPublish && channelReady ? (
                            <div className="mt-4 pl-7">
                                <span className="eyebrow">Visibility</span>
                                <div className="mt-2 flex flex-wrap gap-2">
                                    {['private', 'unlisted', 'public'].map((option) => (
                                        <button
                                            key={option}
                                            type="button"
                                            onClick={() => setPrivacy(option)}
                                            className={`rounded-full border px-4 py-1.5 text-xs capitalize transition-colors ${
                                                privacy === option
                                                    ? 'border-accent/50 bg-accent/10 text-accent'
                                                    : 'border-tint/15 text-muted hover:text-txt'
                                            }`}
                                        >
                                            {option}
                                        </button>
                                    ))}
                                </div>
                                {privacy === 'private' ? (
                                    <p className="mt-2 text-xs leading-relaxed text-faint">
                                        A private video is only visible to you, and its public
                                        link reads &ldquo;Video unavailable&rdquo;. Choose unlisted
                                        if you want to share it.
                                    </p>
                                ) : null}
                            </div>
                        ) : null}

                        <button type="submit" disabled={!ready} className="btn-accent mt-8 w-full">
                            {isGenerating ? 'A render is already running…' : 'Make this video'}
                        </button>

                        {error ? (
                            <p className="mt-4 rounded-xl border border-red-500/25 bg-red-500/[0.07] px-4 py-3 text-sm text-red-700">
                                {error}
                            </p>
                        ) : null}
                        {notice ? (
                            <p className="mt-4 rounded-xl border border-accent/30 bg-accent/[0.07] px-4 py-3 text-sm text-accent">
                                {notice}
                            </p>
                        ) : null}
                    </form>

                    {/* -------------------------------- the aside -------------------------------- */}
                    <aside className="relative hidden lg:block">
                        <div className="media absolute inset-0">
                            <img src={media.writing} alt="" />
                            <span className="absolute inset-0 scrim" />
                        </div>
                        <div className="relative flex h-full flex-col justify-end p-10">
                            <span className="text-[0.68rem] uppercase tracking-[0.2em] text-white/60">
                                What happens next
                            </span>
                            <ol className="mt-4 space-y-3 text-sm text-white/85">
                                {[
                                    'The script gets written in your channel’s voice',
                                    'Visuals are found for every scene',
                                    'It is narrated and the captions are timed',
                                    'Assembled, signed, and stored in your bucket',
                                    'Published, if you asked for that',
                                ].map((line, index) => (
                                    <li key={line} className="flex gap-3">
                                        <span className="font-mono text-xs text-white/45">
                                            {String(index + 1).padStart(2, '0')}
                                        </span>
                                        {line}
                                    </li>
                                ))}
                            </ol>
                            <p className="mt-6 text-xs leading-relaxed text-white/50">
                                About two minutes. Watch it happen in the pipeline below.
                            </p>
                        </div>
                    </aside>
                </div>
            </div>
        </section>
    );
}
