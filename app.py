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
    
    # Active Stable Gemini Models
    models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro']
    
    prompt = f"""
    Analyze the following text and extract or create 5 Multiple Choice Questions (MCQs) in Marathi/English as present in text.
    Return ONLY a valid JSON array format. Do not use markdown code formatting blocks like ```json.
    
    JSON Format required:
    [
      {{
        "id": 1,
        "question": "Question text here?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": "Exact Option text matching one of options",
        "explanation": "Detailed explanation/solution in Marathi/English"
      }}
    ]

    Text Content:
    {text[:4000]}
    """
    
    response = None
    last_error = ""
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            if response and response.text:
                break
        except Exception as e:
            last_error = str(e)
            continue
            
    if not response:
        raise Exception(f"API Error: {last_error if last_error else 'Invalid API Key or Model access.'}")

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
            
