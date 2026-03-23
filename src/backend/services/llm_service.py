from __future__ import annotations
import time
from typing import Optional
from groq import Groq
from configs.settings import settings
from configs.logging_config import get_logger

logger = get_logger(__name__)

THREAT_ANALYST_PROMPT = """You are CyberMind, an expert cybersecurity analyst and threat intelligence specialist.
You have deep knowledge of the MITRE ATT&CK framework, CVE database, threat actor groups, 
malware families, and incident response methodologies.

When analyzing threats or generating playbooks:
- Be precise and technical, your audience is security professionals
- Reference specific MITRE technique IDs where relevant
- Structure responses clearly with numbered steps or labeled sections
- Prioritize actionable intelligence over general advice
- Acknowledge uncertainty when evidence is limited"""


class LLMService:
    def __init__(self) -> None:
        if not settings.groq_api_key:
            logger.warning("groq_api_key_not_set")
        self._client = Groq(api_key=settings.groq_api_key)
        self._model = settings.llm_model
        self._max_tokens = settings.llm_max_tokens
        logger.info("llm_service_ready", model=self._model)

    def _call(self, user_prompt: str, max_tokens: Optional[int] = None) -> tuple[str, float]:
        start = time.perf_counter()
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                max_tokens=max_tokens or self._max_tokens,
                temperature=settings.llm_temperature,
                messages=[
                    {"role": "system", "content": THREAT_ANALYST_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
            )
            text = response.choices[0].message.content
            elapsed = (time.perf_counter() - start) * 1000
            logger.info(
                "llm_call_success",
                model=self._model,
                latency_ms=round(elapsed, 2),
            )
            return text, elapsed
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error("llm_call_failed", error=str(e), latency_ms=round(elapsed, 2))
            raise

    def analyze_threat(
        self,
        threat_id: str,
        threat_name: str,
        threat_description: str,
        rag_context: list[str],
        analyst_query: str = "",
    ) -> tuple[str, float]:
        context = "\n\n---\n\n".join(rag_context) if rag_context else "No additional context available."
        query_section = f"\nAnalyst Question: {analyst_query}" if analyst_query else ""

        prompt = f"""Analyze the following cybersecurity threat and provide a comprehensive intelligence report.

Threat ID: {threat_id}
Name: {threat_name}
Description: {threat_description}

Retrieved Context:
{context}
{query_section}

Structure your response with these sections:
1. Threat Summary
2. Attack Mechanics
3. Indicators of Compromise
4. Detection Opportunities
5. Recommended Mitigations
6. Threat Actor Context"""

        return self._call(prompt)

    def generate_playbook(
        self,
        threat_id: str,
        threat_name: str,
        alert_context: str = "",
        available_tools: list[str] | None = None,
    ) -> tuple[str, float]:
        tools_section = f"\nAvailable Tools: {', '.join(available_tools)}" if available_tools else ""

        prompt = f"""Generate a detailed incident response playbook for the following threat.

Threat ID: {threat_id}
Name: {threat_name}
Alert Context: {alert_context or 'No specific alert context provided.'}
{tools_section}

Structure as numbered steps covering containment, eradication, recovery, and lessons learned.
For each step include: action, responsible team, tools, and estimated time."""

        return self._call(prompt)

    def generate_entity_profile(
        self,
        entity_id: str,
        entity_name: str,
        entity_type: str,
        description: str,
        associated_techniques: list[str],
    ) -> tuple[str, float]:
        techniques = ", ".join(associated_techniques[:15]) or "Unknown"

        prompt = f"""Generate a comprehensive threat intelligence profile for this entity.

ID: {entity_id}
Name: {entity_name}
Type: {entity_type}
Description: {description}
Known MITRE Techniques: {techniques}

Cover: overview, TTPs, targeting profile, infrastructure, and detection recommendations."""

        return self._call(prompt)

    def triage_alert(
        self,
        alert_title: str,
        alert_description: str,
        threat_context: str,
        indicators: list[str],
    ) -> tuple[str, float]:
        iocs = "\n".join(f"- {ioc}" for ioc in indicators) or "- None provided"

        prompt = f"""Triage this security alert and provide a prioritized response recommendation.

Alert: {alert_title}
Description: {alert_description}
Threat Context: {threat_context}
Indicators:
{iocs}

Provide: priority level (P1-P4), reasoning, immediate actions, escalation decision, and false positive assessment."""

        return self._call(prompt, max_tokens=1024)


def get_llm_service() -> LLMService:
    return LLMService()