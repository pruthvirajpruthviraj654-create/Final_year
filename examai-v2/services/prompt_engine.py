# ============================================================
# services/prompt_engine.py
# Builds highly specific, syllabus-grounded AI prompts for
# each question type and marks value.
# ============================================================
from typing import List, Dict, Optional
from services.bloom_engine     import get_bloom_config, get_verbs_for_level
from services.difficulty_engine import get_difficulty_config, get_marks_config


SYSTEM_PROMPT = """You are an expert university professor and examination paper setter with 20+ years of experience.
Your questions are:
- Strictly based on the provided syllabus topics
- University-level academic quality
- Properly formatted for examination papers
- Free from repetition and ambiguity
- Matched to the specified difficulty and Bloom's taxonomy level

CRITICAL RULES:
1. Generate questions ONLY from the provided syllabus topics
2. DO NOT mix subjects or unrelated topics
3. MCQs MUST have exactly 4 options (a, b, c, d) with ONE correct answer
4. Each question must clearly specify marks
5. Follow the exact output format specified
6. NEVER generate generic or textbook-copied questions
"""


def build_mcq_prompt(subject: str, topics: List[str], unit: str,
                      count: int, difficulty: str, bloom_level: str,
                      college_name: str, syllabus_context: str = "") -> str:
    """Build prompt for MCQ generation."""
    diff_cfg  = get_difficulty_config(difficulty)
    bloom_cfg = get_bloom_config(bloom_level)
    verbs     = ", ".join(bloom_cfg["verbs"][:4])
    topics_str = "\n".join(f"  • {t}" for t in topics[:12])

    syllabus_section = ""
    if syllabus_context.strip():
        syllabus_section = f"""
SYLLABUS CONTEXT:
{syllabus_context[:800]}
"""

    return f"""Generate exactly {count} Multiple Choice Questions (MCQ) for a university examination.

SUBJECT: {subject}
UNIT/MODULE: {unit}
TOPICS TO COVER:
{topics_str}
{syllabus_section}
DIFFICULTY: {difficulty} — {diff_cfg['description']}
BLOOM'S LEVEL: {bloom_level} — Use verbs like: {verbs}
STYLE: {diff_cfg['instruction']}

STRICT MCQ FORMAT (follow exactly):
Q[number]. [Question text here]?
   a) [Option A]
   b) [Option B]
   c) [Option C]
   d) [Option D]
   ✓ Correct Answer: [letter]) [correct option text]
   [Marks: 1]

REQUIREMENTS:
- Each MCQ must test a SPECIFIC concept from the listed topics above
- Options must be plausible but only ONE correct
- Avoid trivial questions like "What does X stand for"
- Questions must be concept-based, not definition-lookup
- No two questions should test the same concept
- Do NOT include questions outside the listed topics

Generate all {count} MCQs now:"""


def build_short_prompt(subject: str, topics: List[str], unit: str,
                        count: int, difficulty: str, bloom_level: str,
                        marks: int = 2, syllabus_context: str = "") -> str:
    """Build prompt for short answer questions."""
    diff_cfg  = get_difficulty_config(difficulty)
    bloom_cfg = get_bloom_config(bloom_level)
    verbs     = ", ".join(bloom_cfg["verbs"][:5])
    topics_str = "\n".join(f"  • {t}" for t in topics[:10])

    syllabus_section = ""
    if syllabus_context.strip():
        syllabus_section = f"\nSYLLABUS CONTEXT:\n{syllabus_context[:600]}\n"

    return f"""Generate exactly {count} Short Answer Questions for a university examination.

SUBJECT: {subject}
UNIT/MODULE: {unit}
TOPICS:
{topics_str}
{syllabus_section}
DIFFICULTY: {difficulty} — {diff_cfg['description']}
BLOOM'S LEVEL: {bloom_level} — Use question verbs like: {verbs}
MARKS PER QUESTION: {marks} marks
EXPECTED ANSWER LENGTH: 2–4 sentences

FORMAT (follow exactly):
Q[number]. [Question text here]?    [{marks} Marks]

REQUIREMENTS:
- Questions must ask for definitions, brief explanations, or short comparisons
- Directly from the listed topics
- University examination standard
- Each question covers a DIFFERENT topic
- Use action verbs appropriate for Bloom's {bloom_level}

Generate all {count} short answer questions now:"""


def build_medium_prompt(subject: str, topics: List[str], unit: str,
                         count: int, difficulty: str, bloom_level: str,
                         marks: int = 5, syllabus_context: str = "") -> str:
    """Build prompt for medium (5-mark) questions."""
    diff_cfg  = get_difficulty_config(difficulty)
    bloom_cfg = get_bloom_config(bloom_level)
    verbs     = ", ".join(bloom_cfg["verbs"][:5])
    topics_str = "\n".join(f"  • {t}" for t in topics[:10])

    syllabus_section = ""
    if syllabus_context.strip():
        syllabus_section = f"\nSYLLABUS CONTEXT:\n{syllabus_context[:600]}\n"

    return f"""Generate exactly {count} Medium Answer Questions ({marks} marks each) for a university examination.

SUBJECT: {subject}
UNIT/MODULE: {unit}
TOPICS:
{topics_str}
{syllabus_section}
DIFFICULTY: {difficulty} — {diff_cfg['description']}
BLOOM'S LEVEL: {bloom_level} — Verbs: {verbs}
MARKS: {marks} marks each
EXPECTED ANSWER: Half to one page, structured answer

FORMAT (follow exactly):
Q[number]. [Question text here]?    [{marks} Marks]

ANSWER EXPECTATION:
- Introduction/definition (1 mark)
- Detailed explanation with steps or points (2–3 marks)
- Example or diagram description (1 mark)
- Conclusion or comparison (1 mark)

REQUIREMENTS:
- Questions require ANALYTICAL or APPLICATION-level answers
- Must cover specific topics from the list above
- Include comparisons, classifications, or algorithm explanations
- University B.Tech/BCA level
- Different topics for each question

Generate all {count} medium questions now:"""


def build_descriptive_prompt(subject: str, topics: List[str], unit: str,
                              count: int, difficulty: str, bloom_level: str,
                              marks: int = 7, syllabus_context: str = "") -> str:
    """Build prompt for 7-mark descriptive questions."""
    diff_cfg  = get_difficulty_config(difficulty)
    bloom_cfg = get_bloom_config(bloom_level)
    verbs     = ", ".join(bloom_cfg["verbs"])
    topics_str = "\n".join(f"  • {t}" for t in topics[:8])

    syllabus_section = ""
    if syllabus_context.strip():
        syllabus_section = f"\nSYLLABUS CONTEXT:\n{syllabus_context[:600]}\n"

    return f"""Generate exactly {count} Descriptive Questions ({marks} marks each) for a university examination.

SUBJECT: {subject}
UNIT/MODULE: {unit}
TOPICS:
{topics_str}
{syllabus_section}
DIFFICULTY: {difficulty} — {diff_cfg['description']}
BLOOM'S LEVEL: {bloom_level} — Verbs: {verbs}
MARKS: {marks} marks each
EXPECTED ANSWER: Full page, detailed with diagram descriptions, algorithms, or case analysis

FORMAT:
Q[number]. [Question text here]?    [{marks} Marks]

ANSWER EXPECTATION:
- Comprehensive explanation of concept (2 marks)
- Detailed working/algorithm/steps (3 marks)
- Advantages, disadvantages, or applications (1 mark)
- Example or case study (1 mark)

REQUIREMENTS:
- Each question covers a MAJOR topic from the syllabus
- Requires multi-paragraph, structured answer
- Include application scenarios or real-world context
- University final examination quality

Generate all {count} descriptive questions now:"""


def build_long_prompt(subject: str, topics: List[str], unit: str,
                       count: int, difficulty: str, bloom_level: str,
                       marks: int = 10, syllabus_context: str = "") -> str:
    """Build prompt for 10-mark long answer questions."""
    diff_cfg  = get_difficulty_config(difficulty)
    bloom_cfg = get_bloom_config(bloom_level)
    verbs     = ", ".join(bloom_cfg["verbs"])
    topics_str = "\n".join(f"  • {t}" for t in topics[:8])

    syllabus_section = ""
    if syllabus_context.strip():
        syllabus_section = f"\nSYLLABUS CONTEXT:\n{syllabus_context[:600]}\n"

    return f"""Generate exactly {count} Long Answer Questions ({marks} marks each) for a university examination.

SUBJECT: {subject}
UNIT/MODULE: {unit}
TOPICS:
{topics_str}
{syllabus_section}
DIFFICULTY: {difficulty} — {diff_cfg['description']}
BLOOM'S LEVEL: {bloom_level} — Verbs: {verbs}
MARKS: {marks} marks each (split as two 5-mark sub-questions)

FORMAT (follow exactly):
Q[number]. 
   (a) [Part A question — covers first topic]    [5 Marks]
   (b) [Part B question — covers second topic]   [5 Marks]

REQUIREMENTS:
- Part (a): Theory/concept/explanation (algorithm, working, types)
- Part (b): Application/problem-solving/design/comparison
- Both parts from the listed topics
- Each part needs comprehensive, structured answers
- University B.Tech/BCA final examination standard

Generate all {count} long answer questions now:"""


def build_full_paper_prompt(config: Dict) -> str:
    """
    Master prompt builder: creates a complete section-wise paper prompt.
    config keys: subject, topics, units_str, sections, difficulty, bloom_level,
                 college_name, syllabus_context, exam_type, total_marks, duration
    """
    subject      = config.get("subject", "")
    topics       = config.get("topics", [])
    units_str    = config.get("units_str", "All Units")
    sections     = config.get("sections", [])
    difficulty   = config.get("difficulty", "Mixed")
    bloom_level  = config.get("bloom_level", "L2-Understand")
    college_name = config.get("college_name", "VisionCampus University")
    department   = config.get("department", "Computer Science")
    syllabus_ctx = config.get("syllabus_context", "")
    exam_type    = config.get("exam_type", "End Semester Examination")
    total_marks  = config.get("total_marks", 100)
    duration     = config.get("duration", "3 Hours")

    diff_cfg    = get_difficulty_config(difficulty)
    bloom_cfg   = get_bloom_config(bloom_level)
    verbs       = ", ".join(bloom_cfg["verbs"][:5])
    topics_str  = "\n".join(f"  • {t}" for t in topics[:20])

    syllabus_section = ""
    if syllabus_ctx.strip():
        syllabus_section = f"""
SYLLABUS CONTENT PROVIDED:
{syllabus_ctx[:1000]}
"""

    sections_desc = ""
    for i, sec in enumerate(sections, 1):
        letter = chr(64 + i)
        sections_desc += f"  Section {letter}: {sec['count']} × {sec['marks_per_q']}-mark {sec['type']} questions = {sec['section_marks']} marks\n"

    return f"""You are an expert university professor at {college_name}, Department of {department}.
Generate a COMPLETE university examination question paper.

═══════════════════════════════════════════════════════
PAPER DETAILS:
  Institution : {college_name}
  Subject     : {subject}
  Exam Type   : {exam_type}
  Duration    : {duration}
  Total Marks : {total_marks}
  Units       : {units_str}
  Difficulty  : {difficulty} — {diff_cfg['description']}
  Bloom Level : {bloom_level} — Use verbs: {verbs}
═══════════════════════════════════════════════════════

SYLLABUS TOPICS (generate ONLY from these):
{topics_str}
{syllabus_section}
PAPER STRUCTURE:
{sections_desc}

═══════════════════════════════════════════════════════
GENERATION RULES:
1. ALL questions must come from the listed syllabus topics ONLY
2. MCQs: 4 options (a,b,c,d), mark correct answer with ✓
3. Avoid any topic outside the listed syllabus
4. No two questions should test the same concept
5. Use appropriate action verbs for Bloom's level {bloom_level}
6. Difficulty must match: {diff_cfg['instruction']}
7. Questions must be university B.Tech/BCA examination quality
8. Format each section with a header

═══════════════════════════════════════════════════════
OUTPUT FORMAT:

{college_name}
Department of {department}
{exam_type} — April 2025
Subject: {subject}          Duration: {duration}          Max Marks: {total_marks}

INSTRUCTIONS:
1. All questions are compulsory unless stated otherwise.
2. Figures to the right indicate full marks.
3. Assume suitable data wherever necessary.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[For each section, use this format:]

SECTION [A/B/C/D] — [Question Type] Questions        [[marks] Marks]
([Instructions for this section])

Q[n]. [Question text]?
[For MCQ: options a) b) c) d) and ✓ Correct: ]
                                                    [[marks] Marks]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
              *** END OF QUESTION PAPER ***

Generate the complete question paper now. Be specific, university-level, and syllabus-accurate:"""
