import { motion } from "framer-motion";

const labels = {
  likely_legit: "Likely Legit",
  suspicious: "Suspicious",
  highly_suspicious: "Highly Suspicious",
  extremely_suspicious: "Extremely Suspicious",
};

export default function RiskMeter({ score, color, risk }) {
  return (
    <div className="rounded-2xl border border-border bg-white p-6 shadow-card text-center">
      <div className="mx-auto grid h-48 w-48 place-items-center rounded-full"
        style={{background: `conic-gradient(${color} ${score * 3.6}deg, #e6ece6 0deg)`}}>
        <div className="grid h-36 w-36 place-items-center rounded-full bg-white">
          <div>
            <div className="text-4xl font-black">{Math.round(score)}%</div>
            <div className="mt-1 text-xs font-semibold uppercase tracking-wider text-ink-soft">Suspicion score</div>
          </div>
        </div>
      </div>
      <motion.div initial={{opacity:0, y:6}} animate={{opacity:1, y:0}} className="mt-5 text-xl font-black">
        {labels[risk] || risk}
      </motion.div>
    </div>
  );
}
