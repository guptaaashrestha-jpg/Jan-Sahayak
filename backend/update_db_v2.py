import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'hyperlocal.db')

def upgrade_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if columns exist
    cursor.execute("PRAGMA table_info(issue_report)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'resolved_image_filename' not in columns:
        print("Adding column resolved_image_filename to issue_report...")
        cursor.execute("ALTER TABLE issue_report ADD COLUMN resolved_image_filename VARCHAR(255)")
        
    if 'duplicate_count' not in columns:
        print("Adding column duplicate_count to issue_report...")
        cursor.execute("ALTER TABLE issue_report ADD COLUMN duplicate_count INTEGER DEFAULT 0")

    conn.commit()
    conn.close()
    print("Database upgrade complete.")

if __name__ == '__main__':
    upgrade_db()
