export function createLatestRead() {
  let current = null;
  let disposed = false;

  async function run(read, onData, onError) {
    if (disposed) return;

    current?.abort();
    const controller = new AbortController();
    current = controller;

    try {
      const data = await read(controller.signal);
      // Ignora la risposta anche se la lettura non rispetta il segnale di annullamento.
      if (!controller.signal.aborted) onData(data);
    } catch (error) {
      if (!controller.signal.aborted) onError(error);
    } finally {
      if (current === controller) current = null;
    }
  }

  function dispose() {
    disposed = true;
    current?.abort();
    current = null;
  }

  return { run, dispose };
}
