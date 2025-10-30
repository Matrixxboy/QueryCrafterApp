from openai import OpenAI


def chat_with_gpt(prompt):
    """
    Sends an SQL-related question or instruction to GPT and receives a clean SQL query as output.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
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
        temperature=0.2,  # lower = more precise SQL
        max_tokens=300,
    )

    # Extract the message cleanly
    result = response.choices[0].message.content.strip()
    # Optionally clean SQL formatting (remove ```sql ... ```)
    if result.startswith("```"):
        result = result.strip("`").replace("sql", "").strip()

    return result


# Example usage
print(chat_with_gpt("show me all tables in the database"))
