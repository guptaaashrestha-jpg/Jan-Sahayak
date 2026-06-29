import sqlite3
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'hyperlocal.db')

def upgrade_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(issue_report)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'ai_summary_hi' not in columns:
        print("Adding column ai_summary_hi to issue_report...")
        cursor.execute("ALTER TABLE issue_report ADD COLUMN ai_summary_hi VARCHAR(255)")
        conn.commit()
    
    # Backfill translations
    cursor.execute("SELECT id, ai_summary FROM issue_report WHERE ai_summary_hi IS NULL OR ai_summary_hi = ''")
    rows = cursor.fetchall()
    
    for row in rows:
        report_id, summary_en = row
        if not summary_en:
            continue
            
        print(f"Translating report {report_id}...")
        prompt = f"Translate the following civic issue summary into Hindi. Respond ONLY with the Hindi translation, nothing else.\n\nSummary: {summary_en}"
        try:
            response = gemini_model.generate_content(prompt)
            summary_hi = response.text.strip()
            cursor.execute("UPDATE issue_report SET ai_summary_hi = ? WHERE id = ?", (summary_hi, report_id))
            conn.commit()
            print(f" -> {summary_hi}")
        except Exception as e:
            print(f"Error translating report {report_id}: {e}")
            
    conn.close()
    print("Database upgrade complete.")

if __name__ == '__main__':
    upgrade_db()
