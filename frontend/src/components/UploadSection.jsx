import { useEffect, useRef, useState } from 'react';
import { getIngestJob, listIngestJobs, uploadVideo } from '../api/ingest.js';
import { vertical } from '../data/media.js';
import { ShortsPhone } from './Visuals.jsx';

const STAGES = [
    { key: 'probe', label: 'Reading' },
    { key: 'transcribe', label: 'Transcribing' },
    { key: 'metadata', label: 'Writing metadata' },
    { key: 'thumbnail', label: 'Thumbnail' },
    { key: 'clips', label: 'Finding clips' },
    { key: 'publish', label: 'Publishing' },
    { key: 'done', label: 'Done' },
];

/**
 * Upload a finished video and get the busywork done to it.
 *
 * The file is never re-encoded: a frame is pulled for the thumbnail, the audio
 * is transcribed into an .srt sidecar YouTube renders itself, and the original
 * bytes are what get uploaded. That is what keeps this inside a small
 * instance's memory.
 */
export function UploadSection({ youtubeReady }) {
    const [file, setFile] = useState(null);
    const [publish, setPublish] = useState(false);
    const [privacy, setPrivacy] = useState('private');
    const [suggestClips, setSuggestClips] = useState(true);
    const [uploadPct, setUploadPct] = useState(0);
    const [job, setJob] = useState(null);
    const [error, setError] = useState('');
    const [busy, setBusy] = useState(false);
    const [dragging, setDragging] = useState(false);
    const [limitMb, setLimitMb] = useState(400);

    const inputRef = useRef(null);
    const pollRef = useRef(null);

    useEffect(() => {
        listIngestJobs()
            .then((data) => setLimitMb(data.max_mb ?? 400))
            .catch(() => {});
        return () => window.clearInterval(pollRef.current);
    }, []);

    function pick(nextFile) {
        if (!nextFile) return;
        const mb = nextFile.size / (1024 * 1024);
        if (mb > limitMb) {
            setError(
                `${nextFile.name} is ${mb.toFixed(0)} MB. This instance accepts up to ${limitMb} MB.`,
            );
            return;
        }
        setError('');
        setJob(null);
        setFile(nextFile);
    }

    function watch(jobId) {
        window.clearInterval(pollRef.current);
        pollRef.current = window.setInterval(async () => {
            try {
                const next = await getIngestJob(jobId);
                setJob(next);
                if (!next.active) {
                    window.clearInterval(pollRef.current);
                    setBusy(false);
                }
            } catch {
                // A transient failure is not worth abandoning the watch over;
                // the job is still running server-side either way.
            }
        }, 2000);
    }

    async function start() {
        if (!file || busy) return;
        setBusy(true);
        setError('');
        setUploadPct(0);
        try {
            const created = await uploadVideo(
                file,
                { publish, privacy, suggestClips },
                setUploadPct,
            );
            setJob({ ...created, stage: 'queued', message: 'Queued', progress: 0, active: true });
            watch(created.job_id);
        } catch (err) {
            setError(err.message || 'Upload failed.');
            setBusy(false);
        }
    }

    const result = job?.result;
    const activeStageIndex = STAGES.findIndex((s) => s.key === job?.stage);

    return (
        <section id="upload" className="mx-auto w-full max-w-[1600px] px-4 py-20 sm:px-6 lg:px-8">
            <header className="max-w-2xl">
                <span className="eyebrow">Already filmed it?</span>
                <h2 className="display mt-3 text-display-md">
                    Drop the file. <span className="italic text-muted">Skip the rest.</span>
                </h2>
                <p className="mt-4 text-sm leading-relaxed text-muted">
                    Title, description, twenty tags, a thumbnail, a caption track and the upload
                    itself. Your video is never re-encoded — the original bytes are what reach
                    YouTube.
                </p>
            </header>

            <div className="mt-10 grid gap-8 lg:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)]">
                <div className="space-y-6">
                    {/* dropzone */}
                    <div
                        onDragOver={(event) => {
                            event.preventDefault();
                            setDragging(true);
                        }}
                        onDragLeave={() => setDragging(false)}
                        onDrop={(event) => {
                            event.preventDefault();
                            setDragging(false);
                            pick(event.dataTransfer.files?.[0]);
                        }}
                        className={`glass flex flex-col items-center justify-center px-6 py-14 text-center transition-colors ${
                            dragging ? 'border-accent/60 bg-accent/[0.06]' : ''
                        }`}
                    >
                        <input
                            ref={inputRef}
                            type="file"
                            accept="video/mp4,video/quicktime,video/x-matroska,video/webm,video/x-msvideo"
                            className="hidden"
                            onChange={(event) => pick(event.target.files?.[0])}
                        />

                        <span className="grid h-14 w-14 place-items-center rounded-full border border-tint/15 bg-tint/[0.06]">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6"
                                 strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6 text-accent">
                                <path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5" />
                                <path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
                            </svg>
                        </span>

                        <p className="display mt-5 text-lg">
                            {file ? file.name : 'Drag a video here'}
                        </p>
                        <p className="mt-1.5 text-xs text-faint">
                            {file
                                ? `${(file.size / (1024 * 1024)).toFixed(1)} MB`
                                : `mp4, mov, mkv, webm or avi — up to ${limitMb} MB`}
                        </p>

                        <button
                            type="button"
                            onClick={() => inputRef.current?.click()}
                            className="btn-ghost mt-6"
                        >
                            {file ? 'Choose a different file' : 'Browse files'}
                        </button>
                    </div>

                    {/* options */}
                    <div className="glass p-6 sm:p-8">
                        <h3 className="display text-lg">What should happen to it</h3>

                        <label className="mt-5 flex items-start gap-3">
                            <input
                                type="checkbox"
                                checked={publish}
                                onChange={(event) => setPublish(event.target.checked)}
                                disabled={!youtubeReady}
                                className="mt-1 rounded border-tint/25 bg-panel2 text-accent focus:ring-0"
                            />
                            <span>
                                <span className="text-sm text-txt">Publish to YouTube when it’s ready</span>
                                <span className="mt-0.5 block text-xs text-faint">
                                    {youtubeReady
                                        ? 'Uploads to your connected channel, with the thumbnail and caption track attached.'
                                        : 'Connect a channel first. Without this you still get the thumbnail, captions and metadata to use yourself.'}
                                </span>
                            </span>
                        </label>

                        {publish ? (
                            <div className="mt-5 pl-7">
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
                            </div>
                        ) : null}

                        <label className="mt-5 flex items-start gap-3">
                            <input
                                type="checkbox"
                                checked={suggestClips}
                                onChange={(event) => setSuggestClips(event.target.checked)}
                                className="mt-1 rounded border-tint/25 bg-panel2 text-accent focus:ring-0"
                            />
                            <span>
                                <span className="text-sm text-txt">Find Shorts-worthy moments</span>
                                <span className="mt-0.5 block text-xs text-faint">
                                    Picks self-contained passages from the transcript. Only runs on
                                    videos over two minutes.
                                </span>
                            </span>
                        </label>

                        <button
                            type="button"
                            onClick={start}
                            disabled={!file || busy}
                            className="btn-accent mt-7 w-full"
                        >
                            {busy ? 'Working…' : 'Process this video'}
                        </button>

                        {busy && uploadPct < 100 ? (
                            <div className="mt-4">
                                <div className="h-1 overflow-hidden rounded-full bg-tint/10">
                                    <div
                                        className="h-full rounded-full bg-accent transition-all duration-200"
                                        style={{ width: `${uploadPct}%` }}
                                    />
                                </div>
                                <p className="mt-2 text-xs text-faint">Uploading — {uploadPct}%</p>
                            </div>
                        ) : null}

                        {error ? (
                            <p className="mt-4 rounded-xl border border-red-500/25 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                                {error}
                            </p>
                        ) : null}
                    </div>
                </div>

                {/* -------- progress + result -------- */}
                <aside className="space-y-6">
                    {job ? (
                        <div className="glass p-6 sm:p-8">
                            <h3 className="display text-lg">{job.filename}</h3>
                            <p className="mt-1 text-sm text-muted">{job.message}</p>

                            <ol className="mt-6 space-y-2.5">
                                {STAGES.map((stage, index) => {
                                    const done = activeStageIndex > index || job.stage === 'done';
                                    const current = job.stage === stage.key;
                                    return (
                                        <li key={stage.key} className="flex items-center gap-3 text-sm">
                                            <span
                                                className={`h-1.5 w-1.5 rounded-full ${
                                                    current
                                                        ? 'bg-accent'
                                                        : done
                                                          ? 'bg-accent/40'
                                                          : 'bg-tint/20'
                                                }`}
                                            />
                                            <span className={current ? 'text-txt' : done ? 'text-muted' : 'text-faint'}>
                                                {stage.label}
                                            </span>
                                        </li>
                                    );
                                })}
                            </ol>

                            {job.error ? (
                                <p className="mt-5 rounded-xl border border-red-500/25 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                                    {job.error}
                                </p>
                            ) : null}
                        </div>
                    ) : (
                        <div className="glass p-6 sm:p-8">
                            <h3 className="display text-lg">What comes back</h3>
                            <ul className="mt-5 space-y-3 text-sm text-muted">
                                {[
                                    'Three title options, most specific first',
                                    'A description with the hook in the first line',
                                    'Around twenty search tags, plus hashtags',
                                    'A 1280×720 thumbnail cut from your own footage',
                                    'An .srt caption track from your audio',
                                    'Timestamps for the best Shorts moments',
                                ].map((item) => (
                                    <li key={item} className="flex gap-3">
                                        <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-accent" />
                                        {item}
                                    </li>
                                ))}
                            </ul>
                            {/* Sized off the container rather than a fixed
                                width, so the pair fills whatever the column
                                gives them. At 112px the platform chip and the
                                side rail were landing on top of each other. */}
                            <div className="mt-8 flex justify-center gap-4">
                                <ShortsPhone
                                    variant="cool"
                                    label="Reels"
                                    image={vertical.clip}
                                    caption="Clip 1 of 3"
                                    className="w-[46%] max-w-[15rem]"
                                />
                                <ShortsPhone
                                    variant="warm"
                                    label="Shorts"
                                    image={vertical.shorts}
                                    caption="Clip 2 of 3"
                                    className="w-[46%] max-w-[15rem]"
                                />
                            </div>
                        </div>
                    )}

                    {result ? <ResultPanel result={result} /> : null}
                </aside>
            </div>
        </section>
    );
}

function ResultPanel({ result }) {
    const [copied, setCopied] = useState('');
    const metadata = result.metadata ?? {};

    function copy(label, text) {
        navigator.clipboard?.writeText(text).then(
            () => {
                setCopied(label);
                window.setTimeout(() => setCopied(''), 1600);
            },
            () => setCopied(''),
        );
    }

    return (
        <div className="glass p-6 sm:p-8">
            <h3 className="display text-lg">Ready to use</h3>

            {result.published?.url ? (
                <a
                    href={result.published.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-light mt-5 w-full"
                >
                    Open on YouTube
                </a>
            ) : null}

            <div className="mt-6">
                <div className="flex items-center justify-between">
                    <span className="eyebrow">Titles</span>
                    <button
                        type="button"
                        onClick={() => copy('title', metadata.titles?.[0] ?? '')}
                        className="text-xs text-muted hover:text-txt"
                    >
                        {copied === 'title' ? 'Copied' : 'Copy'}
                    </button>
                </div>
                <ul className="mt-2 space-y-2">
                    {(metadata.titles ?? []).map((title, index) => (
                        <li
                            key={title}
                            className={`rounded-lg border px-3 py-2 text-sm ${
                                index === 0
                                    ? 'border-accent/30 bg-accent/[0.06] text-txt'
                                    : 'border-tint/10 text-muted'
                            }`}
                        >
                            {title}
                        </li>
                    ))}
                </ul>
            </div>

            {metadata.description ? (
                <div className="mt-6">
                    <div className="flex items-center justify-between">
                        <span className="eyebrow">Description</span>
                        <button
                            type="button"
                            onClick={() => copy('description', metadata.description)}
                            className="text-xs text-muted hover:text-txt"
                        >
                            {copied === 'description' ? 'Copied' : 'Copy'}
                        </button>
                    </div>
                    <p className="mt-2 max-h-40 overflow-y-auto whitespace-pre-wrap rounded-lg border border-tint/10 bg-panel2 px-3 py-2 text-xs leading-relaxed text-muted">
                        {metadata.description}
                    </p>
                </div>
            ) : null}

            {metadata.tags?.length ? (
                <div className="mt-6">
                    <div className="flex items-center justify-between">
                        <span className="eyebrow">Tags · {metadata.tags.length}</span>
                        <button
                            type="button"
                            onClick={() => copy('tags', metadata.tags.join(', '))}
                            className="text-xs text-muted hover:text-txt"
                        >
                            {copied === 'tags' ? 'Copied' : 'Copy'}
                        </button>
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1.5">
                        {metadata.tags.map((tag) => (
                            <span key={tag} className="chip py-0.5 text-[0.65rem]">
                                {tag}
                            </span>
                        ))}
                    </div>
                </div>
            ) : null}

            {result.clips?.length ? (
                <div className="mt-6">
                    <span className="eyebrow">Shorts-worthy moments</span>
                    <ul className="mt-2 space-y-2">
                        {result.clips.map((clip) => (
                            <li key={`${clip.start}-${clip.end}`} className="rounded-lg border border-tint/10 px-3 py-2">
                                <div className="flex items-baseline justify-between gap-3">
                                    <span className="text-sm text-txt">{clip.title}</span>
                                    <span className="shrink-0 text-xs text-faint">
                                        {formatTime(clip.start)}–{formatTime(clip.end)}
                                    </span>
                                </div>
                                <p className="mt-1 text-xs leading-relaxed text-faint">{clip.reason}</p>
                            </li>
                        ))}
                    </ul>
                </div>
            ) : null}

            <dl className="mt-6 grid grid-cols-3 gap-3 border-t border-tint/10 pt-5 text-center">
                <Stat label="Length" value={formatTime(result.duration ?? 0)} />
                <Stat label="Captions" value={result.captions ?? 0} />
                <Stat label="Format" value={result.vertical ? '9:16' : '16:9'} />
            </dl>

            {result.warnings?.length ? (
                <ul className="mt-5 space-y-2">
                    {result.warnings.map((warning) => (
                        <li
                            key={warning}
                            className="rounded-lg border border-amber-500/25 bg-amber-500/10 px-3 py-2 text-xs leading-relaxed text-amber-200"
                        >
                            {warning}
                        </li>
                    ))}
                </ul>
            ) : null}
        </div>
    );
}

function Stat({ label, value }) {
    return (
        <div>
            <dt className="text-[0.65rem] uppercase tracking-[0.16em] text-faint">{label}</dt>
            <dd className="display mt-1 text-lg">{value}</dd>
        </div>
    );
}

function formatTime(seconds) {
    const total = Math.max(0, Math.round(Number(seconds) || 0));
    const minutes = Math.floor(total / 60);
    return `${minutes}:${String(total % 60).padStart(2, '0')}`;
}
