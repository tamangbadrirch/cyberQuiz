import streamlit as st
import PyPDF2
from pptx import Presentation
import google.generativeai as genai
import re
import json
import os
from datetime import datetime
import hashlib
import base64

# Hardcoded Gemini API key for instructor use only
GEMINI_API_KEY = "AIzaSyDXhNgu0iMq1DG5zfetJ6KN07H-9yf6LzE"  # Gemini API key for quiz generation

def extract_text_from_pdf(pdf_file):
    text = ""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + " "
    return text

def extract_text_from_pptx(pptx_file):
    text = ""
    prs = Presentation(pptx_file)
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text:
                text += shape.text + " "
    return text

def clean_text(text, max_words=600):
    lines = list(dict.fromkeys(text.splitlines()))
    text = " ".join(lines)
    words = text.split()
    if len(words) > max_words:
        text = " ".join(words[:max_words])
    return text

def generate_mcqs_with_gemini(text, num_questions):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = (
        f"You are a cybersecurity teacher. Based on the following content, generate {num_questions} high-quality, conceptual multiple-choice questions (MCQs) for students. "
        "Each question should have 4 options (A, B, C, D), only one correct answer, and a short explanation. "
        "Do NOT use fill-in-the-blank or word replacement. Make the questions conceptual and relevant to the content. "
        "Format:\n"
        "Q: <question>\nA) <option1>\nB) <option2>\nC) <option3>\nD) <option4>\nAnswer: <A/B/C/D>\nExplanation: <short explanation>\n"
        "Content:\n"
        f"{text}\n"
    )
    response = model.generate_content(prompt)
    return response.text

def parse_mcqs(gemini_response):
    questions = []
    blocks = re.split(r"\nQ: ", "\n" + gemini_response)
    for block in blocks[1:]:
        lines = block.strip().split("\n")
        q = lines[0].strip()
        options = []
        for line in lines[1:5]:
            if line[:2] in ["A)", "B)", "C)", "D)"]:
                options.append(line[3:].strip())
        answer_line = next((l for l in lines if l.startswith("Answer:")), None)
        explanation_line = next((l for l in lines if l.startswith("Explanation:")), None)
        if answer_line and explanation_line and len(options) == 4:
            answer_letter = answer_line.split(":")[1].strip()
            correct_index = "ABCD".index(answer_letter)
            explanation = explanation_line.split(":", 1)[1].strip()
            questions.append({
                "question": q,
                "options": options,
                "correct_answer": correct_index,
                "explanation": explanation
            })
    return questions

def generate_quiz_id(questions):
    # Create a unique ID based on the quiz content
    quiz_str = json.dumps(questions, sort_keys=True)
    return base64.urlsafe_b64encode(hashlib.md5(quiz_str.encode()).digest()).decode()[:8]

def show_quiz_interface(questions):
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
        st.session_state.score = 0
        st.session_state.checked = False
        st.session_state.selected_option = None
        st.session_state.explanation_shown = False
        st.session_state.answers = [None] * len(questions)
        st.session_state.attempted = [False] * len(questions)

    q_idx = st.session_state.current_question
    q = questions[q_idx]
    total_questions = len(questions)

    st.progress((q_idx+1)/total_questions, text=f"{q_idx+1}/{total_questions}")
    st.subheader(f"Question {q_idx+1}")
    st.write(q['question'])

    answer_locked = st.session_state.answers[q_idx] is not None
    selected_option = st.radio(
        "Choose your answer:",
        q['options'],
        index=st.session_state.selected_option if st.session_state.selected_option is not None else 0,
        key=f"radio_{q_idx}",
        disabled=answer_locked
    )

    col1, col2 = st.columns([6,1])
    with col2:
        submit_btn = st.button("Check", key=f"check_{q_idx}", disabled=answer_locked)

    if submit_btn and not answer_locked:
        st.session_state.checked = True
        st.session_state.selected_option = q['options'].index(selected_option)
        st.session_state.answers[q_idx] = st.session_state.selected_option
        st.session_state.attempted[q_idx] = True
        st.session_state.explanation_shown = False

    if st.session_state.answers[q_idx] is not None:
        selected = st.session_state.answers[q_idx]
        if selected == q['correct_answer']:
            st.success("Correct!")
            if not st.session_state.get(f'scored_{q_idx}', False):
                st.session_state.score += 1
                st.session_state[f'scored_{q_idx}'] = True
        else:
            st.error("Incorrect!")

        col_exp1, col_exp2 = st.columns([6,1])
        with col_exp2:
            show_exp = st.button("Explanation", key=f"explanation_{q_idx}")
        if show_exp:
            st.session_state.explanation_shown = True
        if st.session_state.explanation_shown:
            st.info(f"Explanation: {q['explanation']}")

        col_next = st.columns([8,1])
        with col_next[1]:
            next_btn = st.button("Next", key=f"next_{q_idx}")
        if next_btn:
            st.session_state.current_question += 1
            st.session_state.checked = False
            st.session_state.selected_option = None
            st.session_state.explanation_shown = False
            if st.session_state.current_question >= total_questions:
                show_result_summary(questions)
                st.session_state.clear()

def show_result_summary(questions):
    total = len(questions)
    attempted = sum(1 for a in st.session_state.answers if a is not None)
    correct = st.session_state.score
    wrong = attempted - correct
    percent = (correct / total) * 100 if total > 0 else 0
    st.balloons()
    st.success(f"Quiz completed!")
    st.markdown(f"**Total Questions:** {total}")
    st.markdown(f"**Attempted:** {attempted}")
    st.markdown(f"**Correct:** {correct}")
    st.markdown(f"**Wrong:** {wrong}")
    st.markdown(f"**Score:** {percent:.2f}%")

def main():
    st.set_page_config(page_title="Cybersecurity Quiz Generator", layout="centered")
    st.title("Cybersecurity Quiz Generator (AI-Powered)")

    # Get quiz_id from URL parameters
    query_params = st.experimental_get_query_params()
    quiz_id = query_params.get("quiz", [None])[0]

    if quiz_id:
        # Load quiz from session state if it exists
        if 'quizzes' in st.session_state and quiz_id in st.session_state.quizzes:
            questions = st.session_state.quizzes[quiz_id]
            show_quiz_interface(questions)
        else:
            st.error("Quiz not found. Please generate a new quiz.")
            quiz_id = None

    if not quiz_id:
        st.write("Welcome! Upload a file to generate a new quiz.")
        uploaded_file = st.file_uploader("Choose a file", type=['pptx', 'pdf'])
        if uploaded_file:
            num_questions = st.slider("Number of questions to generate", min_value=5, max_value=20, value=10)
            if st.button("Generate Quiz"):
                with st.spinner("Extracting text and generating questions. Please wait..."):
                    if uploaded_file.name.endswith('.pdf'):
                        text = extract_text_from_pdf(uploaded_file)
                    else:
                        text = extract_text_from_pptx(uploaded_file)
                    text = clean_text(text)
                    gemini_response = generate_mcqs_with_gemini(text, num_questions)
                    questions = parse_mcqs(gemini_response)
                    if not questions:
                        st.error("Could not generate questions. Try with a different file or fewer questions.")
                    else:
                        # Generate unique quiz ID and store in session state
                        quiz_id = generate_quiz_id(questions)
                        if 'quizzes' not in st.session_state:
                            st.session_state.quizzes = {}
                        st.session_state.quizzes[quiz_id] = questions
                        
                        st.success("Quiz generated successfully!")
                        st.markdown("### To share this quiz with students:")
                        st.markdown("""
                        1. Deploy this app to Streamlit Cloud:
                           - Go to [share.streamlit.io](https://share.streamlit.io)
                           - Sign up/login with GitHub
                           - Create a new repository and push this app
                           - Deploy the app
                        
                        2. After deployment, you'll get a base URL like:
                           `https://yourusername-quiz-app.streamlit.app`
                        
                        3. Share this complete URL with your students:
                           `https://yourusername-quiz-app.streamlit.app?quiz={quiz_id}`
                        """)
                        st.markdown(f"**Quiz ID:** `{quiz_id}`")
                        st.markdown("Add this quiz ID to your deployed app's URL to share with students.")

if __name__ == "__main__":
    main() 