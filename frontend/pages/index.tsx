import Head from "next/head";
import { useMemo, useState } from "react";

import DebateFeed, { FeedEvent } from "../components/DebateFeed";
import PromptBox from "../components/PromptBox";

type BackendEvent = {
  event_type:
    | "started"
    | "round_start"
    | "agent_thinking"
    | "agent_response"
    | "moderator_thinking"
    | "moderator_response"
    | "round"
    | "final"
    | "error";
  round_number?: number;
  agent?: "centre_left" | "centre" | "centre_right" | "moderator";
  content?: string;
  round_data?: {
    round_number: number;
    centre_left_response: string;
    centre_response: string;
    centre_right_response: string;
    moderator_summary: string;
    consensus_statement: string;
    confidence: number;
  };
  moderator?: {
    agreements: string[];
    disagreements: string[];
    strongest_arguments: string[];
    consensus_statement: string;
    confidence: number;
    summary: string;
  };
  final_consensus?: string;
  final_confidence?: number;
  message?: string;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function HomePage() {
  const [loading, setLoading] = useState(false);
  const [feedEvents, setFeedEvents] = useState<FeedEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [finalConsensus, setFinalConsensus] = useState<string>("");
  const [finalConfidence, setFinalConfidence] = useState<number | null>(null);

  const hasData = useMemo(() => feedEvents.length > 0 || !!finalConsensus, [feedEvents.length, finalConsensus]);

  const startDebate = async (prompt: string, confidenceTarget: number) => {
    setLoading(true);
    setError(null);
    setFeedEvents([]);
    setFinalConsensus("");
    setFinalConfidence(null);

    try {
      const response = await fetch(`${API_BASE_URL}/start-debate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, confidence_target: confidenceTarget }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Request failed (${response.status})`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split("\n\n");
        buffer = chunks.pop() || "";

        for (const chunk of chunks) {
          const line = chunk
            .split("\n")
            .find((entry) => entry.startsWith("data: "))
            ?.replace("data: ", "");

          if (!line) continue;

          const parsed: BackendEvent = JSON.parse(line);

          if (
            parsed.event_type === "round_start" ||
            parsed.event_type === "agent_thinking" ||
            parsed.event_type === "agent_response" ||
            parsed.event_type === "moderator_thinking" ||
            parsed.event_type === "moderator_response"
          ) {
            const feedType = parsed.event_type as FeedEvent["event_type"];
            setFeedEvents((prev) => [
              ...prev.filter((item) => {
                if (
                  feedType === "agent_response" &&
                  item.event_type === "agent_thinking" &&
                  item.round_number === parsed.round_number &&
                  item.agent === parsed.agent
                ) {
                  return false;
                }
                if (
                  feedType === "moderator_response" &&
                  item.event_type === "moderator_thinking" &&
                  item.round_number === parsed.round_number
                ) {
                  return false;
                }
                return true;
              }),
              {
                id: `${Date.now()}-${prev.length}-${parsed.event_type}`,
                event_type: feedType,
                round_number: parsed.round_number,
                agent: parsed.agent,
                message: parsed.message,
                content: parsed.content,
                moderator: parsed.moderator,
              },
            ]);
          }

          if (parsed.event_type === "final") {
            setFinalConsensus(parsed.final_consensus || "");
            setFinalConfidence(parsed.final_confidence ?? null);
          }

          if (parsed.event_type === "error") {
            setError(parsed.message || "Unknown streaming error");
          }
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to start debate";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Anupriyo Mandal's Multi-Agent Debate System</title>
        <meta name="description" content="Structured ideological debate with iterative consensus scoring." />
      </Head>

      <main className="mx-auto min-h-screen max-w-6xl bg-grid px-4 py-10 md:px-8">
        <div className="mb-8">
          <PromptBox loading={loading} onStart={startDebate} />
        </div>

        {error && <p className="mb-6 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}

        {hasData && (
          <div className="space-y-6">
            <DebateFeed events={feedEvents} />

            {finalConsensus && (
              <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-card">
                <h2 className="mb-2 text-lg font-semibold text-slate-900">Final Consensus</h2>
                <p className="mb-3 text-sm text-slate-700">{finalConsensus}</p>
                {finalConfidence !== null && (
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Final confidence: {finalConfidence.toFixed(1)}%
                  </p>
                )}
              </section>
            )}
          </div>
        )}
      </main>
    </>
  );
}
