interface Props {
  level: "Low" | "Medium" | "High";
  score: number;
}

const colors: Record<string, string> = {
  Low: "bg-green-900/40 text-green-300 border-green-700",
  Medium: "bg-amber-900/40 text-amber-300 border-amber-700",
  High: "bg-red-900/40 text-red-300 border-red-700",
};

export default function RiskBadge({ level, score }: Props) {
  return (
    <div
      className={`inline-flex items-center gap-3 px-5 py-3 rounded-xl border text-lg font-bold ${colors[level]}`}
    >
      <span>{score}</span>
      <span className="text-base font-normal opacity-80">{level}</span>
    </div>
  );
}
