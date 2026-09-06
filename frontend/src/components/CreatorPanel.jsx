import { useState } from 'react';
import { durationOptions, formatOptions, visibilityOptions } from '../data/options.js';

const initialForm = {
    format: 'video',
    topic: '',
    duration: 60,
    keyPoints: '',
    visibility: 'unlisted',
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
                <span className="chip">Auto-publishes · ~5–10 min</span>
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
                    <Field label="Visibility on YouTube">
                        <div className="flex flex-col gap-2">
                            {visibilityOptions.map((option) => {
                                const active = form.visibility === option.value;
                                return (
                                    <button
                                        key={option.value}
                                        type="button"
                                        onClick={() => update('visibility', option.value)}
                                        className={`flex items-center justify-between rounded-xl border px-4 py-3 text-sm font-medium transition-all ${
                                            active
                                                ? 'border-accent/40 bg-accent/10 text-txt'
                                                : 'border-tint/10 bg-tint/[0.03] text-muted hover:text-txt'
                                        }`}
                                    >
                                        {option.label}
                                    </button>
                                );
                            })}
                        </div>
                    </Field>

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
                            <span aria-hidden>↗</span>
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
