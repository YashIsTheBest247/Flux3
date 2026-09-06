import { useEffect } from 'react';

export function ConfirmDialog({
    open,
    title = 'Are you sure?',
    message,
    confirmLabel = 'Delete',
    cancelLabel = 'Cancel',
    onConfirm,
    onCancel,
}) {
    // Close on Escape.
    useEffect(() => {
        if (!open) return undefined;
        const onKey = (e) => e.key === 'Escape' && onCancel?.();
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [open, onCancel]);

    if (!open) return null;

    return (
        <div className="fixed inset-0 z-[100] grid place-items-center p-4">
            {/* backdrop */}
            <div
                onClick={onCancel}
                className="absolute inset-0 animate-fadeIn bg-black/60 backdrop-blur-sm"
            />

            {/* dialog */}
            <div
                role="alertdialog"
                aria-modal="true"
                className="glass-strong relative w-full max-w-sm animate-popIn overflow-hidden rounded-2xl p-6 text-center shadow-card"
            >
                <span className="mx-auto grid h-14 w-14 place-items-center rounded-full border border-red-400/30 bg-red-500/10 text-red-400">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" className="h-6 w-6" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m2 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6" />
                        <path d="M10 11v6M14 11v6" />
                    </svg>
                </span>

                <h3 className="display mt-4 text-xl font-semibold text-txt">{title}</h3>
                {message && <p className="mt-2 text-sm text-muted">{message}</p>}

                <div className="mt-6 flex gap-3">
                    <button
                        type="button"
                        onClick={onCancel}
                        className="flex-1 rounded-xl border border-tint/15 bg-tint/[0.04] py-2.5 text-sm font-medium text-txt transition-colors hover:bg-tint/[0.1]"
                    >
                        {cancelLabel}
                    </button>
                    <button
                        type="button"
                        onClick={onConfirm}
                        className="flex-1 rounded-xl bg-red-500 py-2.5 text-sm font-semibold text-white shadow-lg transition-all hover:bg-red-600 hover:shadow-red-500/30 active:scale-95"
                    >
                        {confirmLabel}
                    </button>
                </div>
            </div>
        </div>
    );
}
