import Disclaimer from "./Disclaimer";
import EvidenceCards from "./EvidenceCards";
import RiskMeter from "./RiskMeter";
import StatsCharts from "./StatsCharts";

export default function Dashboard({ result }) {
  const mode = result.extracted_stats?.mode || "Unknown";
  return (
    <div className="space-y-6">
      <Disclaimer text={result.disclaimer} />

      <div className="grid gap-6 lg:grid-cols-[280px,1fr]">
        <RiskMeter
          score={result.suspicion_score}
          color={result.risk_color}
          risk={result.risk_level}
        />
        <div className="rounded-2xl border border-border bg-white p-6 shadow-card">
          <h2 className="text-xl font-black">Player overview</h2>
          <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
            {[
              ["Mode", mode],
              ["Prediction", result.prediction_label],
              ["Model confidence", `${Math.round((result.model_confidence || 0) * 100)}%`],
              ["Probability", `${Math.round((result.probability || 0) * 100)}%`],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl bg-bg p-4">
                <div className="text-xs font-semibold uppercase tracking-wide text-ink-soft">{label}</div>
                <div className="mt-1 font-black">{value}</div>
              </div>
            ))}
          </div>

          {!!result.extracted_stats?.warnings?.length && (
            <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
              <div className="font-bold">OCR warnings</div>
              <ul className="mt-2 list-disc space-y-1 pl-5">
                {result.extracted_stats.warnings.map((w) => <li key={w}>{w}</li>)}
              </ul>
            </div>
          )}
        </div>
      </div>

      <StatsCharts evidence={result.evidence} />

      <section>
        <div className="mb-3">
          <h3 className="text-xl font-black">Evidence / analysis</h3>
          <p className="text-sm text-ink-soft">These are the strongest available model signals; they are not proof of a cheat type.</p>
        </div>
        <EvidenceCards items={result.evidence} />
      </section>
    </div>
  );
}
