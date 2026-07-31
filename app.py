import streamlit as st
from google import genai
import pypdf
import json
import re

st.set_page_config(page_title="PDF to Quiz Generator", layout="centered")

st.title("📝 PDF to Interactive Quiz Generator")
st.write("Upload a PDF to generate a multiple-choice quiz and test your knowledge!")

# 1. API Key Input
api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if not api_key:
    st.info("👈 Please enter your Gemini API Key in the sidebar to proceed.")
    st.stop()

# Initialize Gemini Client (Using official SDK to prevent URL connection errors)
client = genai.Client(api_key=api_key)

# 2. PDF Text Extraction Function
def extract_text_from_pdf(uploaded_file):
    reader = pypdf.PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# 3. PDF File Upload UI
uploaded_file = st.file_uploader("Upload PDF File", type=["pdf"])

if uploaded_file and "quiz_data" not in st.session_state:
    if st.button("Generate Test"):
        with st.spinner("Extracting PDF text and generating quiz questions..."):
            try:
                # Extract text
                pdf_text = extract_text_from_pdf(uploaded_file)
                
                if len(pdf_text.strip()) < 50:
                    st.error("PDF mein sufficient text nahi mila. Plain text PDF upload karein.")
                    st.stop()

                # Prompt for JSON formatting
                prompt = f"""
                You are an educational quiz generator. Read the following text and generate 5 multiple choice questions (MCQs).
                Return ONLY a valid JSON array of objects. Do not include markdown blocks like ```json.
                
                Each object must have this format:
                {{
                    "question": "Question text here",
                    "options": ["Option A", "Option B", "Option C", "Option D"],
                    "answer": "Correct Option Exact Text (must match one option exactly)"
                }}

                Text content:
                {pdf_text[:4000]}
                """

                # Call Gemini API
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt
                )

                # Clean response text
                cleaned_response = re.sub(r'```json\s*|\s*```', '', response.text).strip()
                quiz_data = json.loads(cleaned_response)
                
                # Save to session state
                st.session_state.quiz_data = quiz_data
                st.session_state.submitted = False
                st.rerun()

            except Exception as e:
                st.error(f"Error generating quiz: {e}")

# 4. Display Quiz & Calculate Score
if "quiz_data" in st.session_state:
    quiz_data = st.session_state.quiz_data
    
    with st.form("quiz_form"):
        st.subheader("📋 Attempt the Quiz")
        user_answers = {}
        
        for idx, q in enumerate(quiz_data):
            st.markdown(f"**Q{idx + 1}: {q['question']}**")
            user_answers[idx] = st.radio(
                f"Select option for Q{idx + 1}:",
                q["options"],
                key=f"q_{idx}",
                index=None
            )
            st.write("---")
            
        submit_btn = st.form_submit_button("Submit Answers")

    if submit_btn:
        st.session_state.submitted = True
        score = 0
        total = len(quiz_data)
        
        st.header("📊 Quiz Result")
        
        for idx, q in enumerate(quiz_data):
            user_ans = user_answers.get(idx)
            correct_ans = q["answer"]
            
            if user_ans == correct_ans:
                score += 1
                st.success(f"Q{idx + 1}: Correct! ✅")
            else:
                st.error(f"Q{idx + 1}: Incorrect ❌ (Your Answer: {user_ans if user_ans else 'Not Answered'})")
                st.info(f"Correct Answer: **{correct_ans}**")

        st.metric(label="Your Final Score", value=f"{score} / {total}")
        
        if st.button("Restart Quiz / Upload New PDF"):
            del st.session_state.quiz_data
            del st.session_state.submitted
            st.rerun()
            
