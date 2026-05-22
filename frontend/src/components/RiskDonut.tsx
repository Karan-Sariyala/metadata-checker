import { PieChart, Pie, Cell } from "recharts";
import type { Finding } from "../types";

interface Props {
  findings: Finding[];
  riskLevel: string;
}

const SEVERITY_COLORS: Record<string, string> = {
  High: "#ef4444",
  Medium: "#f59e0b",
  Low: "#3b82f6",
};

export default function RiskDonut({ findings, riskLevel }: Props) {
  const counts: Record<string, number> = { High: 0, Medium: 0, Low: 0 };
  for (const f of findings) {
    if (f.severity in counts) counts[f.severity]++;
  }

  const hasData = Object.values(counts).some((c) => c > 0);

  if (!hasData) {
    return (
      <div className="flex flex-col items-center gap-2">
        <div className="relative w-[140px] h-[140px] sm:w-[160px] sm:h-[160px]">
          <PieChart width={160} height={160}>
            <Pie data={[{ name: "None", value: 100 }]} cx={80} cy={80} innerRadius={55} outerRadius={75} dataKey="value" stroke="none">
              <Cell fill="#3f3f46" />
            </Pie>
          </PieChart>
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <span className="text-sm text-zinc-500">No issues</span>
          </div>
        </div>
      </div>
    );
  }

  const slices = (["High", "Medium", "Low"] as const)
    .filter((sev) => counts[sev] > 0)
    .map((sev) => ({
      name: sev,
      value: counts[sev],
      color: SEVERITY_COLORS[sev],
    }));

  const centerColor = SEVERITY_COLORS[riskLevel] ?? "#e5e5e5";

  return (
    <div className="flex flex-col sm:flex-row items-center gap-6">
      <div className="relative w-[140px] h-[140px] sm:w-[160px] sm:h-[160px] shrink-0">
        <PieChart width={160} height={160}>
          <Pie
            data={slices}
            cx={80}
            cy={80}
            innerRadius={55}
            outerRadius={75}
            dataKey="value"
            stroke="none"
          >
            {slices.map((entry, i) => (
              <Cell key={i} fill={entry.color} />
            ))}
          </Pie>
        </PieChart>
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none select-none">
          <span className="text-lg font-bold" style={{ color: centerColor }}>
            {findings.length}
          </span>
          <span className="text-[10px] text-zinc-500 uppercase tracking-wider">
            signals
          </span>
        </div>
      </div>

      <div className="space-y-1.5 text-sm">
        {(["High", "Medium", "Low"] as const).map((sev) => {
          const c = counts[sev];
          if (c === 0) return null;
          return (
            <div key={sev} className="flex items-center gap-2 text-zinc-300">
              <span
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{ backgroundColor: SEVERITY_COLORS[sev] }}
              />
              <span className="capitalize w-16">{sev.toLowerCase()}</span>
              <span className="text-zinc-400 font-medium">{c}</span>
              <span className="text-zinc-600 text-xs">{c === 1 ? "signal" : "signals"}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
