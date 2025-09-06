import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

# --- Setup and Configuration ---
PROMPTS_DIR = Path(__file__).resolve().parent / 'prompts'
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_API_KEY_HERE":
    print("INFO: GEMINI_API_KEY is not configured. AI services will be disabled.")
    genai.configure(api_key="placeholder")
else:
    genai.configure(api_key=GEMINI_API_KEY)

PRO_MODEL_NAME = os.getenv("GEMINI_PRO_MODEL", "gemini-1.5-pro-latest")
FLASH_MODEL_NAME = os.getenv("GEMINI_FLASH_MODEL", "gemini-1.5-flash-latest")

pro_model = genai.GenerativeModel(PRO_MODEL_NAME)
flash_model = genai.GenerativeModel(FLASH_MODEL_NAME)

# --- Helper Functions ---

def _is_api_configured():
    """Checks if the API key is properly configured."""
    return GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_API_KEY_HERE"

def _load_prompt(prompt_name: str) -> str:
    """
    Loads a prompt template from the 'prompts' directory.

    Args:
        prompt_name: The filename of the prompt to load (e.g., 'pdf_extraction.txt').

    Returns:
        The content of the prompt file as a string.
    """
    try:
        with open(PROMPTS_DIR / prompt_name, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: Prompt file not found: {prompt_name}")
        return "" # Return empty string to prevent crashes, though this indicates a dev error.

# =========================================================================
# --- Core AI Functions ---
# =========================================================================

def process_pdf_and_extract_chapters(file_path: str, subject_name: str) -> dict:
    if not _is_api_configured(): return {"error": "Cannot process PDF. Gemini API key is not configured."}
    try:
        uploaded_file = genai.upload_file(path=file_path, display_name=subject_name)
        prompt_template = _load_prompt('pdf_extraction.txt')
        prompt = prompt_template.format(subject_name=subject_name)
        response = pro_model.generate_content([prompt, uploaded_file])
        cleaned_json = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_json)
    except Exception as e:
        return {"error": f"Failed to process PDF. Reason: {e}"}

def generate_r_script_for_chart(chart_idea: str) -> str | None:
    if not _is_api_configured(): return None
    try:
        prompt_template = _load_prompt('r_script_generation.txt')
        prompt = prompt_template.format(chart_idea=chart_idea)
        response = flash_model.generate_content(prompt)
        r_script = response.text.strip().replace("```r", "").replace("```", "").strip()
        return r_script
    except Exception as e:
        return None

def answer_question_from_context(question: str, context: str) -> str:
    if not _is_api_configured(): return "Error: Cannot answer question. Gemini API key is not configured."
    try:
        prompt_template = _load_prompt('qa_contextual.txt')
        prompt = prompt_template.format(context=context, question=question)
        response = flash_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error: Could not get an answer from the AI. Reason: {e}"

def generate_quiz_from_summary(summary: str) -> dict | None:
    if not _is_api_configured(): return {"error": "Cannot generate quiz. Gemini API key is not configured."}
    try:
        prompt_template = _load_prompt('quiz_generation.txt')
        prompt = prompt_template.format(context=summary)
        response = flash_model.generate_content(prompt)
        cleaned_json = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_json)
    except Exception as e:
        return {"error": f"Failed to generate quiz. Reason: {e}"}
