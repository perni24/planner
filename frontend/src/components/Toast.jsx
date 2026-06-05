function Toast({ toast, onClose }) {
  if (!toast) {
    return null;
  }

  const typeClass = {
    success: 'bg-green-600',
    error: 'bg-red-600',
    info: 'bg-indigo-600',
  }[toast.type] ?? 'bg-indigo-600';

  return (
    <div className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium text-white shadow-lg ${typeClass}`}>
      <span>{toast.message}</span>
      <button
        type="button"
        onClick={onClose}
        className="rounded px-1 text-white/80 transition-colors hover:bg-white/10 hover:text-white"
      >
        X
      </button>
    </div>
  );
}

export default Toast;
