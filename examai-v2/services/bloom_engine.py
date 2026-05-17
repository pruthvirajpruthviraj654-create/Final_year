# ============================================================
# services/bloom_engine.py
# Bloom's Taxonomy engine: maps levels to verbs and question styles
# ============================================================

BLOOM_LEVELS = {
    "L1-Remember":   {
        "verbs":       ["Define", "List", "Name", "Recall", "Identify", "State", "Recognize", "Match"],
        "q_style":     "factual recall and recognition",
        "example":     "Define the term '{topic}' in context of {subject}.",
        "suitable_for":["MCQ", "Short"],
    },
    "L2-Understand": {
        "verbs":       ["Explain", "Describe", "Summarize", "Interpret", "Classify", "Compare", "Illustrate"],
        "q_style":     "explanation and description",
        "example":     "Explain the concept of '{topic}' in {subject} with an example.",
        "suitable_for":["Short", "Medium"],
    },
    "L3-Apply": {
        "verbs":       ["Solve", "Demonstrate", "Apply", "Use", "Implement", "Calculate", "Construct"],
        "q_style":     "application and problem-solving",
        "example":     "Apply {topic} to solve the following problem in {subject}.",
        "suitable_for":["Medium", "Long"],
    },
    "L4-Analyze": {
        "verbs":       ["Analyze", "Differentiate", "Examine", "Compare", "Break down", "Investigate", "Distinguish"],
        "q_style":     "analysis and critical thinking",
        "example":     "Analyze the {topic} in {subject} and compare with {related_topic}.",
        "suitable_for":["Medium", "Long"],
    },
    "L5-Evaluate": {
        "verbs":       ["Assess", "Critique", "Judge", "Justify", "Evaluate", "Defend", "Argue"],
        "q_style":     "evaluation and judgment",
        "example":     "Evaluate the effectiveness of {topic} in {subject} with justification.",
        "suitable_for":["Long"],
    },
    "L6-Create": {
        "verbs":       ["Design", "Develop", "Construct", "Formulate", "Propose", "Create", "Build"],
        "q_style":     "design and creation",
        "example":     "Design a {topic}-based solution for a real-world problem in {subject}.",
        "suitable_for":["Long"],
    },
}

MARKS_TO_BLOOM = {
    1:  ["L1-Remember", "L2-Understand"],
    2:  ["L1-Remember", "L2-Understand", "L3-Apply"],
    5:  ["L2-Understand", "L3-Apply", "L4-Analyze"],
    7:  ["L3-Apply", "L4-Analyze", "L5-Evaluate"],
    10: ["L4-Analyze", "L5-Evaluate", "L6-Create"],
}


def get_bloom_config(bloom_level: str) -> dict:
    """Return config for a given Bloom level string."""
    if bloom_level in BLOOM_LEVELS:
        return BLOOM_LEVELS[bloom_level]
    # Match partial
    for key in BLOOM_LEVELS:
        if bloom_level.lower() in key.lower():
            return BLOOM_LEVELS[key]
    return BLOOM_LEVELS["L2-Understand"]


def get_recommended_bloom_for_marks(marks: int) -> list:
    """Return recommended Bloom levels for a given mark value."""
    for m, levels in sorted(MARKS_TO_BLOOM.items(), key=lambda x: abs(x[0] - marks)):
        if m == marks:
            return levels
    # find closest
    closest = min(MARKS_TO_BLOOM.keys(), key=lambda k: abs(k - marks))
    return MARKS_TO_BLOOM[closest]


def get_verbs_for_level(bloom_level: str) -> list:
    cfg = get_bloom_config(bloom_level)
    return cfg.get("verbs", ["Explain", "Describe"])


def get_all_levels() -> list:
    return list(BLOOM_LEVELS.keys())
