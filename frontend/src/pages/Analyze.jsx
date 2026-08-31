import { useState } from "react";
import Upload from "../components/Upload";
import LoadingState from "../components/LoadingState";
import Dashboard from "../components/Dashboard";
import { analyzeScreenshot } from "../api/client";

export default function Analyze() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  async function run(file) {
    setError("");
    setBusy(true);
    try {
      setResult(await analyzeScreenshot(file));
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || "Analysis failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-8 px-4 py-12 md:px-6">
      <div>
        <h1 className="text-4xl font-black">Analyze a player</h1>
        <p className="mt-2 text-ink-soft">
          Upload a clear screenshot of Solo, Duo or Squad career statistics.
        </p>
      </div>

      {!result && <Upload onAnalyze={run} busy={busy} />}
      {busy && <LoadingState />}
      {error && <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-900">{error}</div>}
      {result && !busy && <Dashboard result={result} />}
    </div>
  );
}
