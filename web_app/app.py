import os
import json
import logging
import io
import pandas as pd
import mysql.connector
from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv
from openai import OpenAI

# ------------------ Logging Setup ------------------
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# ------------------ Flask App Setup ------------------
load_dotenv()
app = Flask(__name__)

# ------------------ Helper Functions ------------------
def get_db_connection():
    """Establishes a connection to the database."""
    try:
        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_DATABASE")
        )
        cursor = connection.cursor()
        logging.info("Database connection successful.")
        return connection, cursor
    except mysql.connector.Error as err:
        logging.error(f"Database connection failed: {err}")
        return None, None

def get_db_structure(cursor):
    """Fetches the database structure."""
    try:
        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()[0]
        cursor.execute(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{db_name}'")
        tables = cursor.fetchall()
        
        all_table_structures = []
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = '{db_name}' AND table_name = '{table_name}'")
            columns = cursor.fetchall()
            all_table_structures.append({"table_name": table_name, "columns": columns})
        
        structure_path = os.path.join(os.path.dirname(__file__), "..", "SavedData", "db_structure.json")
        with open(structure_path, "w") as f:
            json.dump(all_table_structures, f, indent=4)
            
        return all_table_structures
    except mysql.connector.Error as err:
        logging.error(f"Failed to get database structure: {err}")
        return None

# ------------------ Routes ------------------
@app.route('/')
def index():
    """Renders the main page."""
    return render_template('index.html')

@app.route('/api', methods=['POST'])
def api():
    """Handles all API requests."""
    action = request.form.get('action')
    logging.info(f"Received action: {action}")

    if action == 'run_query':
        query = request.form.get('query')
        if not query:
            return jsonify({"error": "Query cannot be empty."})

        connection, cursor = get_db_connection()
        if not connection:
            return jsonify({"error": "Database connection failed."})

        try:
            cursor.execute(query)
            if cursor.with_rows:
                rows = cursor.fetchall()
                columns = [i[0] for i in cursor.description]
                return jsonify({"columns": columns, "rows": rows})
            else:
                connection.commit()
                return jsonify({"message": "Query executed successfully."})
        except mysql.connector.Error as err:
            logging.error(f"Query execution failed: {err}")
            return jsonify({"error": str(err)})
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                logging.info("Database connection closed.")

    elif action == 'show_db_structure':
        connection, cursor = get_db_connection()
        if not connection:
            return jsonify({"error": "Database connection failed."})

        structure = get_db_structure(cursor)
        if connection.is_connected():
            cursor.close()
            connection.close()
            logging.info("Database connection closed.")
            
        if structure:
            return jsonify({"structure": structure})
        else:
            return jsonify({"error": "Failed to get database structure."})

    elif action == 'generate_query':
        question = request.form.get('question')
        if not question:
            return jsonify({"error": "Please enter a prompt to generate a query."})

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return jsonify({"error": "OPENAI_API_KEY not found in .env file."})

        structure_path = os.path.join(os.path.dirname(__file__), "..", "SavedData", "db_structure.json")
        if not os.path.exists(structure_path):
            return jsonify({"error": "Database structure not found. Please run 'Show DB Structure' first."})
            
        with open(structure_path, "r") as f:
            db_structure = json.load(f)
            
        connection, cursor = get_db_connection()
        if not connection:
            return jsonify({"error": "Database connection failed."})
        try:
            cursor.execute("SELECT DATABASE()")
            db_name = cursor.fetchone()[0]
        except Exception as e:
            return jsonify({"error": f"Could not read database name: {e}"})
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                logging.info("Database connection closed.")

        prompt = f"""
            DB: {db_name}
            Schema: {db_structure}

            Write an optimized SQL query to answer: "{question}"

            Rules:
            - Use valid SQL for this DB
            - Include joins/subqueries if needed
            - Output only the SQL query (no text/comments)
            - End with a semicolon
            """

        try:
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system","content": "You are an advanced, expert-level SQL query generator. Your role is to understand the user's intent and produce only a valid and optimized SQL query as output — no explanations, no text, and no comments. Always return the query in proper SQL syntax using advanced techniques such as joins, subqueries, window functions, and aggregations when appropriate."},
                    {"role": "user", "content": prompt.strip()},
                ],
                temperature=0.2,
                max_tokens=300,
            )
            result = response.choices[0].message.content.strip()
            if result.startswith("```"):
                result = result.strip("`").replace("sql", "").strip()
            return jsonify({"query": result})
        except Exception as e:
            logging.error(f"OpenAI API call failed: {e}")
            return jsonify({"error": str(e)})

    elif action == 'export_csv':
        data = request.form.get('data')
        if not data:
            return jsonify({"error": "No data to export."})
        try:
            df = pd.read_json(data)
            
            # Create an in-memory binary stream
            output = io.BytesIO()
            df.to_csv(output, index=False)
            output.seek(0)
            
            return send_file(
                output,
                mimetype='text/csv',
                as_attachment=True,
                download_name='exported_data.csv'
            )
        except Exception as e:
            logging.error(f"Failed to export CSV: {e}")
            return jsonify({"error": str(e)})

    return jsonify({"error": "Invalid action."})

# ------------------ Main ------------------
if __name__ == '__main__':
    # Only used for local testing — not on PythonAnywhere
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
