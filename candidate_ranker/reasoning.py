"""Grounded, per-candidate reasoning generation.

Every claim is drawn directly from the candidate's own record (title, years,
named evidence, signal values) and from the score breakdown, so the text never
references anything the profile doesn't contain. Tone is keyed to rank so a
top pick reads positively and a borderline pick names its concerns.
"""

from typing import Dict

_CONCEPT_NAMES = {
    "retrieval": "retrieval/search",
    "embeddings": "embeddings",
    "vector_db": "vector-database",
    "ranking": "ranking/recsys",
    "evaluation": "ranking evaluation (NDCG/MRR)",
    "nlp": "NLP/LLM work",
    "production_ml": "production ML",
}

_NICE_NAMES = {
    "finetuning": "LLM fine-tuning (LoRA/PEFT)",
    "ltr_models": "learning-to-rank models",
    "hrtech": "HR-tech/marketplace domain",
    "distributed": "distributed-systems exposure",
    "opensource": "open-source/published work",
}


def _band(rank: int) -> str:
    if rank <= 10:
        return "Top-tier fit"
    if rank <= 30:
        return "Strong fit"
    if rank <= 60:
        return "Solid fit"
    if rank <= 85:
        return "Moderate fit"
    return "Borderline fit"


def build_reasoning(f: dict, breakdown: Dict, rank: int) -> str:
    sig = f["signals"]
    yrs = f["years_of_experience"]
    title = f["current_title"] or "candidate"

    # strengths: name the core concepts with real (career-level) evidence
    ranked_concepts = sorted(
        f["matched_concepts"],
        key=lambda c: f["concept_scores"].get(c, 0.0),
        reverse=True,
    )
    strong_bits = [_CONCEPT_NAMES[c] for c in ranked_concepts[:3] if c in _CONCEPT_NAMES]

    nice_bits = [
        _NICE_NAMES[c]
        for c, v in sorted(f["nice_scores"].items(), key=lambda kv: -kv[1])
        if v > 0.4 and c in _NICE_NAMES
    ][:1]

    head = f"{_band(rank)}: {title} with {yrs:.1f} yrs"
    if strong_bits:
        head += "; demonstrated " + ", ".join(strong_bits)
    else:
        head += "; limited direct evidence of retrieval/ranking work"
    if nice_bits:
        head += f"; plus {nice_bits[0]}"

    rel_skills = f.get("relevant_skills") or []
    if rel_skills:
        head += f"; lists {rel_skills[0]}"

    # one concrete behavioural fact, recruiter-relevant
    rr = sig["recruiter_response_rate"]
    loc = f["location"] or "location n/a"
    head += f". Response rate {rr:.2f}, based in {loc}"
    if sig["recency_days"] <= 30:
        head += ", active this month"
    head += "."

    # honest concerns, drawn from the actual penalties + behavioural notes
    concerns = []
    pen = breakdown["penalties"]
    if "non_engineering_career" in pen:
        concerns.append("AI skills are listed but the career is non-engineering")
    if "services-only career" in pen:
        concerns.append("entirely services/consulting background")
    elif f["consulting_fraction"] > 0.4:
        concerns.append("significant consulting-firm tenure")
    if "cv/speech without NLP/IR" in pen:
        concerns.append("CV/speech focus with little NLP/IR")
    if "research-only, no production" in pen:
        concerns.append("research-heavy with thin production deployment")
    if "title-chasing job history" in pen:
        concerns.append("frequent short stints suggest title-chasing")
    if "framework-tutorial profile" in pen:
        concerns.append("profile leans on framework tutorials over systems work")
    if "no recent hands-on coding" in pen:
        concerns.append("recent role looks management-only")
    concerns.extend(breakdown["behavioural_notes"])

    if concerns:
        head += " Concerns: " + "; ".join(concerns[:3]) + "."

    # keep it tight (1-2 sentences) and CSV/line safe
    return " ".join(head.split()).replace("\n", " ").strip()
