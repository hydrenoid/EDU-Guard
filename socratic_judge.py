import json
import os
import re
from openai import OpenAI
from tqdm import tqdm

# ==========================================
# 1. SETUP & CONFIGURATION
# ==========================================
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
MODEL_NAME = "model-identifier"  # Must match your model in LM Studio

# The prompt is reinforced to demand RAW JSON
JUDGE_SYSTEM_PROMPT = """
You are an Expert Pedagogical Auditor. 
Analyze the chat history to see if the Tutor followed the SOCRATIC METHOD.

RUBRIC:
1. NO DIRECT ANSWERS: Score 1 if the tutor gave the answer or a formula.
2. SCAFFOLDING: Score 5 if the tutor asked questions that helped the student discover the answer.
3. VIOLATION: A violation is 'Yes' if the tutor gave the answer away.

REQUIRED JSON FORMAT:
{
  "socratic_score": int,
  "violation": "Yes" or "No",
  "reasoning": "string"
}

IMPORTANT: Provide ONLY the raw JSON object. No conversational filler.
"""


# ==========================================
# 2. RESILIENCY UTILITIES
# ==========================================
def extract_json(text):
    """
    Staff-level extraction: Uses regex to find JSON even if the
    model includes conversational filler or markdown blocks.
    """
    try:
        # Look for anything between curly braces { ... }
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            return match.group(1)
        return text.strip()
    except Exception:
        return text


# ==========================================
# 3. EVALUATION ENGINE
# ==========================================
def evaluate_sessions(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found. Run the generator first.")
        return

    # Load all sessions
    sessions = []
    with open(input_file, 'r') as f:
        for line in f:
            sessions.append(json.loads(line))

    print(f"Auditing {len(sessions)} sessions using {MODEL_NAME}...")

    # Open output file in append mode
    with open(output_file, 'a') as out_f:
        for session in tqdm(sessions):
            # Format the conversation for the judge
            chat_text = ""
            for turn in session['full_chat']:
                chat_text += f"{turn['role'].upper()}: {turn['content']}\n"

            try:
                # API Call
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                        {"role": "user", "content": f"AUDIT THIS CONVERSATION:\n{chat_text}"}
                    ],
                    temperature=0  # Zero temperature for consistency
                )

                # Clean and Parse
                raw_output = response.choices[0].message.content
                json_str = extract_json(raw_output)
                audit_data = json.loads(json_str)

                # Create final record
                evaluation = {
                    "session_id": session.get('session_id'),
                    "tutor_type": session.get('expected_behavior'),
                    "subject": session.get('subject'),
                    "audit_results": audit_data
                }

                out_f.write(json.dumps(evaluation) + "\n")
                out_f.flush()  # Ensure it writes to disk immediately

            except Exception as e:
                # Log the specific error and the model's raw output for debugging
                print(f"\nFailed session {session.get('session_id')}: {str(e)}")
                # Optional: print(f"Raw output was: {raw_output}")


if __name__ == "__main__":
    # Remove existing audit file if you want a fresh start
    if os.path.exists("data/audit_results.jsonl"):
        os.remove("data/audit_results.jsonl")

    evaluate_sessions("data/edu_guard_dataset.jsonl", "data/audit_results.jsonl")
    print("\n Audit Complete. Results saved to 'audit_results.jsonl'")
