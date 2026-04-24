
function CardProgetto({data, nuovo_progetto = false}) {
  return (
    <div className="aspect-square border border-gray-200 rounded-lg p-4 shadow-md bg-white transition-colors transition-shadow duration-200 hover:bg-gray-50 hover:shadow-lg">
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
