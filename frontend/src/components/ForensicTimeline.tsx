import type { ExtractedMetadata, Finding } from "../types";

interface Props {
  metadata: ExtractedMetadata;
  findings: Finding[];
}

function parseDate(raw: string): Date | null {
  if (!raw) return null;
  let s = raw.trim();
  if (s.startsWith("D:")) s = s.slice(2);
  const m = s.match(/^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/);
  if (!m) {
    const d = new Date(s);
    return isNaN(d.getTime()) ? null : d;
  }
  const [, Y, M, D, h, m2, sec] = m;
  let iso = `${Y}-${M}-${D}T${h}:${m2}:${sec}`;
  const tz = s.slice(14).match(/^([+-])(\d{2})'(\d{2})'/);
  if (tz) iso += `${tz[1]}${tz[2]}:${tz[3]}`;
  const d = new Date(iso);
  return isNaN(d.getTime()) ? null : d;
}

function formatDateLabel(d: Date): string {
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

interface Period {
  days: number;
  label: string;
  color: string;
}

function computePeriod(cd: Date, md: Date): Period {
  const diffMs = md.getTime() - cd.getTime();
  const diffDays = diffMs / (1000 * 60 * 60 * 24);
  if (diffMs < 0) return { days: -1, label: "IMPOSSIBLE — modified before created", color: "text-red-400" };
  if (diffDays < 7) return { days: Math.round(diffDays), label: `${Math.round(diffDays)} day${Math.round(diffDays) === 1 ? "" : "s"}`, color: "text-green-400" };
  if (diffDays < 180) return { days: Math.round(diffDays), label: `${Math.round(diffDays)} days`, color: "text-amber-400" };
  const months = Math.round(diffDays / 30);
  return { days: Math.round(diffDays), label: `~${months} month${months === 1 ? "" : "s"}`, color: "text-red-400" };
}

export default function ForensicTimeline({ metadata, findings }: Props) {
  const created = parseDate(metadata.created_date ?? "");
  const modified = parseDate(metadata.modified_date ?? "");

  const inc = metadata.incremental_updates as Record<string, unknown> | null;
  const revisionCount = (inc?.revision_count as number) ?? 1;
  const extraRevisions = revisionCount > 1 ? revisionCount - 1 : 0;

  if (!created && !modified) {
    return (
      <div className="bg-zinc-800/40 rounded-xl border border-zinc-700 p-4">
        <p className="text-amber-400 text-sm">No date information available</p>
      </div>
    );
  }

  if (!created || !modified) {
    const date = (created ?? modified)!;
    return (
      <div className="bg-zinc-800/40 rounded-xl border border-zinc-700 p-5">
        <div className="flex flex-col items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-green-500" />
          <span className="text-xs text-zinc-300">{formatDateLabel(date)}</span>
          <span className="text-xs text-zinc-500 italic">
            Only one date available — cannot compute timeline span
          </span>
        </div>
      </div>
    );
  }

  const period = computePeriod(created, modified);
  const isImpossible = period.days < 0;
  const modColor = isImpossible
    ? "red"
    : period.days < 7
      ? "green"
      : period.days < 180
        ? "amber"
        : "red";

  const modDotColor = { green: "bg-green-500", amber: "bg-amber-500", red: "bg-red-500" }[modColor];

  const severityCounts = { High: 0, Medium: 0, Low: 0 };
  for (const f of findings) {
    if (f.severity in severityCounts) severityCounts[f.severity as keyof typeof severityCounts]++;
  }

  const toolDiff =
    metadata.creator &&
    metadata.producer &&
    metadata.creator.toLowerCase() !== metadata.producer.toLowerCase() &&
    !metadata.creator.toLowerCase().includes(metadata.producer.toLowerCase()) &&
    !metadata.producer.toLowerCase().includes(metadata.creator.toLowerCase());

  return (
    <div className="bg-zinc-800/40 rounded-xl border border-zinc-700 p-5">
      <h4 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-4">
        Document Timeline
      </h4>

      {/* Timeline bar */}
      <div className="relative w-full">
        {/* SVG line */}
        <svg className="w-full h-8" viewBox="0 0 100 32" preserveAspectRatio="none">
          <line x1="2" y1="16" x2="98" y2="16" stroke="#52525b" strokeWidth="2" />
          {extraRevisions > 0 &&
            Array.from({ length: extraRevisions }).map((_, i) => {
              const x = 2 + (96 / (extraRevisions + 1)) * (i + 1);
              return (
                <line key={i} x1={x} y1="10" x2={x} y2="22" stroke="#a1a1aa" strokeWidth="1.5" />
              );
            })}
          {/* Creation dot */}
          <circle cx="2" cy="16" r="6" fill="#22c55e" stroke="#0f0f0f" strokeWidth="2" />
          {/* Modification dot */}
          <circle cx="98" cy="16" r="6" fill={modDotColor === "bg-green-500" ? "#22c55e" : modDotColor === "bg-amber-500" ? "#f59e0b" : "#ef4444"} stroke="#0f0f0f" strokeWidth="2" />
        </svg>

        {/* Labels row */}
        <div className="flex justify-between text-xs mt-1">
          <div className="text-center">
            <p className="text-zinc-300">{formatDateLabel(created)}</p>
            {metadata.creator && <p className="text-zinc-500 truncate max-w-[140px]">{metadata.creator}</p>}
          </div>
          <div className="text-center">
            {extraRevisions > 0 && (
              <p className="text-zinc-400 text-[10px] mb-0.5">{revisionCount} revisions</p>
            )}
          </div>
          <div className="text-center">
            <p className="text-zinc-300">{formatDateLabel(modified)}</p>
            {metadata.producer && <p className="text-zinc-500 truncate max-w-[140px]">{metadata.producer}</p>}
          </div>
        </div>

        {/* Gap label */}
        <p className={`text-center text-xs font-medium mt-2 ${period.color}`}>
          {period.label}
        </p>
      </div>

      {/* Tool row */}
      {(metadata.creator || metadata.producer) && (
        <div className="flex flex-col sm:flex-row gap-3 mt-4">
          {metadata.creator && (
            <div className={`flex-1 rounded-lg border px-3 py-2 text-xs ${toolDiff ? "border-amber-700 bg-amber-900/20" : "border-zinc-700"}`}>
              <span className="text-zinc-500">Created with:</span>
              <span className="text-zinc-200 ml-1">{metadata.creator}</span>
            </div>
          )}
          {metadata.producer && (
            <div className={`flex-1 rounded-lg border px-3 py-2 text-xs ${toolDiff ? "border-amber-700 bg-amber-900/20" : "border-zinc-700"}`}>
              <span className="text-zinc-500">Last saved with:</span>
              <span className="text-zinc-200 ml-1">{metadata.producer}</span>
            </div>
          )}
        </div>
      )}

      {/* Findings indicator */}
      {findings.length > 0 && (
        <div className="flex items-center gap-4 mt-4 text-xs text-zinc-400">
          {severityCounts.High > 0 && (
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />
              {severityCounts.High} high signal{severityCounts.High > 1 ? "s" : ""}
            </span>
          )}
          {severityCounts.Medium > 0 && (
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" />
              {severityCounts.Medium} medium signal{severityCounts.Medium > 1 ? "s" : ""}
            </span>
          )}
          {severityCounts.Low > 0 && (
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-blue-500 inline-block" />
              {severityCounts.Low} low signal{severityCounts.Low > 1 ? "s" : ""}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
