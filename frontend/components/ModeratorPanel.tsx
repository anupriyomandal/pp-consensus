import { motion } from "framer-motion";

type ModeratorPanelProps = {
  summary: string;
  consensus: string;
  confidence: number;
  agreements: string[];
  disagreements: string[];
  strongestArguments: string[];
};

export default function ModeratorPanel({
  summary,
  consensus,
  confidence,
  agreements,
  disagreements,
  strongestArguments,
}: ModeratorPanelProps) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card"
    >
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-700">Moderator</h3>
        <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white">
          Confidence {confidence.toFixed(1)}%
        </span>
      </div>
      <p className="mb-3 text-sm text-slate-700">{summary}</p>
      <p className="mb-4 rounded-xl bg-slate-100 p-3 text-sm text-slate-800">{consensus}</p>

      <div className="grid gap-3 md:grid-cols-3">
        <Block title="Agreements" items={agreements} />
        <Block title="Disagreements" items={disagreements} />
        <Block title="Strongest" items={strongestArguments} />
      </div>
    </motion.section>
  );
}

function Block({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-600">{title}</p>
      <ul className="space-y-2 text-sm text-slate-700">
        {items.length ? (
          items.map((item, idx) => <li key={idx}>- {item}</li>)
        ) : (
          <li>- None listed</li>
        )}
      </ul>
    </div>
  );
}
