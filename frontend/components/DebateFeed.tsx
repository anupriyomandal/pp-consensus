import { motion } from "framer-motion";

export type FeedEvent = {
  id: string;
  event_type:
    | "round_start"
    | "agent_thinking"
    | "agent_response"
    | "moderator_thinking"
    | "moderator_response";
  round_number?: number;
  agent?: "centre_left" | "centre" | "centre_right" | "moderator";
  message?: string;
  content?: string;
  moderator?: {
    agreements: string[];
    disagreements: string[];
    strongest_arguments: string[];
    consensus_statement: string;
    confidence: number;
    summary: string;
  };
};

type DebateFeedProps = {
  events: FeedEvent[];
};

const agentTitle: Record<string, string> = {
  centre_left: "Centre-Left Agent",
  centre: "Centre Agent",
  centre_right: "Centre-Right Agent",
  moderator: "Moderator",
};

const toneStyles: Record<string, string> = {
  centre_left: "border-emerald-300 bg-emerald-50",
  centre: "border-sky-300 bg-sky-50",
  centre_right: "border-amber-300 bg-amber-50",
  moderator: "border-slate-300 bg-slate-50",
};

export default function DebateFeed({ events }: DebateFeedProps) {
  return (
    <section className="space-y-4">
      {events.map((event, index) => {
        if (event.event_type === "round_start") {
          return (
            <motion.div
              key={event.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: Math.min(index * 0.02, 0.25) }}
              className="rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-3 text-sm font-semibold text-indigo-800"
            >
              Debate Round {event.round_number}
            </motion.div>
          );
        }

        if (event.event_type === "agent_thinking" || event.event_type === "moderator_thinking") {
          const agent = event.agent || "moderator";
          return (
            <motion.div
              key={event.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, delay: Math.min(index * 0.02, 0.25) }}
              className="rounded-xl border border-slate-200 bg-white px-4 py-3"
            >
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-600">{agentTitle[agent]}</p>
              <p className="mt-1 inline-flex items-center gap-2 text-sm text-slate-700">
                <span className="h-2 w-2 animate-pulse rounded-full bg-slate-500" />
                {event.message || "Thinking..."}
              </p>
            </motion.div>
          );
        }

        if (event.event_type === "agent_response") {
          const agent = event.agent || "centre";
          return (
            <motion.article
              key={event.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25, delay: Math.min(index * 0.02, 0.25) }}
              className={`rounded-2xl border p-4 shadow-card ${toneStyles[agent]}`}
            >
              <div className="mb-2 flex items-center justify-between gap-3">
                <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-700">{agentTitle[agent]}</h3>
                <span className="rounded-full bg-white/80 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-slate-600">
                  Round {event.round_number}
                </span>
              </div>
              <p className="whitespace-pre-wrap text-sm leading-6 text-slate-800">{event.content}</p>
            </motion.article>
          );
        }

        const moderator = event.moderator;
        return (
          <motion.section
            key={event.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25, delay: Math.min(index * 0.02, 0.25) }}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card"
          >
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-700">Moderator</h3>
              <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white">
                Confidence {moderator?.confidence?.toFixed(1) || "0.0"}%
              </span>
            </div>
            <p className="mb-3 text-sm text-slate-700">{moderator?.summary || event.message}</p>
            <p className="mb-4 rounded-xl bg-slate-100 p-3 text-sm text-slate-800">{moderator?.consensus_statement}</p>
            <div className="grid gap-3 md:grid-cols-3">
              <Block title="Agreements" items={moderator?.agreements || []} />
              <Block title="Disagreements" items={moderator?.disagreements || []} />
              <Block title="Strongest" items={moderator?.strongest_arguments || []} />
            </div>
          </motion.section>
        );
      })}
    </section>
  );
}

function Block({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-600">{title}</p>
      <ul className="space-y-2 text-sm text-slate-700">
        {items.length ? items.map((item, idx) => <li key={idx}>- {item}</li>) : <li>- None listed</li>}
      </ul>
    </div>
  );
}
