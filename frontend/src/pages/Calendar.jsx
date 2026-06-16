function Calendar() {
  return (
    <div className="flex min-h-full items-center justify-center px-6 py-12">
      <div className="relative w-full max-w-xl overflow-hidden rounded-3xl border border-main-border bg-main-card p-10 text-center text-main-text shadow-xl">
        <div className="absolute left-1/2 top-0 h-32 w-32 -translate-x-1/2 -translate-y-1/2 rounded-full bg-indigo-500/20 blur-3xl" />

        <p className="text-sm font-semibold uppercase tracking-[0.35em] text-main-text/50">
          Calendario
        </p>
        <h1 className="mt-4 text-4xl font-bold tracking-tight sm:text-5xl">
          Coming soon
        </h1>
        <p className="mx-auto mt-4 max-w-md text-sm leading-6 text-main-text/70">
          La vista calendario arrivera qui: eventi, task programmate e scadenze in un unico spazio.
        </p>

        <div className="mt-8 flex justify-center">
          <div className="grid grid-cols-7 gap-2 rounded-2xl border border-main-border bg-main-bg p-4">
            {Array.from({ length: 21 }).map((_, index) => (
              <span
                key={index}
                className={`h-3 w-3 rounded-full ${
                  index % 5 === 0 ? 'bg-indigo-500' : 'bg-main-border'
                }`}
              />
            ))}
          </div>
        </div>
    </div>
    </div>
  );
}

export default Calendar;
