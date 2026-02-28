import { motion } from "framer-motion";

type AgentCardProps = {
  title: string;
  response: string;
  tone: "left" | "center" | "right";
  stepLabel?: string;
};

const toneStyles = {
  left: "border-emerald-300 bg-emerald-50",
  center: "border-sky-300 bg-sky-50",
  right: "border-amber-300 bg-amber-50",
};

export default function AgentCard({ title, response, tone, stepLabel }: AgentCardProps) {
  return (
    <motion.article
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={`rounded-2xl border p-4 shadow-card ${toneStyles[tone]}`}
    >
      <div className="mb-2 flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-700">{title}</h3>
        {stepLabel && (
          <span className="rounded-full bg-white/80 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-slate-600">
            {stepLabel}
          </span>
        )}
      </div>
      <p className="whitespace-pre-wrap text-sm leading-6 text-slate-800">{response}</p>
    </motion.article>
  );
}
