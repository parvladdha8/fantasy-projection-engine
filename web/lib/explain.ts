// Turns the stored explanation ("recent average 22.3 → -1.1 role & efficiency … → median 22.2 (floor …)") into steps.
export type Step = { label: string; value: number; kind: "start" | "change" | "end" };

export function parseExplanation(text: string | null): Step[] {
  if (!text) return [];
  const parts = text.split("→").map((s) => s.trim()).filter(Boolean);
  const steps: Step[] = [];
  parts.forEach((p, i) => {
    if (i === 0) {
      const m = p.match(/^(.*?)\s+(-?\d+(?:\.\d+)?)$/);
      if (m) steps.push({ label: m[1], value: Number(m[2]), kind: "start" });
    } else if (i === parts.length - 1) {
      const m = p.match(/^median\s+(-?\d+(?:\.\d+)?)/);
      if (m) steps.push({ label: "median", value: Number(m[1]), kind: "end" });
    } else {
      const m = p.match(/^([+-]?\d+(?:\.\d+)?)\s+(.*)$/);
      if (m) steps.push({ label: m[2], value: Number(m[1]), kind: "change" });
    }
  });
  return steps;
}
