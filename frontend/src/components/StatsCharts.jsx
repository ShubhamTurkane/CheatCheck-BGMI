import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell
} from "recharts";

// Different backend versions (or a future refactor of the SHAP-formatting
// code) might name the numeric magnitude field differently. Rather than
// hardcoding one name and silently rendering all-zero bars when it doesn't
// match, try the common candidates in order and use whichever one is
// actually a real, non-null number on this item.
const CONTRIBUTION_KEYS = ["contribution", "shap_value", "shapValue", "impact", "weight", "value"];

function pickContribution(item) {
  for (const key of CONTRIBUTION_KEYS) {
    const raw = item[key];
    if (raw !== undefined && raw !== null && raw !== "") {
      const num = Number(raw);
      if (!Number.isNaN(num)) return num;
    }
  }
  return null; // genuinely no usable numeric field found on this item
}

export default function StatsCharts({ evidence = [] }) {
  const parsed = evidence.map((x) => ({
    name: x.feature && x.feature.length > 14 ? x.feature.slice(0, 14) + "…" : x.feature,
    contribution: pickContribution(x),
  }));

  // Only chart items where we actually found a usable number. If NONE of
  // the items have one, that's a real "no explainability data" case (or a
  // backend field-name mismatch worth logging), not just a zero value.
  const data = parsed
    .filter((d) => d.contribution !== null)
    .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution))
    .slice(0, 6);

  const missingFieldOnAllItems = evidence.length > 0 && data.length === 0;

  return (
    <div className="rounded-2xl border border-border bg-white p-6 shadow-card">
      <h3 className="mb-4 text-lg font-bold">Model contribution</h3>
      {data.length ? (
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical" margin={{ left: 10, right: 20 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={120} />
              <Tooltip />
              <Bar dataKey="contribution" radius={[0, 6, 6, 0]}>
                {data.map((d, i) => (
                  <Cell key={i} fill={d.contribution < 0 ? "#8B0000" : "#5C7A29"} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="text-sm text-ink-soft">
          {missingFieldOnAllItems
            ? "Explainability data was returned but is missing a recognizable contribution value — check the backend field name."
            : "No explainability values are available yet."}
        </p>
      )}
    </div>
  );
}
