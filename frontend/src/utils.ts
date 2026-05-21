export function formatDate(raw: string): string {
  if (!raw || raw.trim() === "") return "";

  let s = raw.trim();
  if (s.startsWith("D:")) s = s.slice(2);

  const m = s.match(/^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/);
  if (!m) return raw;

  const [, Y, M, D, h, m2, sec] = m;
  let iso = `${Y}-${M}-${D}T${h}:${m2}:${sec}`;

  const tzMatch = s.slice(14).match(/^([+-])(\d{2})'(\d{2})'/);
  if (tzMatch) {
    const sign = tzMatch[1];
    iso += `${sign}${tzMatch[2]}:${tzMatch[3]}`;
  }

  const dt = new Date(iso);
  if (isNaN(dt.getTime())) return raw;

  return dt.toLocaleString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZone: "UTC",
    timeZoneName: "short",
  });
}
