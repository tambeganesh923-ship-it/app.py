import streamlit as st
import PyPDF2
import json
import google.generativeai as genai

st.set_page_config(page_title="PDF Quiz Generator", layout="wide")
st.title("📄 PDF to Interactive Test Generator")

api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = None
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text

def generate_questions(text, api_key):
    genai.configure(api_key=api_key)
    # Updated model
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Analyze the text and extract/create 5 MCQs in strict JSON array format without markdown code blocks.
    JSON Format:
    [
      {{
        "id": 1,
        "question": "Question text?",
        "options": ["A", "B", "C", "D"],
        "correct_answer": "Option text exactly matching one option",
        "explanation": "Detailed explanation"
      }}
    ]
    Text: {text[:4000]}
    """
    response = model.generate_content(prompt)
    clean_json = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_json)

uploaded_file = st.file_uploader("Upload PDF File", type=["pdf"])

if uploaded_file and api_key:
    if st.button("Generate Test"):
        with st.spinner("Generating Quiz..."):
            try:
                extracted_text = extract_text_from_pdf(uploaded_file)
                st.session_state.quiz_data = generate_questions(extracted_text, api_key)
                st.session_state.submitted = False
                st.session_state.user_answers = {}
                st.success("Test ready! Niche attempt karein.")
            except Exception as e:
                st.error(f"Error: {e}")

if st.session_state.quiz_data and not st.session_state.submitted:
    with st.form("quiz_form"):
        for q in st.session_state.quiz_data:
            st.markdown(f"**Q{q['id']}: {q['question']}**")
            st.session_state.user_answers[q['id']] = st.radio(
                "Select Option:", q['options'], key=f"q_{q['id']}", index=None
            )
            st.write("---")
        
        if st.form_submit_button("Submit Test"):
            st.session_state.submitted = True
            st.rerun()

if st.session_state.submitted:
    score = sum(1 for q in st.session_state.quiz_data if st.session_state.user_answers.get(q['id']) == q['correct_answer'])
    st.header(f"📊 Score: {score} / {len(st.session_state.quiz_data)}")
    
    for q in st.session_state.quiz_data:
        user_ans = st.session_state.user_answers.get(q['id'])
        is_correct = user_ans == q['correct_answer']
        
        with st.expander(f"Q{q['id']}: {q['question']}"):
            st.write(f"**Your Answer:** {user_ans}")
            st.write(f"**Correct Answer:** {q['correct_answer']}")
            st.info(f"**Solution:** {q['explanation']}")
            
