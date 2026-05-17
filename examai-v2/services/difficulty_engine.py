# ============================================================
# services/difficulty_engine.py
# Maps difficulty levels to prompt instructions and distributions
# ============================================================

DIFFICULTY_CONFIG = {
    "Easy": {
        "description": "straightforward, recall-based, directly from syllabus definitions",
        "bloom_focus": "L1-Remember and L2-Understand",
        "instruction": "Questions should test basic recall and understanding. Use simple language. No complex derivations.",
        "distribution": {"Easy": 70, "Medium": 30, "Hard": 0},
    },
    "Medium": {
        "description": "analytical, application-based, requires understanding and application",
        "bloom_focus": "L3-Apply and L4-Analyze",
        "instruction": "Questions should require understanding and application. Include some derivations or comparisons.",
        "distribution": {"Easy": 20, "Medium": 60, "Hard": 20},
    },
    "Hard": {
        "description": "complex, evaluative, design-based, multi-step reasoning",
        "bloom_focus": "L4-Analyze, L5-Evaluate, and L6-Create",
        "instruction": "Questions should require deep analysis, design thinking, and multi-step problem solving.",
        "distribution": {"Easy": 10, "Medium": 30, "Hard": 60},
    },
    "Mixed": {
        "description": "balanced university standard distribution",
        "bloom_focus": "All levels",
        "instruction": "Follow standard university distribution: 30% Easy, 50% Medium, 20% Hard.",
        "distribution": {"Easy": 30, "Medium": 50, "Hard": 20},
    },
}

MARKS_CONFIG = {
    1: {
        "name":      "MCQ (1 mark)",
        "type":      "MCQ",
        "format":    "4 options (a,b,c,d), exactly one correct answer",
        "style":     "Objective, concept-testing, single-answer",
        "time":      "1–2 minutes",
        "bloom":     ["L1-Remember", "L2-Understand"],
        "instruction":"Generate ONLY MCQ with 4 options. Mark correct answer.",
    },
    2: {
        "name":      "Short Answer (2 marks)",
        "type":      "Short",
        "format":    "2–4 sentence answer expected",
        "style":     "Definition, concept explanation, one-line comparison",
        "time":      "3–5 minutes",
        "bloom":     ["L1-Remember", "L2-Understand"],
        "instruction":"Short definition or 2-3 line explanation. No diagrams needed.",
    },
    5: {
        "name":      "Medium Answer (5 marks)",
        "type":      "Medium",
        "format":    "Half to one page answer, structured",
        "style":     "Detailed explanation with examples, small comparison tables, flowcharts description",
        "time":      "10–15 minutes",
        "bloom":     ["L2-Understand", "L3-Apply", "L4-Analyze"],
        "instruction":"Structured answer with introduction, explanation, example, and conclusion. University exam style.",
    },
    7: {
        "name":      "Descriptive (7 marks)",
        "type":      "Descriptive",
        "format":    "One full page answer with diagrams/algorithms",
        "style":     "Detailed analysis, algorithm steps, comparison, case study",
        "time":      "15–20 minutes",
        "bloom":     ["L3-Apply", "L4-Analyze", "L5-Evaluate"],
        "instruction":"Comprehensive answer covering theory, algorithm or working, advantages/disadvantages, and applications.",
    },
    10: {
        "name":      "Long Answer (10 marks)",
        "type":      "Long",
        "format":    "Full detailed answer, 2 parts (a) and (b)",
        "style":     "Two sub-questions each worth 5 marks, comprehensive coverage",
        "time":      "25–30 minutes",
        "bloom":     ["L4-Analyze", "L5-Evaluate", "L6-Create"],
        "instruction":"Two-part question. Part (a) covers theory/concept [5 marks]. Part (b) covers application/design [5 marks].",
    },
}


def get_difficulty_config(difficulty: str) -> dict:
    return DIFFICULTY_CONFIG.get(difficulty, DIFFICULTY_CONFIG["Mixed"])


def get_marks_config(marks: int) -> dict:
    if marks in MARKS_CONFIG:
        return MARKS_CONFIG[marks]
    closest = min(MARKS_CONFIG.keys(), key=lambda k: abs(k - marks))
    return MARKS_CONFIG[closest]


def compute_section_distribution(total_marks: int, q_types: list) -> list:
    """
    Given total marks and desired question types, return a section plan.
    Returns list of: {marks, count, section_marks, type}
    """
    sections = []
    remaining = total_marks

    type_marks_map = {
        "MCQ": 1, "Short": 2, "Medium": 5,
        "Descriptive": 7, "Long": 10,
    }

    for qt in q_types:
        m = type_marks_map.get(qt, 2)
        count = max(1, remaining // (m * len(q_types)))
        sec_marks = count * m
        if sec_marks > remaining:
            sec_marks = remaining
            count = sec_marks // m
        sections.append({
            "type":          qt,
            "marks_per_q":   m,
            "count":         count,
            "section_marks": count * m,
        })
        remaining -= count * m

    return sections
