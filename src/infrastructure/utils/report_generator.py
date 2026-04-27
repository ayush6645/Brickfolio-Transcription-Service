"""
Brickfolio Reporting and Artifact Generation Utility

This module handles the formatting and export of processed business 
intelligence. It transforms raw AI JSON outputs into human-readable 
Markdown reports suitable for management review.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import settings as config

def model_label_for_provider(provider_name: str) -> str:
    """
    Returns the human-readable label for a given AI provider.
    
    Args:
        provider_name: The internal provider key (e.g., 'gemini').
    """
    return config.PROVIDER_MODEL_LABELS.get(provider_name.lower(), provider_name.upper())

def transcript_export_path(base_name: str, provider_name: str) -> Path:
    """Calculates the standard output path for a raw transcript text file."""
    return config.OUTPUT_TRANSCRIPTS_DIR / f"{base_name}_{model_label_for_provider(provider_name)}.txt"

def summary_export_path(base_name: str, provider_name: str) -> Path:
    """Calculates the standard output path for a managed summary report."""
    return config.OUTPUT_SUMMARIES_DIR / f"{base_name}_{model_label_for_provider(provider_name)}_summary.txt"

def normalize_transcript_text(transcript: str) -> str:
    """Ensures transcript text is valid and formatted for reports."""
    text = (transcript or "").strip()
    return text if text else "Transcript unavailable."

def safe_json_dump(data: Dict[str, Any], output_path: Path) -> None:
    """
    Saves a dictionary as a pretty-printed JSON file, ensuring directories exist.

    Args:
        data: The dictionary to save.
        output_path: Target file path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)

def _list_value(value: Any) -> str:
    """Internal helper to convert lists or missing values into comma-separated strings."""
    if isinstance(value, list):
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        return ", ".join(cleaned) if cleaned else "Not identified"
    if value is None:
        return "Not identified"
    text = str(value).strip()
    return text if text else "Not identified"

def _dict_value(data: Dict[str, Any], key: str, default: str = "Not identified") -> str:
    """Internal helper to safely extract and stringify values from a dictionary."""
    value = data.get(key, default)
    if isinstance(value, list):
        return _list_value(value)
    text = str(value).strip() if value is not None else ""
    return text if text else default

def build_manager_summary(
    *,
    audio_file_name: str,
    provider_name: str,
    transcript: str,
    analysis: Dict[str, Any],
) -> str:
    """
    Assembles a comprehensive Markdown report from AI-generated intelligence JSON.

    Args:
        audio_file_name: Name of the original audio file.
        provider_name: AI model used for analysis.
        transcript: The refined phonetic transcript text.
        analysis: The raw intelligence JSON from the audit stage.

    Returns:
        str: A fully formatted Markdown report content.
    """
    # Extract nested sections for cleaner access
    metadata = analysis.get("call_metadata", {})
    data_points = analysis.get("data_points", {})
    customer_interest = analysis.get("customer_interest", {})
    sentiment = analysis.get("sentiment_analysis", {})
    psychology = analysis.get("customer_psychology", {})
    customer_eval = analysis.get("customer_evaluation", {})
    dynamics = analysis.get("conversation_dynamics", {})
    agent_eval = analysis.get("agent_evaluation", {})
    risks = analysis.get("risks_and_opportunities", {})
    conversion = analysis.get("conversion_insights", {})
    math_audit = analysis.get("mathematical_audit", {})
    next_steps = analysis.get("next_best_actions", [])
    interaction_timeline = analysis.get("interaction_timeline", [])

    # Legacy support for single next best action keys
    if not next_steps:
        single_action = analysis.get("next_best_action")
        if single_action:
            next_steps = [single_action]

    if isinstance(next_steps, str):
        next_steps = [next_steps]

    # Build report sections
    lines = [
        f"# Brickfolio Call Intelligence Report",
        "",
        "## Call Metadata",
        f"- Source File: {audio_file_name}",
        f"- Provider: {provider_name}",
        f"- Call Stage: {_dict_value(analysis, 'call_stage', 'Unknown')}",
        f"- Duration: {_dict_value(metadata, 'duration', 'Unknown')}",
        f"- Language Mix: {_dict_value(metadata, 'languages', 'Hindi / English / Marathi (auto-detected)')}",
        "",
        "## Lead Intelligence",
        f"- Lead Qualification: {_dict_value(analysis, 'lead_qualification', customer_interest.get('level', 'Not identified'))}",
        f"- Lead Score: {_dict_value(customer_interest, 'score_1_to_10', 'Not scored')}/10",
        f"- Budget: {_dict_value(data_points, 'budget')}",
        f"- Preferred Location: {_dict_value(data_points, 'location')}",
        f"- Requirements: {_dict_value(data_points, 'requirements')}",
        f"- Possession Timeline: {_dict_value(data_points, 'possession')}",
        "",
        "## Customer Psychology",
        f"- Intent Level: {_dict_value(customer_interest, 'level', 'Not identified')}",
        f"- Buying Signals: {_dict_value(analysis, 'buying_signals', customer_interest.get('reasoning', 'Not identified'))}",
        f"- Objections: {_dict_value(analysis, 'objections', 'Not identified')}",
        f"- Psychological Read: {_dict_value(psychology, 'summary', 'Not identified')}",
        "",
        "## Customer Business Assessment",
        f"- Overall Quality: {_dict_value(customer_eval, 'overall_quality', 'Not identified')}",
        f"- Decision Quality: {_dict_value(customer_eval, 'decision_quality', 'Not identified')}",
        f"- Trust Readiness: {_dict_value(customer_eval, 'trust_readiness', 'Not identified')}",
        f"- Positive Points: {_list_value(customer_eval.get('positive_points', []))}",
        f"- Negative Points: {_list_value(customer_eval.get('negative_points', []))}",
        f"- Conversion Levers: {_list_value(customer_eval.get('conversion_levers', []))}",
        f"- Next Call Sales Tip: {_dict_value(customer_eval, 'next_call_sales_tip', 'Not identified')}",
        "",
        "## Sentiment Analysis",
        f"- Customer Sentiment: {_dict_value(sentiment, 'customer_sentiment', 'Not identified')}",
        f"- Agent Sentiment: {_dict_value(sentiment, 'agent_sentiment', 'Not identified')}",
        f"- Emotional Flow: {_dict_value(sentiment, 'emotional_flow', 'Not identified')}",
        f"- Connection Quality: {_dict_value(sentiment, 'connection_quality', 'Not identified')}",
        "",
        "## Conversation Dynamics",
        f"- Speaker Balance: {_dict_value(dynamics, 'speaker_balance', 'Not identified')}",
        f"- Objection Handling: {_dict_value(dynamics, 'objection_handling', 'Not identified')}",
        f"- Follow-Up Commitment: {_dict_value(dynamics, 'follow_up_commitment', 'Not identified')}",
        "",
        "## Agent Performance Audit",
        f"- Overall Performance: {_dict_value(agent_eval, 'overall_performance', 'Not identified')}",
        f"- Pitching Quality: {_dict_value(agent_eval, 'pitching_quality', 'Not identified')}",
        f"- Pitching Skills: {_dict_value(agent_eval, 'pitching_skills', 'Not identified')}",
        f"- Qualification Skills: {_dict_value(agent_eval, 'qualification_skills', 'Not identified')}",
        f"- Objection Handling: {_dict_value(agent_eval, 'objection_handling', 'Not identified')}",
        f"- Closing Skills: {_dict_value(agent_eval, 'closing_skills', 'Not identified')}",
        f"- Genuineness: {_dict_value(agent_eval, 'genuineness', 'Not identified')}",
        f"- Positive Points: {_list_value(agent_eval.get('positive_points', []))}",
        f"- Negative Points: {_list_value(agent_eval.get('negative_points', []))}",
        f"- Strengths: {_dict_value(agent_eval, 'strengths', 'Not identified')}",
        f"- Training Recommendations: {_dict_value(agent_eval, 'training_recommendations', 'Not identified')}",
        "",
        "## Conversion Insights",
        f"- Conversion Probability: {_dict_value(conversion, 'conversion_probability', _dict_value(analysis, 'conversion_probability', 'Not estimated'))}",
        f"- Conversion Stage: {_dict_value(conversion, 'stage', _dict_value(analysis, 'call_stage', 'Not identified'))}",
        f"- Buying Signals: {_list_value(conversion.get('buying_signals', analysis.get('buying_signals', [])))}",
        f"- Blockers: {_list_value(conversion.get('blockers', analysis.get('objections', [])))}",
        f"- Next Milestone: {_dict_value(conversion, 'next_milestone', 'Not identified')}",
        "",
        "## Mathematical Audit",
        f"- Interest Score Calculation: {_dict_value(math_audit, 'interest_score_calculation', 'Not identified')}",
        f"- Lead Genuineness Percentage: {_dict_value(math_audit, 'lead_genuineness_percentage', 'Not identified')}",
        f"- Agent Effectiveness Score: {_dict_value(math_audit, 'agent_effectiveness_score', 'Not identified')}",
        f"- Customer Conversion Readiness Score: {_dict_value(math_audit, 'customer_conversion_readiness_score', 'Not identified')}",
        f"- Budget Benchmark Comparison: {_dict_value(math_audit, 'budget_benchmark_comparison', 'Not identified')}",
        f"- Conversion Probability Percent: {_dict_value(math_audit, 'conversion_probability_percent', 'Not identified')}",
        "",
        "## Risks & Opportunities",
        f"- Risks: {_dict_value(risks, 'risks', analysis.get('compliance', {}).get('details', 'Not identified'))}",
        f"- Opportunities: {_dict_value(risks, 'opportunities', 'Not identified')}",
        "",
        "## Actionable Recommendations",
    ]

    if next_steps:
        lines.extend(f"- {str(step).strip()}" for step in next_steps if str(step).strip())
    else:
        lines.append("- No explicit next action captured.")

    # Render vertical interaction timeline if available
    if interaction_timeline:
        lines.extend(["", "## Interaction Timeline"])
        for item in interaction_timeline:
            if not isinstance(item, dict):
                continue
            stage = _dict_value(item, "stage", "Unknown stage")
            estimate = _dict_value(item, "time_estimate", "Unknown timing")
            summary = _dict_value(item, "summary", "No summary provided")
            lines.append(f"- {stage}: {estimate} | {summary}")

    # Embed original transcript snapshot for reference
    lines.extend(
        [
            "",
            "## Transcript Snapshot",
            normalize_transcript_text(transcript),
            "",
        ]
    )

    return "\n".join(lines)
