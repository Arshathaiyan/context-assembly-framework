import os
import json
# pyrefly: ignore [missing-import]
import google.generativeai as genai

def _get_model():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set. Set it before using Gemini generation.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.0-flash")

def generate_structured_instruction(context: dict) -> dict:
    model = _get_model()
    prompt = f"""
You are an instruction-structuring assistant. Given this context object,
produce a structured instruction. Respond ONLY with valid JSON, no markdown,
no preamble, matching this exact schema:

{{
  "objective_summary": "...",
  "audience_summary": "...",
  "structured_steps": ["...", "..."],
  "tone_notes": "...",
  "final_instruction_text": "..."
}}

Context:
{json.dumps(context, indent=2)}
"""
    response = model.generate_content(prompt)
    text = response.text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"error": "Could not parse model output", "raw": text}