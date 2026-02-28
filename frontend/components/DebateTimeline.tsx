import AgentCard from "./AgentCard";
import ModeratorPanel from "./ModeratorPanel";

export type RoundView = {
  round_number: number;
  centre_left_response: string;
  centre_response: string;
  centre_right_response: string;
  moderator_summary: string;
  consensus_statement: string;
  confidence: number;
  agreements: string[];
  disagreements: string[];
  strongest_arguments: string[];
};

type DebateTimelineProps = {
  rounds: RoundView[];
};

export default function DebateTimeline({ rounds }: DebateTimelineProps) {
  return (
    <section className="space-y-6">
      {rounds.map((round) => (
        <article key={round.round_number} className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-card">
          <h2 className="mb-4 text-lg font-semibold text-slate-900">Round {round.round_number}</h2>
          <div className="mb-4 space-y-3">
            <AgentCard
              title="Centre-Left Agent"
              response={round.centre_left_response}
              tone="left"
              stepLabel="Message 1"
            />
            <AgentCard title="Centre Agent" response={round.centre_response} tone="center" stepLabel="Message 2" />
            <AgentCard
              title="Centre-Right Agent"
              response={round.centre_right_response}
              tone="right"
              stepLabel="Message 3"
            />
          </div>

          <ModeratorPanel
            summary={round.moderator_summary}
            consensus={round.consensus_statement}
            confidence={round.confidence}
            agreements={round.agreements}
            disagreements={round.disagreements}
            strongestArguments={round.strongest_arguments}
          />
        </article>
      ))}
    </section>
  );
}
