interface Props {
  mode: "simple" | "technical";
  onToggle: (mode: "simple" | "technical") => void;
}

const modes = ["simple", "technical"] as const;

export default function ModeToggle({ mode, onToggle }: Props) {
  return (
    <div className="inline-flex rounded-full border border-zinc-600 overflow-hidden">
      {modes.map((m) => (
        <button
          key={m}
          onClick={() => onToggle(m)}
          className={`px-4 py-1.5 text-sm font-medium transition-colors ${
            mode === m
              ? "bg-white text-zinc-900"
              : "bg-transparent text-zinc-500 hover:text-zinc-300"
          }`}
        >
          {m === "simple" ? "Simple" : "Technical"}
        </button>
      ))}
    </div>
  );
}
