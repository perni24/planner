
function CardProgetto({data, nuovo_progetto = false}) {
  return (
    <div className="aspect-square border border-main-border rounded-lg p-4 shadow-md bg-main-card transition-colors transition-shadow duration-200 hover:bg-main-hover hover:shadow-lg text-main-text">
    {nuovo_progetto ? (
        <div className="flex h-full flex-col">
        <h2 className="text-center text-xl font-semibold">Nuovo Progetto</h2>
        <p className="flex flex-1 items-center justify-center text-5xl font-bold">+</p>
        </div>
    ) : (
        <>
        <h2 className="text-center text-xl font-semibold">{data?.name ?? 'Progetto di Test'}</h2>
        </>
    )}
    </div>
    
  );
  }

  export default CardProgetto;
