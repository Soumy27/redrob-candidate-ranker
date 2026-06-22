# Redrob Candidate Ranker — Senior AI Engineer

A candidate-discovery and ranking system for the Redrob *Intelligent Candidate
Discovery & Ranking Challenge*. It reads the released job description, builds a
structured understanding of what the role actually needs, and ranks the top 100
candidates out of the 100,000-candidate pool.

The design goal is to rank candidates the way an experienced recruiter would:
by reasoning about role fit, career substance and real availability — **not** by
counting AI keywords. The dataset is full of traps (keyword-stuffers,
plain-language strong candidates, behavioural twins, and ~80 impossible
honeypot profiles), and the ranker is built specifically to see through them.

---

## Quick start

```bash
# 1. install
pip install -r requirements.txt

# 2. place the dataset next to rank.py (or pass any path with --candidates)
#    candidates.jsonl  (or candidates.jsonl.gz — both are supported)

# 3. produce the ranking
python rank.py --candidates ./candidates.jsonl --out ./submission.csv

# 4. validate the format
python validate_submission.py ./submission.csv

# optional: an XLSX copy for inspection
python make_xlsx.py --csv ./submission.csv --out ./submission.xlsx
```

Runs **CPU-only, with no network access**, and finishes the full 100K pool in
under one minute on a 16 GB laptop — comfortably inside the 5-minute budget.

---

## How it works

The ranker is a **hybrid model**: a lexical-semantic retrieval signal fused with
a structured, explainable fit-scoring engine and a behavioural-availability
modifier. Each stage maps directly to something the JD says.

```
candidate ─► evidence extraction ─► weighted fit score
                                         │
                  semantic similarity ───┤
                                         ▼
                            stated-negative penalties
                                         ▼
                          behavioural availability modifier
                                         ▼
                              honeypot gate (force to bottom)
                                         ▼
                                  top-100 ranking
```

### 1. Understanding the role (`candidate_ranker/job_profile.py`)
The JD is parsed once into an explicit, weighted target profile: must-have
competencies (embeddings-based retrieval, vector/hybrid search, ranking
evaluation, strong Python), nice-to-haves (fine-tuning, learning-to-rank,
HR-tech, OSS), explicit negatives, the 6–8 year experience centre of gravity,
and the Noida/Pune location preference. A plain-language query paragraph drives
the semantic layer so we match on *intent*, not surface words.

### 2. Reading the candidate (`candidate_ranker/features.py`)
Each profile is turned into structured evidence. The key idea is **evidence
weighting**: a concept that shows up inside a real career-history description or
job title counts far more than the same word sitting in a self-asserted skills
tag. That single distinction defeats keyword-stuffing — a "Marketing Manager"
with a perfect AI skills list has no career evidence to back it up.

This stage also detects: product-company vs services/consulting tenure,
job-hopping / title-chasing, research-only-without-production, CV/speech focus
without NLP/IR, stale (management-only) recent roles, and arithmetic-impossible
honeypot profiles.

### 3. Semantic layer (`candidate_ranker/pipeline.py`)
An offline TF-IDF (1–2 gram) cosine similarity between each candidate's free
text and the JD query. This is what surfaces the *plain-language strong
candidate* — someone who built a recommender at a product company but never
wrote "RAG" or "Pinecone" in their profile.

### 4. Scoring (`candidate_ranker/scoring.py`)
```
fit   = weighted sum of (semantic, core-concepts, title/role, production,
                         experience, location, nice-to-haves)
fit   = fit × stated-negative penalties     (consulting-only, CV-without-NLP,
                                              research-only, title-chasing, …)
final = fit × behavioural-availability modifier   (response rate, recency,
                                                    open-to-work, notice, …)
honeypots are forced to the bottom.
```
The behavioural modifier implements the JD's point that a perfect-on-paper
candidate who hasn't logged in for six months and ignores recruiters is, for
hiring purposes, not actually available.

### 5. Reasoning (`candidate_ranker/reasoning.py`)
Every row gets a 1–2 sentence justification built entirely from facts in that
candidate's own record — title, years, demonstrated competency areas, a named
in-profile skill, recruiter response rate, location, activity — plus honest
concerns drawn from the penalties that fired. Tone is keyed to rank.

---

## Repository layout

```
rank.py                       CLI entry point (produces submission.csv)
make_xlsx.py                  optional CSV -> XLSX export
validate_submission.py        official format validator
requirements.txt
submission_metadata.yaml
candidate_ranker/
    job_profile.py            structured JD target profile
    lexicons.py               domain concept lexicons & negative signals
    features.py               per-candidate evidence extraction + honeypots
    scoring.py                fit score, penalties, behavioural modifier
    reasoning.py              grounded per-candidate reasoning
    pipeline.py               orchestration + semantic layer + CSV output
    loader.py                 JSONL / gzipped-JSONL loading
```

## Reproducing the submission

```
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

This is the single command that regenerates `submission.csv` from the candidate
pool. No pre-computation, no cached artifacts, no manual edits.

## Compute profile

| Constraint | This system |
|------------|-------------|
| Runtime    | < 1 min for 100K candidates |
| Memory     | < 4 GB |
| Compute    | CPU only |
| Network    | none (no external/LLM API calls) |
