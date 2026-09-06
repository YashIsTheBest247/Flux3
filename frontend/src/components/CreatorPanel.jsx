import { useState } from 'react';
import { durationOptions, formatOptions, privacyOptions } from '../data/options.js';

const initialForm = {
    format: 'video',
    topic: '',
    duration: 60,
    keyPoints: '',
    autoPublish: true,
    privacy: 'unlisted',
};

export function CreatorPanel({ onGenerate, isGenerating }) {
    const [form, setForm] = useState(initialForm);
    const [error, setError] = useState('');

    function update(field, value) {
        setForm((current) => ({ ...current, [field]: value }));
    }

    async function handleSubmit(event) {
        event.preventDefault();
        setError('');

        if (!form.topic.trim()) {
            setError('Add a topic before generating.');
            return;
        }

        try {
            await onGenerate(form);
        } catch (submitError) {
            setError(submitError.message || 'Generation request failed.');
        }
    }

    return (
        <section id="creator" className="mx-auto max-w-7xl px-5 py-20 lg:px-8">
            <div className="mb-10 flex flex-wrap items-end justify-between gap-4">
                <div>
                    <span className="eyebrow">Studio</span>
                    <h2 className="display mt-2 text-3xl font-semibold sm:text-4xl">
                        Create a video
                    </h2>
                </div>
                <span className="chip">~5–10 min · publish optional</span>
            </div>

            <form onSubmit={handleSubmit} className="grid gap-5 lg:grid-cols-12">
                {/* Content */}
                <div className="glass flex flex-col gap-8 p-6 lg:col-span-8 lg:p-8">
                    <Field label="Format">
                        <div className="grid gap-3 sm:grid-cols-2">
                            {formatOptions.map((option) => {
                                const active = form.format === option.value;
                                return (
                                    <button
                                        key={option.value}
                                        type="button"
                                        onClick={() => update('format', option.value)}
                                        className={`flex flex-col items-start gap-1 rounded-xl border p-4 text-left transition-all ${
                                            active
                                                ? 'border-accent/40 bg-accent/10 shadow-glow'
                                                : 'border-tint/10 bg-tint/[0.03] hover:border-tint/20'
                                        }`}
                                    >
                                        <span className="text-sm font-semibold text-txt">
                                            {option.label}
                                        </span>
                                        <span className="text-xs text-muted">{option.hint}</span>
                                    </button>
                                );
                            })}
                        </div>
                    </Field>

                    <Field label="Topic">
                        <input
                            type="text"
                            value={form.topic}
                            onChange={(event) => update('topic', event.target.value)}
                            placeholder="e.g. The architecture of photosynthesis"
                            className="field-input display text-lg"
                        />
                    </Field>

                    <Field label="Duration">
                        <div className="flex flex-wrap gap-2">
                            {durationOptions.map((option) => {
                                const active = form.duration === option.value;
                                return (
                                    <button
                                        key={option.value}
                                        type="button"
                                        onClick={() => update('duration', option.value)}
                                        className={`rounded-full border px-4 py-2 text-sm font-medium transition-all ${
                                            active
                                                ? 'border-transparent bg-primary text-onprimary'
                                                : 'border-tint/10 bg-tint/[0.03] text-muted hover:text-txt'
                                        }`}
                                    >
                                        {option.label}
                                    </button>
                                );
                            })}
                        </div>
                    </Field>

                    <Field label="Key points" hint="Optional">
                        <textarea
                            value={form.keyPoints}
                            onChange={(event) => update('keyPoints', event.target.value)}
                            rows={4}
                            placeholder="Tone, data points, anything you want included. One per line."
                            className="field-input resize-none"
                        />
                    </Field>
                </div>

                {/* Publish */}
                <div className="glass-strong flex flex-col gap-8 p-6 lg:col-span-4 lg:p-8">
                    <Field label="Auto-publish to YouTube">
                        <button
                            type="button"
                            role="switch"
                            aria-checked={form.autoPublish}
                            onClick={() => update('autoPublish', !form.autoPublish)}
                            className={`flex items-center justify-between gap-3 rounded-xl border px-4 py-3 text-left transition-all ${
                                form.autoPublish
                                    ? 'border-accent/40 bg-accent/10'
                                    : 'border-tint/10 bg-tint/[0.03] hover:border-tint/20'
                            }`}
                        >
                            <span className="flex flex-col">
                                <span className="text-sm font-semibold text-txt">
                                    {form.autoPublish ? 'Enabled' : 'Disabled'}
                                </span>
                                <span className="text-xs text-muted">
                                    {form.autoPublish
                                        ? 'Uploads to YouTube when the render finishes'
                                        : 'Render stays in your library only'}
                                </span>
                            </span>
                            <span
                                className={`relative h-6 w-11 shrink-0 rounded-full transition-colors ${
                                    form.autoPublish ? 'bg-accent' : 'bg-tint/20'
                                }`}
                            >
                                <span
                                    className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
                                        form.autoPublish ? 'translate-x-[22px]' : 'translate-x-0.5'
                                    }`}
                                />
                            </span>
                        </button>
                    </Field>

                    {form.autoPublish && (
                        <Field label="Visibility">
                            <div className="grid grid-cols-2 gap-2">
                                {privacyOptions.map((option) => {
                                    const active = form.privacy === option.value;
                                    return (
                                        <button
                                            key={option.value}
                                            type="button"
                                            onClick={() => update('privacy', option.value)}
                                            className={`flex flex-col items-start gap-0.5 rounded-xl border px-4 py-3 text-left transition-all ${
                                                active
                                                    ? 'border-accent/40 bg-accent/10 text-txt'
                                                    : 'border-tint/10 bg-tint/[0.03] text-muted hover:text-txt'
                                            }`}
                                        >
                                            <span className="text-sm font-semibold text-txt">
                                                {option.label}
                                            </span>
                                            <span className="text-xs text-muted">{option.hint}</span>
                                        </button>
                                    );
                                })}
                            </div>
                        </Field>
                    )}

                    <div className="mt-auto flex flex-col gap-3">
                        {error && (
                            <p className="rounded-xl border border-red-400/30 bg-red-500/10 px-3 py-2 text-xs text-red-300">
                                {error}
                            </p>
                        )}
                        <button
                            type="submit"
                            disabled={isGenerating}
                            className="btn-light w-full py-4 text-base"
                        >
                            {isGenerating ? 'Generating…' : 'Generate video'}
                        </button>
                        <p className="text-center text-xs text-faint">One render at a time</p>
                    </div>
                </div>
            </form>
        </section>
    );
}

function Field({ label, hint, children }) {
    return (
        <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
                <span className="eyebrow">{label}</span>
                {hint && <span className="text-xs text-faint">{hint}</span>}
            </div>
            {children}
        </div>
    );
}
