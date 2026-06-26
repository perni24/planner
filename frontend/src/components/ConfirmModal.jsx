function ConfirmModal({
  title,
  message,
  confirmLabel,
  cancelLabel,
  onConfirm,
  onCancel,
  isSubmitting = false,
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4">
      <div className="w-full max-w-md rounded-lg border border-main-border bg-main-card p-6 text-main-text shadow-xl">
        <div className="space-y-3">
          <h2 className="text-xl font-semibold">{title}</h2>
          <p className="text-sm leading-6 text-main-text/70">{message}</p>
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            disabled={isSubmitting}
            className="rounded-md border border-main-border px-4 py-2 text-sm font-medium text-main-text transition-colors hover:bg-main-hover hover:text-main-hover-text disabled:cursor-not-allowed disabled:opacity-60"
          >
            {cancelLabel}
          </button>

          <button
            type="button"
            onClick={onConfirm}
            disabled={isSubmitting}
            className="rounded-md border border-red-500 bg-red-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-600 disabled:cursor-not-allowed disabled:border-gray-400 disabled:bg-gray-400 disabled:opacity-60"
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ConfirmModal;
