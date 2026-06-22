"""Concept lexicons used to read candidate text the way a domain expert would.

Each concept group is a bag of surface forms (lowercase substrings). We match
these against a candidate's *full text* and, crucially, track *where* a match
occurs. A term appearing inside a real career-history description is far
stronger evidence than the same term sitting in a bare skills tag, which is the
signal we use to defeat keyword-stuffing.
"""

# ---------------------------------------------------------------------------
# Core technical concepts the role is built around (the "things you need").
# ---------------------------------------------------------------------------
CONCEPTS = {
    "retrieval": [
        "retrieval", "semantic search", "vector search", "hybrid search",
        "dense retrieval", "sparse retrieval", "bm25", "information retrieval",
        "nearest neighbor", "nearest neighbour", "approximate nearest",
        " ann ", "knn", "embedding search", "search relevance", "lexical search",
    ],
    "embeddings": [
        "embedding", "embeddings", "sentence-transformer", "sentence transformers",
        "sbert", "bge", "e5 model", " e5 ", "text embedding",
        "word2vec", "fasttext", "glove", "representation learning", "vector representation",
    ],
    "vector_db": [
        "pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch",
        "faiss", "vespa", "pgvector", "chroma", "vector database", "vector db",
        "vector store", "vector index", "annoy", "hnsw", "scann",
    ],
    "ranking": [
        "ranking", "re-rank", "rerank", "re rank", "learning to rank", " ltr ",
        "recommendation", "recommender", "recsys", "relevance ranking",
        "search ranking", "candidate ranking", "matching system", "scoring model",
        "personalization", "personalisation", "ranking system",
    ],
    "evaluation": [
        "ndcg", "mrr", "mean average precision", " map@", "precision@", "recall@",
        "offline eval", "a/b test", "ab test", "ab testing", "ranking metric",
        "evaluation framework", "offline-to-online", "online metric", "click-through",
        "ctr", "eval harness", "benchmark",
    ],
    "nlp": [
        " nlp", "natural language", "language model", " llm", "large language model",
        "transformer", " bert", "roberta", "text classification", "named entity",
        "question answering", "summarization", "summarisation", "tokeniz",
        "text mining", "sentiment", "topic model", "semantic similarity",
    ],
    "production_ml": [
        "production", "deployed", "real users", "at scale", "low latency",
        "serving", "inference", "data pipeline", "mlops", "model serving",
        "ml platform", "ml system", "end-to-end", "shipped", "in production",
        "productioniz", "productionis",
    ],
}

# Weight of each core concept toward role fit (sums are normalised later).
CONCEPT_WEIGHTS = {
    "retrieval": 1.30,
    "embeddings": 1.20,
    "vector_db": 1.20,
    "ranking": 1.30,
    "evaluation": 1.00,
    "nlp": 1.00,
    "production_ml": 0.90,
}

# ---------------------------------------------------------------------------
# "Nice to have" concepts — additive bonus, never a gate.
# ---------------------------------------------------------------------------
NICE_CONCEPTS = {
    "finetuning": [
        "fine-tun", "fine tun", "finetun", "lora", "qlora", "peft", "rlhf",
        " sft ", "instruction tun", "distillation",
    ],
    "ltr_models": [
        "xgboost", "lightgbm", "gradient boost", "neural ranker",
        "learning-to-rank", "catboost",
    ],
    "hrtech": [
        "hr-tech", "hrtech", "recruiting", "recruitment", "talent",
        "applicant tracking", " ats ", "marketplace", "two-sided", "job matching",
    ],
    "distributed": [
        "distributed system", "apache spark", " spark", "kafka", " ray ",
        "large-scale inference", "sharding", "horizontal scaling", "airflow",
        "kubernetes", "k8s",
    ],
    "opensource": [
        "open source", "open-source", " oss ", "maintainer", "contributor",
        "published a paper", "co-authored", "conference talk", "neurips",
        " acl ", " emnlp", " kdd ", "sigir", "patent",
    ],
}

NICE_WEIGHTS = {
    "finetuning": 0.45,
    "ltr_models": 0.35,
    "hrtech": 0.40,
    "distributed": 0.30,
    "opensource": 0.45,
}

# ---------------------------------------------------------------------------
# Specialisations the JD explicitly does NOT want when NLP/IR is absent.
# ---------------------------------------------------------------------------
CV_SPEECH_ROBOTICS = [
    "computer vision", "image classification", "object detection",
    "image segmentation", "semantic segmentation", "speech recognition",
    " tts", " asr", "text-to-speech", "robotics", " slam", "point cloud",
    "image generation", "gans", "diffusion model", "ocr", "pose estimation",
    "autonomous driving", "lidar",
]

# ---------------------------------------------------------------------------
# Services / consulting employers. An entire career here is a stated negative;
# partial exposure is fine.
# ---------------------------------------------------------------------------
CONSULTING_FIRMS = [
    "tcs", "tata consultancy", "infosys", "wipro", "accenture", "cognizant",
    "capgemini", "tech mahindra", "hcl", "mphasis", "ltimindtree", "lti ",
    "l&t infotech", "mindtree", "igate", "syntel", "hexaware", "birlasoft",
    "ntt data", "dxc", "deloitte", "kpmg", "pwc", "ernst & young",
]

# Framework-tutorial / wrapper signals (the "framework enthusiast" pattern).
FRAMEWORK_FLUFF = [
    "langchain", "llamaindex", "llama-index", "autogpt", "tutorial",
    "wrapper around", "demo app", "toy project", "hello world", "crewai",
]

# Pure-research signals (penalised when no production deployment is present).
RESEARCH_ONLY = [
    "phd researcher", "research scholar", "postdoc", "post-doc",
    "research assistant", "academic research", "research-only", "thesis",
    "purely theoretical", "research intern",
]

# ---------------------------------------------------------------------------
# Title classification. The single most decisive non-keyword signal: a
# "Marketing Manager" with a perfect AI skills list is still not an AI Engineer.
# ---------------------------------------------------------------------------
SOFTWARE_AI_TITLE_TERMS = [
    "ai engineer", "ml engineer", "machine learning engineer",
    "machine learning", "data scientist", "applied scientist",
    "research engineer", "nlp engineer", "software engineer", "backend engineer",
    "data engineer", "search engineer", "relevance engineer", "platform engineer",
    "sde", "software developer", "ai/ml", "deep learning", "mle ",
    "staff engineer", "principal engineer", "ml scientist", "research scientist",
]

# Titles that are clearly NOT this software/AI role (used as a hard down-weight,
# even when they contain the word "engineer", e.g. civil/mechanical).
NON_TECH_TITLE_TERMS = [
    "marketing", "sales", "accountant", "human resources", "hr manager",
    "recruiter", "content writer", "graphic designer", "operations manager",
    "project manager", "business analyst", "customer support", "civil engineer",
    "mechanical engineer", "electrical engineer", "chemical engineer",
    "finance", "administrative", "office manager", "teacher", "nurse",
    "supply chain", "logistics", "procurement",
]

# Hands-on / individual-contributor language (recency of real coding).
HANDS_ON_TERMS = [
    "wrote", "built", "implemented", "developed", "coded", "designed and built",
    "engineered", "deployed", "optimized", "debugged", "shipped", "prototyped",
    "refactored",
]

# Pure-management / non-coding leadership language (the "stopped coding" risk).
MANAGEMENT_TERMS = [
    "managed a team", "led the team", "people management", "headcount",
    "stakeholder management", "roadmap", "budget", "org design",
    "purely architectural", "no longer hands-on",
]
