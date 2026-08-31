import { useEffect, useState } from "react";
import { modelInfo } from "../api/client";

export default function Admin() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    modelInfo().then(setData).catch((e) => setError(e?.response?.data?.detail || e.message));
  }, []);

  if (error) {
    return <div className="mx-auto max-w-4xl px-4 py-12"><div className="rounded-xl border border-amber-200 bg-amber-50 p-5 text-amber-900">{error}</div></div>;
  }
  if (!data) {
    return <div className="mx-auto max-w-4xl px-4 py-12">Loading model information…</div>;
  }

  const m = data.metrics || {};
  return (
    <div className="mx-auto max-w-6xl space-y-8 px-4 py-12 md:px-6">
      <div>
        <h1 className="text-4xl font-black">ML Admin</h1>
        <p className="mt-2 text-ink-soft">Evaluation metrics from the held-out test set.</p>
      </div>

      <div className="grid gap-4 md:grid-cols-5">
        {[
          ["Accuracy", m.accuracy],
          ["Precision", m.precision],
          ["Recall", m.recall],
          ["F1", m.f1],
          ["ROC-AUC", m.roc_auc]
        ].map(([label, value]) => (
          <div key={label} className="rounded-2xl border border-border bg-white p-5 shadow-card">
            <div className="text-sm text-ink-soft">{label}</div>
            <div className="mt-1 text-2xl font-black">{typeof value === "number" ? value.toFixed(3) : "—"}</div>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-border bg-white p-6 shadow-card">
          <h2 className="text-lg font-black">Selected model</h2>
          <div className="mt-2 text-2xl font-black text-primary">{data.model_name}</div>
          <p className="mt-2 text-sm text-ink-soft">
            Experimental model: {data.is_experimental ? "Yes" : "No"}
          </p>
        </div>
        <div className="rounded-2xl border border-border bg-white p-6 shadow-card">
          <h2 className="text-lg font-black">Dataset summary</h2>
          <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
            <div><div className="text-ink-soft">Records</div><div className="font-bold">{data.dataset_summary.total_records ?? "—"}</div></div>
            <div><div className="text-ink-soft">Legit</div><div className="font-bold">{data.dataset_summary.legit_count ?? "—"}</div></div>
            <div><div className="text-ink-soft">Hacker</div><div className="font-bold">{data.dataset_summary.hacker_count ?? "—"}</div></div>
            <div><div className="text-ink-soft">Duplicates</div><div className="font-bold">{data.dataset_summary.duplicates ?? "—"}</div></div>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-border bg-white p-6 shadow-card">
        <h2 className="text-lg font-black">Global feature importance</h2>
        <div className="mt-4 space-y-3">
          {(data.feature_importance || []).slice(0, 10).map((item) => (
            <div key={item.feature}>
              <div className="flex justify-between text-sm"><span>{item.feature}</span><span className="font-bold">{(item.importance * 100).toFixed(1)}%</span></div>
              <div className="mt-1 h-2 overflow-hidden rounded-full bg-bg"><div className="h-full rounded-full bg-primary" style={{width: `${item.importance * 100}%`}} /></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
