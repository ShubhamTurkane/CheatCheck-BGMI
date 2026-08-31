import { motion } from "framer-motion";

const stages = [
  "Upload received",
  "Reading screenshot",
  "Extracting player statistics",
  "Processing features",
  "Running ML model",
  "Generating analysis",
];

export default function LoadingState() {
  return (
    <div className="rounded-2xl border border-border bg-white p-6 shadow-card">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h3 className="font-bold text-lg">Analyzing screenshot</h3>
          <p className="text-sm text-ink-soft">OCR and model inference are running.</p>
        </div>
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 1.2, ease: "linear" }}
          className="h-8 w-8 rounded-full border-4 border-border border-t-primary"
        />
      </div>
      <div className="space-y-3">
        {stages.map((stage, index) => (
          <div key={stage} className="flex items-center gap-3 text-sm">
            <span className="grid h-6 w-6 place-items-center rounded-full bg-primary/10 font-bold text-primary">{index + 1}</span>
            <span>{stage}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
