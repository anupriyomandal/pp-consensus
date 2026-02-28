import { useState } from "react";

type PromptBoxProps = {
  loading: boolean;
  onStart: (prompt: string, confidenceTarget: number) => Promise<void>;
};

export default function PromptBox({ loading, onStart }: PromptBoxProps) {
  const [prompt, setPrompt] = useState("");
  const [confidenceTarget, setConfidenceTarget] = useState(80);

  return (
    <section className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-card backdrop-blur">
      <h1 className="mb-1 text-2xl font-semibold text-slate-900">Anupriyo Mandal's Multi-Agent Debate System</h1>
      <p className="mb-5 text-sm text-slate-600">Simulate ideological debate until confidence converges.</p>

      <label className="mb-2 block text-sm font-medium text-slate-700">Debate prompt</label>
      <textarea
        className="mb-4 h-32 w-full rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm outline-none transition focus:border-sky-400"
        placeholder="Example: Should governments subsidize large-scale AI infrastructure?"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
      />

      <div className="mb-5">
        <label className="mb-1 block text-sm font-medium text-slate-700">Target confidence: {confidenceTarget}%</label>
        <input
          className="w-full accent-sky-600"
          type="range"
          min={50}
          max={100}
          step={1}
          value={confidenceTarget}
          onChange={(e) => setConfidenceTarget(Number(e.target.value))}
        />
      </div>

      <button
        className="rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
        disabled={loading || prompt.trim().length < 5}
        onClick={() => onStart(prompt, confidenceTarget)}
      >
        {loading ? "Debating..." : "Start Debate"}
      </button>
    </section>
  );
}
