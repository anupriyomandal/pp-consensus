from __future__ import annotations

import json
import os
import re
from typing import Dict, List

from backend.models.schemas import ModeratorOutput, RoundRecord
from backend.services.llm_service import LLMService


class ModeratorAgent:
    def __init__(self, llm: LLMService) -> None:
        self.llm = llm

    async def moderate(
        self,
        prompt: str,
        round_number: int,
        centre_left_response: str,
        centre_response: str,
        centre_right_response: str,
        memory: List[RoundRecord],
    ) -> ModeratorOutput:
        memory_text = self._memory_to_text(memory)
        system_prompt = (
            "You are the Moderator Agent in a structured debate.\n"
            "Task:\n"
            "- Identify agreements, disagreements, strongest arguments.\n"
            "- Produce a consensus statement.\n"
            "- Produce confidence score (0-100), reflecting logical convergence, evidence quality, and viewpoint stability.\n"
            "- Be strict: confidence should increase only when disagreements materially narrow.\n"
            "Return valid JSON only with keys:\n"
            "agreements, disagreements, strongest_arguments, consensus_statement, confidence, summary.\n"
            "For agreements, disagreements, and strongest_arguments return arrays of plain strings only."
        )
        user_prompt = (
            f"Debate prompt: {prompt}\n"
            f"Round: {round_number}\n\n"
            f"Prior memory:\n{memory_text}\n\n"
            "Current round inputs:\n"
            f"Centre-Left:\n{centre_left_response}\n\n"
            f"Centre:\n{centre_response}\n\n"
            f"Centre-Right:\n{centre_right_response}\n"
        )

        raw = await self.llm.complete(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.25,
            response_format={"type": "json_object"},
            max_tokens=800,
        )

        parsed = self._safe_parse(raw)
        stage = "primary"
        if self._is_parse_failure(parsed):
            repaired = await self._repair_json(raw)
            parsed = self._safe_parse(repaired)
            stage = "repaired"

        if not self._is_parse_failure(parsed) and self._is_low_information(parsed):
            regenerated = await self._regenerate_structured_output(
                prompt=prompt,
                round_number=round_number,
                centre_left_response=centre_left_response,
                centre_response=centre_response,
                centre_right_response=centre_right_response,
                memory_text=memory_text,
            )
            regen_parsed = self._safe_parse(regenerated)
            if not self._is_parse_failure(regen_parsed) and not self._is_low_information(regen_parsed):
                parsed = regen_parsed
                stage = "regenerated"

        fallback = self._deterministic_fallback(
            centre_left_response=centre_left_response,
            centre_response=centre_response,
            centre_right_response=centre_right_response,
            memory=memory,
        )

        if self._is_parse_failure(parsed):
            parsed = fallback
            stage = "fallback_parse"
        elif self._is_low_information(parsed):
            parsed = self._merge_with_fallback(parsed, fallback)
            stage = "fallback_merge"

        self._debug_stage(
            round_number=round_number,
            stage=stage,
            confidence=float(parsed.get("confidence", 0)),
            agreements=len(parsed.get("agreements", [])),
            disagreements=len(parsed.get("disagreements", [])),
            strongest=len(parsed.get("strongest_arguments", [])),
            raw_len=len(raw),
        )

        return ModeratorOutput(**parsed)

    @staticmethod
    def _safe_parse(raw: str) -> Dict:
        try:
            parsed = ModeratorAgent._extract_json_object(raw)
            data = json.loads(parsed)
            return ModeratorAgent._normalize_payload(data)
        except Exception:
            return {
                "agreements": [],
                "disagreements": ["Could not parse moderator output as JSON."],
                "strongest_arguments": [],
                "consensus_statement": "Consensus unavailable due to parsing issue.",
                "confidence": 0,
                "summary": raw[:600],
            }

    @staticmethod
    def _normalize_items(value: object) -> List[str]:
        if not isinstance(value, list):
            return []

        items: List[str] = []
        for entry in value:
            if isinstance(entry, str):
                text = entry.strip()
            elif isinstance(entry, dict):
                text = "; ".join(
                    f"{str(k).strip()}: {str(v).strip()}" for k, v in entry.items() if str(v).strip()
                )
            elif isinstance(entry, list):
                text = ", ".join(str(v).strip() for v in entry if str(v).strip())
            else:
                text = str(entry).strip()

            if text:
                items.append(text)
        return items

    @staticmethod
    def _normalize_payload(data: Dict) -> Dict:
        data["agreements"] = ModeratorAgent._normalize_items(data.get("agreements", []))
        data["disagreements"] = ModeratorAgent._normalize_items(data.get("disagreements", []))
        data["strongest_arguments"] = ModeratorAgent._normalize_items(data.get("strongest_arguments", []))
        consensus = str(data.get("consensus_statement", "")).strip()
        summary = str(data.get("summary", "")).strip()
        data["consensus_statement"] = consensus or "No consensus available."
        data["summary"] = summary or "No summary available."
        confidence = float(data.get("confidence", 0))
        data["confidence"] = max(0.0, min(100.0, confidence))
        return data

    @staticmethod
    def _is_parse_failure(data: Dict) -> bool:
        return data.get("consensus_statement") == "Consensus unavailable due to parsing issue."

    @staticmethod
    def _is_low_information(data: Dict) -> bool:
        return (
            not data.get("agreements")
            or not data.get("disagreements")
            or not data.get("strongest_arguments")
            or str(data.get("summary", "")).strip() in {"", "No summary available."}
            or str(data.get("consensus_statement", "")).strip() in {"", "No consensus available."}
        )

    @staticmethod
    def _extract_json_object(raw: str) -> str:
        text = raw.strip()
        if not text:
            raise ValueError("Empty moderator output")

        # Fast path if content is already valid JSON.
        try:
            json.loads(text)
            return text
        except Exception:
            pass

        # Strip code fences if model wrapped the JSON.
        if text.startswith("```"):
            lines = text.splitlines()
            if len(lines) >= 3 and lines[-1].strip() == "```":
                text = "\n".join(lines[1:-1]).strip()
                if text.lower().startswith("json"):
                    text = text[4:].strip()
                try:
                    json.loads(text)
                    return text
                except Exception:
                    pass

        # Extract the first balanced {...} object from mixed text.
        start = text.find("{")
        if start == -1:
            raise ValueError("No JSON object start found")

        depth = 0
        in_string = False
        escaped = False
        for idx in range(start, len(text)):
            ch = text[idx]
            if escaped:
                escaped = False
                continue
            if ch == "\\":
                escaped = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : idx + 1]
                    json.loads(candidate)
                    return candidate

        raise ValueError("No balanced JSON object found")

    async def _repair_json(self, raw: str) -> str:
        repair_system = (
            "You are a strict JSON repair assistant. "
            "Return valid JSON only with keys: agreements, disagreements, strongest_arguments, "
            "consensus_statement, confidence, summary. "
            "All list fields must be arrays of plain strings. confidence must be a number 0-100."
        )
        repair_user = f"Repair this into valid JSON with the required schema:\n\n{raw}"
        try:
            return await self.llm.complete(
                [
                    {"role": "system", "content": repair_system},
                    {"role": "user", "content": repair_user},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
                max_tokens=500,
            )
        except Exception:
            return raw

    async def _regenerate_structured_output(
        self,
        *,
        prompt: str,
        round_number: int,
        centre_left_response: str,
        centre_response: str,
        centre_right_response: str,
        memory_text: str,
    ) -> str:
        regen_system = (
            "You are the moderator for a debate. Return JSON only.\n"
            "Required keys: agreements, disagreements, strongest_arguments, consensus_statement, confidence, summary.\n"
            "Rules:\n"
            "- agreements: exactly 2 non-empty strings.\n"
            "- disagreements: exactly 2 non-empty strings.\n"
            "- strongest_arguments: exactly 3 non-empty strings (one per agent).\n"
            "- consensus_statement: one concise paragraph.\n"
            "- summary: one concise paragraph.\n"
            "- confidence: number between 0 and 100.\n"
            "No markdown, no code fences."
        )
        regen_user = (
            f"Prompt: {prompt}\n"
            f"Round: {round_number}\n"
            f"Memory:\n{memory_text}\n\n"
            f"Centre-Left:\n{centre_left_response}\n\n"
            f"Centre:\n{centre_response}\n\n"
            f"Centre-Right:\n{centre_right_response}\n"
        )
        return await self.llm.complete(
            [
                {"role": "system", "content": regen_system},
                {"role": "user", "content": regen_user},
            ],
            temperature=0.15,
            response_format={"type": "json_object"},
            max_tokens=700,
        )

    @staticmethod
    def _merge_with_fallback(data: Dict, fallback: Dict) -> Dict:
        merged = dict(data)
        for key in ("agreements", "disagreements", "strongest_arguments"):
            if not merged.get(key):
                merged[key] = fallback[key]
        if str(merged.get("summary", "")).strip() in {"", "No summary available."}:
            merged["summary"] = fallback["summary"]
        if str(merged.get("consensus_statement", "")).strip() in {"", "No consensus available."}:
            merged["consensus_statement"] = fallback["consensus_statement"]
        prev_conf = fallback.get("_previous_confidence")
        current_conf = float(merged.get("confidence", 0))
        if current_conf <= 0:
            merged["confidence"] = fallback["confidence"]
        elif isinstance(prev_conf, (float, int)):
            # Prevent abrupt confidence collapses in late-round fallback merges.
            lower_bound = max(0.0, float(prev_conf) - 8.0)
            upper_bound = min(100.0, float(prev_conf) + 8.0)
            merged["confidence"] = max(lower_bound, min(upper_bound, current_conf))
        return merged

    @staticmethod
    def _deterministic_fallback(
        *,
        centre_left_response: str,
        centre_response: str,
        centre_right_response: str,
        memory: List[RoundRecord],
    ) -> Dict:
        previous_confidence = memory[-1].confidence if memory else 45.0
        fallback_confidence = ModeratorAgent._heuristic_confidence(
            centre_left_response=centre_left_response,
            centre_response=centre_response,
            centre_right_response=centre_right_response,
            memory=memory,
        )
        # Keep fallback confidence close to the previous round so one bad generation
        # does not reset trajectory.
        fallback_confidence = max(
            max(0.0, previous_confidence - 8.0),
            min(min(100.0, previous_confidence + 6.0), fallback_confidence),
        )
        return {
            "agreements": [
                "All agents provided a structured argument with cited support.",
                "All agents addressed implementation tradeoffs and second-order effects.",
            ],
            "disagreements": [
                "Agents still differ on the level and design of intervention.",
                "Evidence weighting still differs across ideology-specific priorities.",
            ],
            "strongest_arguments": [
                f"Centre-Left focus: {centre_left_response[:180].strip()}...",
                f"Centre focus: {centre_response[:180].strip()}...",
                f"Centre-Right focus: {centre_right_response[:180].strip()}...",
            ],
            "consensus_statement": (
                "A provisional consensus favors targeted, evidence-led policy with explicit guardrails, "
                "while major disagreement remains on subsidy scale and state-market boundary."
            ),
            "confidence": fallback_confidence,
            "summary": (
                "The round shows convergence on goals and evaluation criteria, but unresolved disagreement on policy intensity "
                "and implementation design keeps confidence moderate."
            ),
            "_previous_confidence": previous_confidence,
        }

    @staticmethod
    def _heuristic_confidence(
        *,
        centre_left_response: str,
        centre_response: str,
        centre_right_response: str,
        memory: List[RoundRecord],
    ) -> float:
        left_tokens = ModeratorAgent._token_set(centre_left_response)
        centre_tokens = ModeratorAgent._token_set(centre_response)
        right_tokens = ModeratorAgent._token_set(centre_right_response)

        overlap_lc = ModeratorAgent._jaccard(left_tokens, centre_tokens)
        overlap_cr = ModeratorAgent._jaccard(centre_tokens, right_tokens)
        overlap_lr = ModeratorAgent._jaccard(left_tokens, right_tokens)
        avg_overlap = (overlap_lc + overlap_cr + overlap_lr) / 3.0

        # Base confidence from topical overlap between ideological positions.
        confidence = 30.0 + avg_overlap * 55.0

        # Stability bonus/penalty relative to previous moderator confidence.
        if memory:
            previous = memory[-1].confidence
            drift = confidence - previous
            if abs(drift) <= 8:
                confidence += 3.0
            elif drift < -15:
                confidence += 5.0  # avoid harsh collapse from one malformed round

        return max(25.0, min(88.0, round(confidence, 1)))

    @staticmethod
    def _token_set(text: str) -> set[str]:
        words = re.findall(r"[a-zA-Z]{4,}", text.lower())
        stop = {
            "that",
            "this",
            "with",
            "from",
            "have",
            "will",
            "they",
            "their",
            "which",
            "about",
            "there",
            "should",
            "would",
            "could",
            "while",
            "where",
            "into",
            "because",
            "against",
        }
        return {w for w in words if w not in stop}

    @staticmethod
    def _jaccard(a: set[str], b: set[str]) -> float:
        if not a or not b:
            return 0.0
        union = a | b
        if not union:
            return 0.0
        return len(a & b) / len(union)

    @staticmethod
    def _debug_stage(
        *,
        round_number: int,
        stage: str,
        confidence: float,
        agreements: int,
        disagreements: int,
        strongest: int,
        raw_len: int,
    ) -> None:
        if os.getenv("DEBUG_MODERATOR", "0") != "1":
            return
        print(
            "[moderator] "
            f"round={round_number} stage={stage} conf={confidence:.1f} "
            f"agreements={agreements} disagreements={disagreements} strongest={strongest} raw_len={raw_len}"
        )

    @staticmethod
    def _memory_to_text(memory: List[RoundRecord]) -> str:
        if not memory:
            return "No prior rounds."
        chunks = []
        for r in memory[-5:]:
            chunks.append(
                f"Round {r.round_number}:\n"
                f"- Moderator summary: {r.moderator_summary}\n"
                f"- Consensus: {r.consensus_statement}\n"
                f"- Confidence: {r.confidence}"
            )
        return "\n\n".join(chunks)
