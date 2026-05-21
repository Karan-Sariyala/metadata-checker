import { PieChart, Pie, Cell } from "recharts";
import type { Finding } from "../types";

interface Props {
  findings: Finding[];
  totalScore: number;
  riskLevel: string;
}

const SEVERITY_BASE: Record<string, number> = { High: 30, Medium: 15, Low: 5 };

const COLORS: Record<string, string> = { High: "#ef4444", Medium: "#f59e0b", Low: "#3b82f6" };

const CENTER_COLORS: Record<string, string> = {
  Low: "#22c55e",
  Medium: "#f59e0b",
  High: "#ef4444",
};

export default function RiskDonut({ findings, totalScore, riskLevel }: Props) {
  const counts: Record<string, number> = { High: 0, Medium: 0, Low: 0 };
  for (const f of findings) {
    if (f.severity in counts) counts[f.severity]++;
  }

  const slices: { name: string; value: number; color: string }[] = [];
  let rawTotal = 0;
  for (const sev of ["High", "Medium", "Low"] as const) {
    const v = counts[sev] * SEVERITY_BASE[sev];
    if (v > 0) {
      rawTotal += v;
      slices.push({ name: sev, value: v, color: COLORS[sev] });
    }
  }

  const unused = Math.max(0, 100 - totalScore);
  if (unused > 0) {
    slices.push({ name: "Unused", value: unused, color: "#3f3f46" });
  }

  if (slices.length === 0) {
    slices.push({ name: "None", value: 100, color: "#3f3f46" });
  }

  const centerColor = totalScore === 0 ? "#22c55e" : CENTER_COLORS[riskLevel] ?? "#e5e5e5";

  return (
    <div className="flex items-center gap-6 flex-wrap">
      <div className="relative shrink-0" style={{ width: 200, height: 200 }}>
        <PieChart width={200} height={200}>
          <Pie
            data={slices}
            cx={100}
            cy={100}
            innerRadius={65}
            outerRadius={95}
            dataKey="value"
            stroke="none"
          >
            {slices.map((entry, i) => (
              <Cell key={i} fill={entry.color} />
            ))}
          </Pie>
        </PieChart>
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-3xl font-bold" style={{ color: centerColor }}>
            {totalScore}
          </span>
          <span className="text-xs text-zinc-500 uppercase tracking-wider mt-0.5">
            {findings.length === 0 ? "No issues" : riskLevel}
          </span>
        </div>
      </div>

      <div className="space-y-2 text-sm">
        {(["High", "Medium", "Low"] as const).map((sev) => {
          const c = counts[sev];
          if (c === 0) return null;
          const pts = c * SEVERITY_BASE[sev];
          return (
            <div key={sev} className="flex items-center gap-2 text-zinc-300">
              <span
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{ backgroundColor: COLORS[sev] }}
              />
              <span className="capitalize w-16">{sev.toLowerCase()}</span>
              <span className="text-zinc-500 w-6 text-right">{c}</span>
              <span className="text-zinc-600">&mdash;</span>
              <span className="text-zinc-400 w-16 text-right">{pts} pts</span>
            </div>
          );
        })}
        {totalScore < 100 && (
          <div className="flex items-center gap-2 text-zinc-500">
            <span className="w-2.5 h-2.5 rounded-full shrink-0 bg-zinc-600" />
            <span className="w-16">Unused</span>
            <span className="w-6 text-right">&ndash;</span>
            <span className="text-zinc-600">&mdash;</span>
            <span className="w-16 text-right">{100 - totalScore} pts</span>
          </div>
        )}
      </div>
    </div>
  );
}
