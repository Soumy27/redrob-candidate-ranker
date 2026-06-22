"""Per-candidate feature and evidence extraction.

This module turns a raw candidate record into the structured evidence the
scorer reasons over. The central idea is *evidence weighting*: the same concept
term counts for much more when it appears inside a real career-history
description than when it sits in a bare skills tag. That single distinction is
what separates a genuine practitioner from a keyword-stuffer.
"""

from datetime import date, datetime
from typing import Dict, List

from . import lexicons as L

_REF_DATE = date(2026, 6, 22)  # dataset "now"; latest activity sits just before


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _count_terms(text: str, terms: List[str]) -> int:
    """Number of distinct surface forms from `terms` present in `text`."""
    return sum(1 for t in terms if t in text)


def _has_any(text: str, terms: List[str]) -> bool:
    return any(t in text for t in terms)


# --------------------------------------------------------------------------- #
# main extraction
# --------------------------------------------------------------------------- #
def extract_features(cand: dict) -> dict:
    profile = cand.get("profile", {}) or {}
    history = cand.get("career_history", []) or []
    skills = cand.get("skills", []) or []
    education = cand.get("education", []) or []
    signals = cand.get("redrob_signals", {}) or {}

    # ---- text surfaces -----------------------------------------------------
    headline = (profile.get("headline") or "").lower()
    summary = (profile.get("summary") or "").lower()
    cur_title = (profile.get("current_title") or "").lower()

    titles = [cur_title] + [(j.get("title") or "").lower() for j in history]
    descriptions = " ".join((j.get("description") or "").lower() for j in history)
    skill_names = [(s.get("name") or "").lower() for s in skills]
    skill_text = " ".join(skill_names)

    # "strong" text = lived experience (titles + descriptions + headline/summary)
    strong_text = " ".join([headline, summary, " ".join(titles), descriptions])
    # "weak" text = self-asserted skill tags only
    weak_text = skill_text
    full_text = strong_text + " " + weak_text

    f: Dict = {}
    f["candidate_id"] = cand.get("candidate_id")
    f["name"] = profile.get("anonymized_name", "")
    f["current_title"] = profile.get("current_title", "")
    f["years_of_experience"] = float(profile.get("years_of_experience") or 0.0)
    f["location"] = (profile.get("location") or "")
    f["country"] = (profile.get("country") or "")
    f["semantic_text"] = (summary + " " + descriptions + " " + headline).strip()

    # ---- core concept evidence (strong vs weak) ----------------------------
    concept_scores = {}
    matched_concepts = []
    for concept, terms in L.CONCEPTS.items():
        strong_hits = _count_terms(strong_text, terms)
        weak_hits = _count_terms(weak_text, terms)
        # Strong evidence counts fully; tag-only evidence is heavily discounted.
        raw = min(strong_hits, 3) + 0.25 * min(weak_hits if strong_hits == 0 else 0, 3)
        # saturating, so three solid mentions ~= full credit for the concept
        score = 1.0 - 0.55 ** raw if raw > 0 else 0.0
        concept_scores[concept] = score
        if strong_hits > 0:
            matched_concepts.append(concept)
    f["concept_scores"] = concept_scores
    f["matched_concepts"] = matched_concepts

    # role-relevant skills the candidate actually lists, strongest first — used
    # to ground the reasoning in a concrete, in-profile skill name
    relevant_terms = set()
    for terms in L.CONCEPTS.values():
        relevant_terms.update(terms)
    for terms in L.NICE_CONCEPTS.values():
        relevant_terms.update(terms)
    rel = [
        (s.get("name", ""), int(s.get("endorsements") or 0))
        for s in skills
        if any(t.strip() in (s.get("name") or "").lower() for t in relevant_terms)
    ]
    rel.sort(key=lambda x: -x[1])
    f["relevant_skills"] = [name for name, _ in rel[:3] if name]

    # ---- nice-to-haves -----------------------------------------------------
    nice_scores = {}
    for concept, terms in L.NICE_CONCEPTS.items():
        hits = _count_terms(full_text, terms)
        nice_scores[concept] = 1.0 - 0.6 ** hits if hits > 0 else 0.0
    f["nice_scores"] = nice_scores

    # ---- title / role classification --------------------------------------
    f["is_software_ai_title"] = _has_any(cur_title, L.SOFTWARE_AI_TITLE_TERMS)
    f["is_non_tech_title"] = _has_any(cur_title, L.NON_TECH_TITLE_TERMS)
    # any software/AI title anywhere in history (career could be transitioning)
    f["ever_software_ai_title"] = any(
        _has_any(t, L.SOFTWARE_AI_TITLE_TERMS) for t in titles
    )

    # ---- production signal -------------------------------------------------
    prod_hits = _count_terms(strong_text, L.CONCEPTS["production_ml"])
    f["production_signal"] = 1.0 - 0.5 ** prod_hits if prod_hits else 0.0

    # ---- consulting / services exposure (by tenure) ------------------------
    total_months = sum(int(j.get("duration_months") or 0) for j in history) or 1
    consulting_months = 0
    for j in history:
        comp = (j.get("company") or "").lower()
        if _has_any(comp, L.CONSULTING_FIRMS):
            consulting_months += int(j.get("duration_months") or 0)
    f["consulting_fraction"] = consulting_months / total_months
    f["only_consulting"] = (
        consulting_months / total_months >= 0.85 and len(history) >= 2
    )

    # ---- job-hopping / tenure ---------------------------------------------
    durations = [int(j.get("duration_months") or 0) for j in history]
    short_stints = sum(1 for d in durations if 0 < d < 18)
    f["num_jobs"] = len(history)
    f["short_stints"] = short_stints
    avg_tenure = (sum(durations) / len(durations)) if durations else 0
    f["avg_tenure_months"] = avg_tenure
    # title-chaser: many roles, short average tenure, climbing seniority
    climbing = sum(
        1 for t in titles if any(w in t for w in ("senior", "staff", "principal", "lead"))
    )
    f["title_chaser"] = (
        len(history) >= 4 and avg_tenure < 20 and climbing >= 2 and short_stints >= 2
    )

    # ---- specialisation: CV/speech/robotics without NLP/IR -----------------
    cv_hits = _count_terms(full_text, L.CV_SPEECH_ROBOTICS)
    nlp_ir = (
        concept_scores["nlp"] + concept_scores["retrieval"] + concept_scores["ranking"]
    )
    f["cv_speech_hits"] = cv_hits
    f["cv_without_nlp"] = cv_hits >= 4 and nlp_ir < 0.4

    # ---- research-only without production ----------------------------------
    f["research_only"] = (
        _has_any(full_text, L.RESEARCH_ONLY) and f["production_signal"] < 0.25
    )

    # ---- framework-enthusiast / langchain-wrapper-only ---------------------
    fluff_hits = _count_terms(full_text, L.FRAMEWORK_FLUFF)
    f["framework_fluff"] = fluff_hits >= 2 and f["production_signal"] < 0.3

    # ---- stale hands-on (stopped coding) -----------------------------------
    recent_desc = (history[0].get("description") or "").lower() if history else ""
    f["recent_hands_on"] = _has_any(recent_desc, L.HANDS_ON_TERMS)
    f["recent_pure_mgmt"] = (
        _has_any(recent_desc, L.MANAGEMENT_TERMS) and not f["recent_hands_on"]
    )

    # ---- experience band fit (soft) ---------------------------------------
    yoe = f["years_of_experience"]
    f["exp_fit"] = _experience_fit(yoe)

    # ---- location fit ------------------------------------------------------
    loc = f["location"].lower()
    in_india = "india" in (f["country"].lower())
    f["in_india"] = in_india
    f["willing_to_relocate"] = bool(signals.get("willing_to_relocate", False))
    f["location_fit"] = _location_fit(loc, in_india, f["willing_to_relocate"])

    # ---- education tier (mild) --------------------------------------------
    tiers = [e.get("tier") for e in education]
    f["top_tier_edu"] = "tier_1" in tiers

    # ---- behavioural signals ----------------------------------------------
    f["signals"] = _behavioural(signals)

    # ---- honeypot detection ------------------------------------------------
    f["honeypot"], f["honeypot_reasons"] = _detect_honeypot(
        cand, history, skills, yoe
    )

    return f


# --------------------------------------------------------------------------- #
# component helpers
# --------------------------------------------------------------------------- #
def _experience_fit(yoe: float) -> float:
    """Soft band centred on 6-8 yrs; gentle decay outside, never zero."""
    if 6.0 <= yoe <= 8.0:
        return 1.0
    if 4.0 <= yoe < 6.0:
        return 0.80 + 0.20 * (yoe - 4.0) / 2.0
    if 8.0 < yoe <= 11.0:
        return 1.0 - 0.45 * (yoe - 8.0) / 3.0
    if 2.0 <= yoe < 4.0:
        return 0.40 + 0.40 * (yoe - 2.0) / 2.0
    if yoe > 11.0:
        return max(0.25, 0.55 - 0.03 * (yoe - 11.0))
    return max(0.15, 0.20 * yoe / 2.0)  # very junior


def _location_fit(loc: str, in_india: bool, relocate: bool) -> float:
    from .job_profile import build_job_profile
    pref = build_job_profile().preferred_locations
    if any(p in loc for p in pref):
        return 1.0
    if in_india:
        return 0.80          # India tier-1 elsewhere, easy to relocate
    if relocate:
        return 0.55          # outside India but willing (no visa sponsorship caveat)
    return 0.20              # outside India, not willing => weak fit


def _behavioural(s: dict) -> dict:
    last_active = _parse_date(s.get("last_active_date"))
    recency_days = (_REF_DATE - last_active).days if last_active else 999
    return {
        "open_to_work": bool(s.get("open_to_work_flag", False)),
        "recruiter_response_rate": float(s.get("recruiter_response_rate") or 0.0),
        "recency_days": recency_days,
        "interview_completion_rate": float(s.get("interview_completion_rate") or 0.0),
        "profile_completeness": float(s.get("profile_completeness_score") or 0.0),
        "saved_by_recruiters_30d": int(s.get("saved_by_recruiters_30d") or 0),
        "search_appearance_30d": int(s.get("search_appearance_30d") or 0),
        "notice_period_days": int(s.get("notice_period_days") or 0),
        "offer_acceptance_rate": float(s.get("offer_acceptance_rate") or -1.0),
        "github_activity_score": float(s.get("github_activity_score") or -1.0),
    }


def _detect_honeypot(cand, history, skills, yoe):
    """Flag profiles whose arithmetic is impossible (subtle data-integrity traps).

    We only flag genuinely impossible records so real candidates are never
    suppressed: end-before-start dates, tenure that cannot fit the stated years,
    skill usage longer than the whole career, or many 'expert' skills claimed
    with zero months of use.
    """
    reasons = []
    yoe_months = yoe * 12.0

    # 1. end_date before start_date, or a single role longer than whole career
    for j in history:
        sd = _parse_date(j.get("start_date"))
        ed = _parse_date(j.get("end_date"))
        dur = int(j.get("duration_months") or 0)
        if sd and ed and ed < sd:
            reasons.append("role end date precedes start date")
        if dur > yoe_months + 14:
            reasons.append("single role longer than total experience")
        # stated duration grossly disagrees with date span
        if sd and ed:
            span = (ed.year - sd.year) * 12 + (ed.month - sd.month)
            if span >= 0 and abs(span - dur) > 18:
                reasons.append("duration inconsistent with dates")

    # 2. total tenure cannot fit the stated years of experience
    total = sum(int(j.get("duration_months") or 0) for j in history)
    if total > yoe_months * 2 + 18 and yoe > 0:
        reasons.append("combined tenure exceeds a plausible career length")

    # 3. a single skill claimed for longer than the candidate has existed
    #    professionally by a wide margin (kept very loose; normal overlap is fine)
    for s in skills:
        if int(s.get("duration_months") or 0) > yoe_months + 60:
            reasons.append("skill used far longer than entire career")
            break

    # 4. many 'expert' skills with zero months of use
    expert_zero = sum(
        1 for s in skills
        if s.get("proficiency") == "expert" and int(s.get("duration_months") or 0) == 0
    )
    if expert_zero >= 4:
        reasons.append("multiple 'expert' skills with zero months of use")

    return (len(reasons) > 0, sorted(set(reasons)))
