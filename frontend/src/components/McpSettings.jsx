import { useLanguage } from '../context/useLanguage';
import { useToast } from '../context/useToast';

const MCP_URL = import.meta.env.DEV
  ? 'http://127.0.0.1:8000/mcp/'
  : new URL('/mcp/', window.location.origin).toString();

function McpSettings() {
  const { jsonLanguage } = useLanguage();
  const { showToast } = useToast();

  async function copyMcpUrl() {
    try {
      await navigator.clipboard.writeText(MCP_URL);
      showToast(jsonLanguage['settings.mcp.toast.copied'], 'success');
    } catch (error) {
      console.error('Error copying MCP URL:', error);
      showToast(jsonLanguage['settings.mcp.toast.copyError'], 'error');
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-4">
        <label className="text-sm font-medium">
          {jsonLanguage['settings.mcp.title']}
        </label>
        <span className="inline-flex items-center gap-2 rounded-full border border-main-border px-3 py-1 text-xs font-medium text-main-text/70">
          <span className="h-2 w-2 rounded-full bg-emerald-500" aria-hidden="true" />
          {jsonLanguage['settings.mcp.available']}
        </span>
      </div>

      <p className="text-sm text-main-text/70">
        {jsonLanguage['settings.mcp.description']}
      </p>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="rounded-md border border-main-border bg-main-bg/40 px-4 py-3">
          <p className="text-xs text-main-text/60">
            {jsonLanguage['settings.mcp.serverName']}
          </p>
          <p className="mt-1 text-sm font-medium">Planner</p>
        </div>
        <div className="rounded-md border border-main-border bg-main-bg/40 px-4 py-3">
          <p className="text-xs text-main-text/60">
            {jsonLanguage['settings.mcp.transport']}
          </p>
          <p className="mt-1 text-sm font-medium">Streamable HTTP</p>
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <span className="text-xs text-main-text/60">
          {jsonLanguage['settings.mcp.endpoint']}
        </span>
        <div className="flex flex-col gap-3 sm:flex-row">
          <code className="min-w-0 flex-1 overflow-x-auto rounded-md border border-main-border bg-main-bg/40 px-4 py-2 text-sm">
            {MCP_URL}
          </code>
          <button
            type="button"
            onClick={copyMcpUrl}
            className="rounded-md border border-main-border bg-main-card px-4 py-2 text-sm font-medium text-main-text shadow-sm transition-colors hover:bg-main-hover hover:text-main-hover-text"
          >
            {jsonLanguage['settings.mcp.copy']}
          </button>
        </div>
      </div>

      <details className="group rounded-md border border-main-border px-4 py-3">
        <summary className="cursor-pointer text-sm font-medium">
          {jsonLanguage['settings.mcp.instructions.title']}
        </summary>
        <ol className="mt-4 list-decimal space-y-2 pl-5 text-sm text-main-text/70">
          <li>{jsonLanguage['settings.mcp.instructions.openClient']}</li>
          <li>{jsonLanguage['settings.mcp.instructions.addServer']}</li>
          <li>{jsonLanguage['settings.mcp.instructions.selectTransport']}</li>
          <li>{jsonLanguage['settings.mcp.instructions.enterUrl']}</li>
          <li>{jsonLanguage['settings.mcp.instructions.keepOpen']}</li>
        </ol>
        <p className="mt-4 text-xs text-main-text/60">
          {jsonLanguage['settings.mcp.instructions.note']}
        </p>
      </details>

      <p className="rounded-md border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-xs text-amber-600">
        {jsonLanguage['settings.mcp.warning']}
      </p>
    </div>
  );
}

export default McpSettings;
