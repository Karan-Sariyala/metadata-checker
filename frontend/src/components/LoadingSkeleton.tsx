export default function LoadingSkeleton() {
  const bar = (w: string) => (
    <div className={`h-4 rounded bg-zinc-700 animate-pulse ${w}`} />
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <div className="flex-1 space-y-2">
          {bar("w-3/5")}
          {bar("w-1/3")}
        </div>
        <div className="w-[200px] h-[200px] rounded-full bg-zinc-700 animate-pulse shrink-0" />
      </div>

      <div className="h-20 rounded-xl bg-zinc-800 animate-pulse" />

      <div className="space-y-3">
        <div className="h-4 w-24 rounded bg-zinc-700 animate-pulse" />
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 rounded-xl bg-zinc-800 animate-pulse" />
          ))}
        </div>
      </div>

      <div className="h-36 rounded-xl bg-zinc-800 animate-pulse" />

      <div className="space-y-1">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="flex gap-4">
            {bar("w-1/4")}
            {bar("w-2/4")}
          </div>
        ))}
      </div>
    </div>
  );
}
