"""Fit scoring: combine evidence into a single, explainable score.

score = (weighted positive fit)  ->  apply stated-negative penalties
                                 ->  multiply by behavioural availability
                                 ->  force honeypots to the bottom

Every step mirrors a sentence in the JD, which is what lets the reasoning
column stay honest and lets us defend the design.
"""

from typing import Dict, Tuple

from . import lexicons as L
from .lexicons import CONCEPT_WEIGHTS, NICE_WEIGHTS


def _core_concept_score(concept_scores: Dict[str, float]) -> float:
    num = sum(CONCEPT_WEIGHTS[c] * concept_scores.get(c, 0.0) for c in CONCEPT_WEIGHTS)
    den = sum(CONCEPT_WEIGHTS.values())
    return num / den


def _nice_score(nice_scores: Dict[str, float]) -> float:
    s = sum(NICE_WEIGHTS[c] * nice_scores.get(c, 0.0) for c in NICE_WEIGHTS)
    return min(1.0, s / (0.5 * sum(NICE_WEIGHTS.values())))


def _title_role_score(f: dict) -> float:
    if f["is_software_ai_title"]:
        return 1.0
    if f["ever_software_ai_title"] and not f["is_non_tech_title"]:
        return 0.75          # adjacent / transitioning engineer
    if f["ever_software_ai_title"] and f["is_non_tech_title"]:
        return 0.45          # moved out of engineering
    if f["is_non_tech_title"]:
        return 0.10          # e.g. Marketing Manager — the keyword-stuffer trap
    return 0.45              # ambiguous title, judged on other evidence


def _behavioural_multiplier(s: dict) -> Tuple[float, list]:
    """Availability / engagement modifier in roughly [0.45, 1.12]."""
    notes = []
    m = 1.0

    m *= 1.05 if s["open_to_work"] else 0.85
    if not s["open_to_work"]:
        notes.append("not marked open to work")

    rr = s["recruiter_response_rate"]
    m *= 0.70 + 0.40 * rr
    if rr < 0.15:
        notes.append(f"low recruiter response rate ({rr:.2f})")

    rec = s["recency_days"]
    if rec <= 30:
        m *= 1.03
    elif rec <= 90:
        m *= 1.0
    elif rec <= 180:
        m *= 0.90
        notes.append("inactive 3-6 months")
    else:
        m *= 0.70
        notes.append("inactive 6+ months")

    m *= 0.85 + 0.15 * s["interview_completion_rate"]
    m *= 0.90 + 0.10 * (s["profile_completeness"] / 100.0)

    # mild demand signal from recruiters
    demand = min(1.0, (s["saved_by_recruiters_30d"] / 8.0))
    m *= 1.0 + 0.04 * demand

    np_days = s["notice_period_days"]
    if np_days <= 30:
        m *= 1.02
    elif np_days <= 60:
        m *= 1.0
    elif np_days <= 90:
        m *= 0.96
    else:
        m *= 0.90
        notes.append(f"long notice period ({np_days}d)")

    return max(0.45, min(1.12, m)), notes


def score_candidate(f: dict, semantic_sim: float, weights: Dict[str, float]):
    """Return (final_score, breakdown_dict)."""
    comp = {
        "semantic": semantic_sim,
        "core_concepts": _core_concept_score(f["concept_scores"]),
        "title_role": _title_role_score(f),
        "production": f["production_signal"],
        "experience": f["exp_fit"],
        "location": f["location_fit"],
        "nice_to_have": _nice_score(f["nice_scores"]),
    }
    base = sum(weights[k] * comp[k] for k in weights)

    # ---- stated-negative penalties (multiplicative) -----------------------
    penalties = {}
    if f["is_non_tech_title"] and not f["ever_software_ai_title"]:
        penalties["non_engineering_career"] = 0.20
    if f["only_consulting"]:
        penalties["services-only career"] = 0.50
    if f["cv_without_nlp"]:
        penalties["cv/speech without NLP/IR"] = 0.60
    if f["research_only"]:
        penalties["research-only, no production"] = 0.55
    if f["title_chaser"]:
        penalties["title-chasing job history"] = 0.72
    if f["framework_fluff"]:
        penalties["framework-tutorial profile"] = 0.80
    if f["recent_pure_mgmt"]:
        penalties["no recent hands-on coding"] = 0.85

    fit = base
    for factor in penalties.values():
        fit *= factor

    # ---- behavioural availability modifier --------------------------------
    bmult, bnotes = _behavioural_multiplier(f["signals"])
    final = fit * bmult

    # ---- honeypot gate: force to the very bottom --------------------------
    if f["honeypot"]:
        final = -1.0

    breakdown = {
        "components": comp,
        "base": base,
        "penalties": penalties,
        "behavioural_multiplier": bmult,
        "behavioural_notes": bnotes,
        "final": final,
    }
    return final, breakdown
