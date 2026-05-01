import google.generativeai as genai
import os
import json

def format_rounds(rounds: list) -> str:
    lines = []
    for i, r in enumerate(rounds, 1):
        atlas_claim = ""
        riot_claim = ""
        if isinstance(r, dict):
            atlas = r.get("atlas", {})
            if isinstance(atlas, dict):
                atlas_claim = atlas.get("claim", "")
            
            riot = r.get("riot", {})
            if isinstance(riot, dict):
                riot_claim = riot.get("claim", "")
                
        lines.append(f"Round {i} — ATLAS: {atlas_claim} | RIOT: {riot_claim}")
    return "\n".join(lines)

def generate_fix(
    code_snippet: str,
    winner: str,
    fix_direction: str,
    debate_rounds: list
) -> dict:
    prompt = f"""
You are a code repair agent. A multi-agent debate has concluded.

Winner: {winner}
Fix direction: {fix_direction}

Debate summary:
{format_rounds(debate_rounds)}

Original code:
{code_snippet}

Instructions:
- Apply the minimum fix consistent with the winning argument
- Return raw JSON only, no markdown, no backticks
- JSON format:
{{
  "fixed_code": "complete fixed code as string",
  "explanation": "max 2 sentences",
  "confidence": float between 0 and 1,
  "diff": [
    {{"line": int, "original": "original line", "fixed": "fixed line"}}
  ]
}}
"""
    try:
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
            
        if text.endswith("```"):
            text = text[:-3]
            
        text = text.strip()
        return json.loads(text)
    except Exception:
        return {
            "fixed_code": code_snippet,
            "explanation": "Fix generation failed.",
            "confidence": 0.0,
            "diff": []
        }
