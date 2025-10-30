import os
import json
from openai import OpenAI

# -----------------------------
# Common Paths
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "..", "SavedData")
LLM_SETTINGS_FILE = os.path.join(SAVE_DIR, "llm_settings.json")

def get_llm_settings():
    """Loads LLM settings from the JSON file."""
    if not os.path.exists(LLM_SETTINGS_FILE):
        return None
    with open(LLM_SETTINGS_FILE, "r") as f:
        return json.load(f)

def chat_with_gpt(prompt, api_key, model="gpt-4o-mini", temperature=0.2):
    """
    Sends an SQL-related question or instruction to GPT and receives a clean SQL query as output.
    """
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a senior SQL expert and database architect. "
                        "Your only task is to generate valid, executable SQL queries based on the user's request. "
                        "You must not include explanations, comments, markdown formatting, or text outside the SQL query. "
                        "Always assume the database is MySQL unless otherwise stated. "
                        "If a query can vary depending on table or column names, use realistic placeholder names."
                    ),
                },
                {"role": "user", "content": prompt.strip()},
            ],
            temperature=temperature,
            max_tokens=300,
        )
        result = response.choices[0].message.content.strip()
        if result.startswith("```"):
            result = result.strip("`").replace("sql", "").strip()
        return result
    except Exception as e:
        return f"Error: {e}"

# Example usage (optional, for testing)
if __name__ == "__main__":
    settings = get_llm_settings()
    if settings:
        print(chat_with_gpt("show me all tables in the database", settings.get("api_key"), settings.get("model"), settings.get("temperature")))
    else:
        print("LLM settings not found. Please create llm_settings.json.")