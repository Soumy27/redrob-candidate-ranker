"""Structured representation of the job description.

Rather than feeding raw JD text to a similarity model and hoping for the best,
we parse the JD into an explicit, weighted target profile. This is the
"understand what the role needs" layer: every requirement, soft preference and
stated negative from the JD is encoded here with a weight, so the rest of the
pipeline reasons against intent rather than against surface words.

Source: job_description.docx — "Senior AI Engineer — Founding Team", Redrob AI.
"""

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class JobProfile:
    title: str

    # Experience: the JD says 5-9 yrs is a guide, ideal 6-8, with 4-5 of those
    # in applied ML at product companies. Treated as a soft band, not a cut.
    exp_ideal_low: float = 6.0
    exp_ideal_high: float = 8.0
    exp_soft_low: float = 4.0
    exp_soft_high: float = 11.0

    # Locations that are a clean fit (India tier-1, Noida/Pune preferred).
    preferred_locations: List[str] = field(default_factory=list)
    # India is in-scope generally; outside India needs relocation willingness
    # (no visa sponsorship per the JD).
    in_country: str = "India"

    notice_period_soft_cap_days: int = 30

    # Relative importance of each scoring component (documented, not magic).
    component_weights: Dict[str, float] = field(default_factory=dict)

    # A natural-language query used by the semantic (TF-IDF) layer. This is the
    # "what we actually mean" paragraph, written in the plain language a strong
    # candidate would use to describe the work — so a buzzword-free Tier-5 who
    # built a recommender at a product company still surfaces.
    semantic_query: str = ""


def build_job_profile() -> JobProfile:
    return JobProfile(
        title="Senior AI Engineer — Founding Team (Redrob AI)",
        preferred_locations=[
            "noida", "pune", "hyderabad", "mumbai", "delhi", "gurgaon",
            "gurugram", "bengaluru", "bangalore", "ncr", "new delhi",
        ],
        component_weights={
            # Positive evidence of genuine role fit.
            "semantic": 0.16,        # plain-language similarity to the real work
            "core_concepts": 0.30,   # retrieval/ranking/embeddings/eval evidence
            "title_role": 0.20,      # is this person actually an AI/SW engineer
            "production": 0.12,      # shipped to real users at a product company
            "experience": 0.10,      # experience band fit
            "location": 0.05,        # Noida/Pune/India + relocation
            "nice_to_have": 0.07,    # fine-tuning, LTR, HR-tech, OSS, distributed
        },
        semantic_query=(
            "Senior AI engineer who builds and ships production retrieval, "
            "ranking and recommendation systems for real users at scale. "
            "Deep experience with embeddings based semantic search, vector "
            "databases and hybrid search infrastructure such as FAISS, "
            "Pinecone, Weaviate, Qdrant, Milvus, OpenSearch or Elasticsearch. "
            "Strong Python engineer who has handled embedding drift, index "
            "refresh and retrieval quality regression in production. Designs "
            "rigorous evaluation frameworks for ranking systems using NDCG, "
            "MRR, MAP and offline to online correlation, and interprets A/B "
            "tests. Has shipped an end to end search, ranking or recommendation "
            "system at a product company, not pure research and not pure "
            "services consulting. Comfortable with LLMs, fine-tuning, LoRA and "
            "learning to rank models. Tilts toward shipping working systems "
            "over research. Based in or willing to relocate to Noida or Pune, "
            "India, and actively in the job market."
        ),
    )
