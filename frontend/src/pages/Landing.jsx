import { ArrowRight, ShieldCheck } from "lucide-react";
import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-16 md:px-6">
      <section className="grid items-center gap-10 lg:grid-cols-[1.2fr,.8fr]">
        <div>
          <div className="mb-4 inline-flex items-center gap-2 rounded-full bg-primary/10 px-3 py-1 text-sm font-bold text-primary">
            <ShieldCheck size={16} /> Statistical risk assessment
          </div>
          <h1 className="max-w-3xl text-5xl font-black tracking-tight md:text-6xl">
            CheatCheck <span className="text-primary">BGMI</span>
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-ink-soft">
            AI-powered statistical analysis for identifying potentially suspicious BGMI player behavior from career-statistics screenshots.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/analyze" className="inline-flex items-center gap-2 rounded-lg bg-primary px-5 py-3 font-bold text-white hover:bg-primary-hover">
              Analyze Player <ArrowRight size={18} />
            </Link>
            <a href="#how-it-works" className="rounded-lg border border-border bg-white px-5 py-3 font-bold">
              How It Works
            </a>
          </div>
        </div>

        <div className="rounded-3xl border border-border bg-white p-8 shadow-lift">
          <div className="text-xs font-bold uppercase tracking-[.2em] text-primary">Pipeline</div>
          <div className="mt-6 space-y-5">
            {[
              ["01", "Upload", "Upload a BGMI player-statistics screenshot."],
              ["02", "Analyze", "OCR extracts visible statistics and the ML model evaluates patterns."],
              ["03", "Understand", "Review the suspicion score, evidence and model explanation."]
            ].map(([n, title, desc]) => (
              <div className="flex gap-4" key={n}>
                <div className="text-2xl font-black text-accent">{n}</div>
                <div><div className="font-black">{title}</div><div className="text-sm text-ink-soft">{desc}</div></div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="how-it-works" className="mt-24">
        <h2 className="text-3xl font-black">What this app does — and does not do</h2>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-border bg-white p-6 shadow-card">
            <h3 className="font-bold text-primary">It does</h3>
            <p className="mt-2 text-sm text-ink-soft">
              Compare extracted statistics with patterns learned from the supplied dataset and explain which features influenced the output.
            </p>
          </div>
          <div className="rounded-2xl border border-border bg-white p-6 shadow-card">
            <h3 className="font-bold text-red-700">It does not</h3>
            <p className="mt-2 text-sm text-ink-soft">
              Prove that someone is cheating, identify a specific cheat from generic stats, or replace manual investigation.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
