import { useRef, useState } from "react";
import { UploadCloud, X } from "lucide-react";

const ACCEPT = ".png,.jpg,.jpeg,.webp";

export default function Upload({ onAnalyze, busy }) {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");

  function choose(next) {
    if (!next) return;
    if (!next.type.startsWith("image/")) {
      alert("Please select an image file.");
      return;
    }
    setFile(next);
    setPreview(URL.createObjectURL(next));
  }

  return (
    <div className="rounded-2xl border border-border bg-white p-6 shadow-card">
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); choose(e.dataTransfer.files?.[0]); }}
        onClick={() => inputRef.current?.click()}
        className="cursor-pointer rounded-2xl border-2 border-dashed border-border bg-bg p-8 text-center transition hover:border-primary"
      >
        <input
          ref={inputRef}
          hidden
          type="file"
          accept={ACCEPT}
          onChange={(e) => choose(e.target.files?.[0])}
        />
        <UploadCloud className="mx-auto mb-3 text-primary" size={36} />
        <h2 className="text-xl font-bold">Drop BGMI Screenshot Here</h2>
        <p className="mt-1 text-sm text-ink-soft">or click to browse PNG, JPG, JPEG or WEBP</p>
      </div>

      {file && (
        <div className="mt-5 grid gap-4 md:grid-cols-[180px,1fr]">
          <img src={preview} alt="Selected BGMI screenshot" className="h-44 w-full rounded-xl border border-border object-contain bg-black" />
          <div className="flex flex-col justify-between">
            <div>
              <div className="font-semibold">{file.name}</div>
              <div className="mt-1 text-sm text-ink-soft">{(file.size / 1024 / 1024).toFixed(2)} MB</div>
            </div>
            <div className="flex gap-2">
              <button
                disabled={busy}
                onClick={(e) => { e.stopPropagation(); onAnalyze(file); }}
                className="rounded-lg bg-primary px-5 py-2.5 font-bold text-white hover:bg-primary-hover disabled:opacity-50"
              >
                {busy ? "Analyzing..." : "Analyze Player"}
              </button>
              <button
                disabled={busy}
                onClick={(e) => { e.stopPropagation(); setFile(null); setPreview(""); }}
                className="rounded-lg border border-border px-3 py-2.5"
                aria-label="Remove file"
              >
                <X size={18} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
