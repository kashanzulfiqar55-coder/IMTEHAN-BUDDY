"""
Imtihan Buddy - exam practice from your own textbook chapter.
For Pakistani Matric and Intermediate students.
Upload chapter -> generate questions -> answer -> get checked + explained
in English / Roman Urdu.
"""

import json
import re

import streamlit as st
from google import genai
from google.genai import types
from pypdf import PdfReader

# ---------- Config ----------
MODEL = "gemini-3.5-flash"  # <-- change this to your exact Gemini model ID if needed
MAX_CHARS = 60000  # chapter text sent to the AI (keeps cost and speed OK)

st.set_page_config(page_title="Imtihan Buddy", page_icon="📚", layout="centered")


# ---------- Helpers ----------
@st.cache_resource
def get_client():
    key = st.secrets.get("GEMINI_API_KEY")
    if not key:
        st.error("API key missing. Add GEMINI_API_KEY in Streamlit secrets.")
        st.stop()
    return genai.Client(api_key=key)


def read_chapter(file) -> str:
    if file.name.lower().endswith(".pdf"):
        reader = PdfReader(file)
        pages = [(p.extract_text() or "") for p in reader.pages]
        return "\n".join(pages).strip()
    return file.read().decode("utf-8", errors="ignore").strip()


def ask_ai(system: str, user: str, max_tokens: int = 8000) -> str:
    resp = get_client().models.generate_content(
        model=MODEL,
        contents=user,
        config=types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
        ),
    )
    return resp.text or ""


def parse_json(text: str):
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start : end + 1])


def language_rule(mode: str) -> str:
    if mode == "English":
        return "Write explanations in simple English."
    if mode == "Roman Urdu":
        return ("Write explanations in Roman Urdu (Urdu written in English letters, "
                "e.g. 'Yeh jawab sahi hai kyun ke...'). Keep technical terms in English.")
    return ("Write explanations in BOTH simple English and Roman Urdu "
            "(Urdu in English letters). Keep technical terms in English.")


# ---------- Prompts ----------
QUESTION_SYSTEM = """You are an experienced Pakistani teacher preparing students for
Matric (SSC) and Intermediate (HSSC) board exams. You write exam-style questions
using ONLY the chapter text provided. Never use outside knowledge for the answers.
Reply with valid JSON only, no extra text."""

CHECK_SYSTEM = """You are a fair, encouraging Pakistani teacher marking a student's answers.
Mark ONLY against the chapter text provided. If the student's answer is correct but
worded differently, give credit. Quote the supporting line from the chapter as evidence.
Reply with valid JSON only, no extra text."""


def generate_questions(chapter, level, subject, qtypes, n, lang_mode):
    prompt = f"""Class: {level}
Subject: {subject}
Create {n} practice questions from the chapter below.
Allowed types: {", ".join(qtypes)}.
Mix types and difficulty like a real board paper.

Marks: mcq = 1, short = 2, long = 5.

Return JSON exactly like:
{{"questions":[
  {{"id":1,"type":"mcq","marks":1,"question":"...",
    "options":["A) ...","B) ...","C) ...","D) ..."],"correct":"A",
    "model_answer":"...","evidence":"short quote from chapter"}},
  {{"id":2,"type":"short","marks":2,"question":"...","options":[],
    "correct":"","model_answer":"...","evidence":"short quote from chapter"}}
]}}
Questions must be written in English (like real exam papers).

CHAPTER:
\"\"\"{chapter[:MAX_CHARS]}\"\"\""""
    data = parse_json(ask_ai(QUESTION_SYSTEM, prompt))
    return data["questions"]


def check_answers(chapter, questions, answers, lang_mode):
    items = []
    for q in questions:
        items.append({
            "id": q["id"], "type": q["type"], "marks": q["marks"],
            "question": q["question"], "options": q.get("options", []),
            "reference_answer": q.get("model_answer", ""),
            "student_answer": answers.get(q["id"], "") or "(no answer)",
        })
    prompt = f"""{language_rule(lang_mode)}

Mark each answer out of its marks (partial marks allowed for short/long).
Return JSON exactly like:
{{"results":[
  {{"id":1,"score":1,"verdict":"correct|partial|incorrect",
    "correct_answer":"...",
    "evidence":"line from the chapter that proves it",
    "explanation_en":"... (or empty if English not requested)",
    "explanation_ur":"... (Roman Urdu, or empty if not requested)",
    "tip":"one short tip to improve this answer"}}
]}}

QUESTIONS AND STUDENT ANSWERS:
{json.dumps(items, ensure_ascii=False)}

CHAPTER:
\"\"\"{chapter[:MAX_CHARS]}\"\"\""""
    return parse_json(ask_ai(CHECK_SYSTEM, prompt))["results"]


# ---------- UI ----------
st.title("📚 Imtihan Buddy")
st.caption("Upload your own textbook chapter. Practice. Get checked. Understand — in English or Roman Urdu.")

with st.sidebar:
    st.header("Settings")
    level = st.selectbox("Class", ["9th (Matric)", "10th (Matric)",
                                   "1st Year (Inter)", "2nd Year (Inter)"])
    subject = st.text_input("Subject", placeholder="e.g. Physics, Biology, Chemistry")
    lang_mode = st.radio("Explain in", ["English", "Roman Urdu", "Both"], index=2)
    qtypes = st.multiselect("Question types", ["mcq", "short", "long"],
                            default=["mcq", "short"])
    n = st.slider("Number of questions", 3, 15, 6)

file = st.file_uploader("Upload chapter (PDF or TXT)", type=["pdf", "txt"])

if file:
    if st.session_state.get("file_name") != file.name:
        st.session_state.clear()
        st.session_state["file_name"] = file.name
        st.session_state["chapter"] = read_chapter(file)

    chapter = st.session_state["chapter"]
    if len(chapter) < 300:
        st.warning("Could not read enough text. If this is a scanned PDF (photo), "
                   "please upload a text-based PDF or paste the text in a .txt file.")
        st.stop()
    st.success(f"Chapter loaded ({len(chapter):,} characters).")
    if len(chapter) > MAX_CHARS:
        st.info("Chapter is long, so only the first part is used. Upload it in sections for best results.")

    if st.button("✨ Generate questions", type="primary"):
        if not qtypes:
            st.error("Choose at least one question type.")
        else:
            with st.spinner("Making questions from your chapter..."):
                try:
                    st.session_state["questions"] = generate_questions(
                        chapter, level, subject or "General", qtypes, n, lang_mode)
                    st.session_state.pop("results", None)
                except Exception as e:
                    st.error(f"Something went wrong: {e}")

    questions = st.session_state.get("questions")
    if questions:
        st.divider()
        st.subheader("Your practice paper")
        answers = {}
        for q in questions:
            st.markdown(f"**Q{q['id']}. {q['question']}**  _({q['marks']} mark{'s' if q['marks'] > 1 else ''})_")
            if q["type"] == "mcq" and q.get("options"):
                answers[q["id"]] = st.radio("Choose one", q["options"], index=None,
                                            key=f"a{q['id']}", label_visibility="collapsed")
            else:
                answers[q["id"]] = st.text_area("Your answer", key=f"a{q['id']}",
                                                label_visibility="collapsed")

        if st.button("✅ Check my answers"):
            with st.spinner("Checking against your chapter..."):
                try:
                    st.session_state["results"] = check_answers(
                        chapter, questions, answers, lang_mode)
                except Exception as e:
                    st.error(f"Something went wrong: {e}")

    results = st.session_state.get("results")
    if results and questions:
        st.divider()
        st.subheader("Results")
        total = sum(q["marks"] for q in questions)
        got = sum(float(r.get("score", 0)) for r in results)
        st.metric("Your score", f"{got:g} / {total}")
        qmap = {q["id"]: q for q in questions}
        icon = {"correct": "🟢", "partial": "🟡", "incorrect": "🔴"}
        for r in results:
            q = qmap.get(r["id"], {})
            with st.expander(f"{icon.get(r['verdict'], '⚪')} Q{r['id']}: {q.get('question', '')[:70]}"):
                st.write(f"**Marks:** {r['score']} / {q.get('marks', '')}")
                st.write(f"**Correct answer:** {r['correct_answer']}")
                if r.get("explanation_en"):
                    st.write(f"🇬🇧 {r['explanation_en']}")
                if r.get("explanation_ur"):
                    st.write(f"🇵🇰 {r['explanation_ur']}")
                st.info(f"📖 From your chapter: \"{r['evidence']}\"")
                if r.get("tip"):
                    st.caption(f"💡 {r['tip']}")
else:
    st.info("👆 Upload a chapter to begin.")
