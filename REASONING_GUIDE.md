# How to read the ranking — reviewer guide

This explains the vocabulary used in the `reasoning` column of `submission.csv`
so the file can be read cold, without the code. Every claim in a reasoning line
is drawn directly from that candidate's own record — nothing is invented.

## Anatomy of a reasoning line

> **Top-tier fit:** Senior NLP Engineer with 7.8 yrs; **demonstrated** retrieval/search, embeddings, vector-database; **plus** LLM fine-tuning (LoRA/PEFT); **lists** Pinecone. **Response rate** 0.78, based in Coimbatore, **active this month**. **Concerns:** long notice period (120d).

| Phrase | What it means | Where it comes from |
|--------|---------------|---------------------|
| **Fit band** (`Top-tier` / `Strong` / `Solid` / `Moderate` / `Borderline`) | Confidence tier, keyed to the candidate's rank so tone matches position | rank 1–10 / 11–30 / 31–60 / 61–85 / 86–100 |
| **"<Title> with X yrs"** | Current job title and total years of experience | `profile.current_title`, `profile.years_of_experience` |
| **"demonstrated ..."** | Competency areas backed by **real career-history evidence** (job titles + role descriptions), not just self-listed tags | `career_history[].description`, `title`, `headline`, `summary` |
| **"plus ..."** | A *nice-to-have* the JD likes (LLM fine-tuning, learning-to-rank, HR-tech, distributed systems, open-source) | matched in profile text |
| **"lists <skill>"** | One concrete skill the candidate actually has on their profile | `skills[].name` |
| **"Response rate 0.NN"** | `recruiter_response_rate` — the fraction of recruiter messages this candidate replies to (0.00–1.00). A low value means they're hard to actually reach/hire, even if technically strong | `redrob_signals.recruiter_response_rate` |
| **"based in <city>"** | Candidate location (Noida/Pune/Delhi-NCR/Hyderabad etc. are the JD's preferred locations) | `profile.location` |
| **"active this month"** | Logged in to the platform within ~30 days — a freshness/availability signal | `redrob_signals.last_active_date` |
| **"Concerns: ..."** | Honest negatives that lowered the score (see below) | the penalties that fired for this candidate |

## What "demonstrated" deliberately does NOT count

A competency only appears under **"demonstrated"** when it shows up in lived
experience (a job title or a role description). A term that appears *only* as a
bare skills tag is heavily discounted. This is the core anti–keyword-stuffing
rule: a "Marketing Manager" who lists every AI keyword has no career evidence to
back it up, so the model does not treat them as an AI engineer.

## The "Concerns" vocabulary

| Concern phrase | Meaning |
|----------------|---------|
| `low recruiter response rate (0.NN)` | Replies to very few recruiter messages — low real availability |
| `inactive 3-6 months` / `inactive 6+ months` | Hasn't logged in recently |
| `not marked open to work` | Has not flagged themselves as job-seeking |
| `long notice period (NNd)` | Notice period well above the JD's sub-30-day preference |
| `significant consulting-firm tenure` | A large share of career at services/consulting firms (a JD caution) |
| `entirely services/consulting background` | Whole career at consulting firms (a stated JD negative) |
| `frequent short stints suggest title-chasing` | Many <18-month roles with climbing titles (a stated JD negative) |
| `CV/speech focus with little NLP/IR` | Specialised in vision/speech without NLP/retrieval (a stated JD negative) |
| `research-heavy with thin production deployment` | Academic/research signals with little production evidence (a stated JD negative) |
| `recent role looks management-only` | No recent hands-on coding evidence (the JD requires recent code) |

## On the `score` column

`score` is a **relative** confidence, min-max normalised across the top 100 into
a fixed 0.20–0.99 band (rank 1 ≈ 0.99, rank 100 = 0.20). Only the *ordering* is
graded (NDCG@10/@50, MAP, P@10); the absolute magnitude carries no weight. The
steep drop after the top ~15 reflects that genuinely strong matches are rare in
the pool — which the JD itself anticipates.

## Honeypots

~80 candidates in the pool have subtly impossible profiles (e.g. a single role
longer than their entire career, or many "expert" skills with zero months of
use). The ranker detects these arithmetic impossibilities and forces them to the
bottom, so none appear in the top 100.
