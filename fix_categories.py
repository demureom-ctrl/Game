
import sqlite3
import os

DB_PATH = 'questions.db'

def fix_categories():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        # Merge 'ثقافة عامة' into 'معلومات عامة'
        # First check counts
        cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'ثقافة عامة'")
        old_gen_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'معلومات عامة'")
        new_gen_count = cur.fetchone()[0]
        
        print(f"Before: 'ثقافة عامة'={old_gen_count}, 'معلومات عامة'={new_gen_count}")

        # Update
        cur.execute("UPDATE questions SET category = 'معلومات عامة' WHERE category = 'ثقافة عامة'")
        print("Merged 'ثقافة عامة' -> 'معلومات عامة'")

        # Merge 'تكنولوجيا' into 'تقنية'
        cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'تكنولوجيا'")
        tech_1 = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM questions WHERE category = 'تقنية'")
        tech_2 = cur.fetchone()[0]
        
        print(f"Before: 'تكنولوجيا'={tech_1}, 'تقنية'={tech_2}")
        
        cur.execute("UPDATE questions SET category = 'تقنية' WHERE category = 'تكنولوجيا'")
        print("Merged 'تكنولوجيا' -> 'تقنية'")

        conn.commit()
        
        # Verify
        cur.execute("SELECT category, COUNT(*) FROM questions GROUP BY category")
        rows = cur.fetchall()
        print("\nFinal Category Counts:")
        for row in rows:
            print(f"- {row[0]}: {row[1]}")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_categories()
