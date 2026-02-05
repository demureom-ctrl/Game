import re
import json
import sqlite3
from pathlib import Path

INDEX_PATH = Path(__file__).with_name('index.html')
DB_PATH = Path(__file__).with_name('questions.db')

def extract_full_db(js_text: str) -> str:
    # find the start of FULL_QUESTIONS_DB
    m = re.search(r'const\s+FULL_QUESTIONS_DB\s*=\s*\[', js_text)
    if not m:
        raise ValueError('FULL_QUESTIONS_DB not found')
    start = m.end() - 1  # position of '['
    i = start
    depth = 0
    while i < len(js_text):
        if js_text[i] == '[':
            depth += 1
        elif js_text[i] == ']':
            depth -= 1
            if depth == 0:
                end = i
                return js_text[start:end+1]
        i += 1
    raise ValueError('Could not find matching closing bracket for FULL_QUESTIONS_DB')

def js_array_to_json(s: str) -> str:
    # remove JS single-line and block comments
    s = re.sub(r'//.*?\n', '\n', s)
    s = re.sub(r'/\*.*?\*/', '', s, flags=re.S)
    # quote bare keys: category: -> "category":
    s = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'"\1":', s)
    # convert single-quoted JS strings into JSON-safe strings
    def replace_single(match):
        inner = match.group(1)
        return json.dumps(inner, ensure_ascii=False)
    s = re.sub(r"'([^'\\\\]*(?:\\\\.[^'\\\\]*)*)'", replace_single, s)
    # remove trailing commas before } or ]
    s = re.sub(r',\s*([}\]])', r'\1', s)
    return s

def load_questions_from_html(path: Path):
    txt = path.read_text(encoding='utf-8')
    arr_text = extract_full_db(txt)
    json_text = js_array_to_json(arr_text)
    data = json.loads(json_text)
    return data

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        difficulty INTEGER NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        options TEXT
    )''')
    conn.commit()
    conn.close()

def import_questions():
    ensure_db()
    data = load_questions_from_html(INDEX_PATH)
    conn = get_conn()
    cur = conn.cursor()
    inserted = 0
    skipped = 0
    for item in data:
        category = item.get('category')
        difficulty = int(item.get('difficulty',1))
        question = item.get('question')
        answer = item.get('answer')
        options = item.get('options') or []
        # skip if same question exists
        cur.execute('SELECT id FROM questions WHERE category=? AND difficulty=? AND question=?', (category,difficulty,question))
        if cur.fetchone():
            skipped += 1
            continue
        cur.execute('INSERT INTO questions (category,difficulty,question,answer,options) VALUES (?,?,?,?,?)', (category,difficulty,question,answer,json.dumps(options, ensure_ascii=False)))
        inserted += 1
    conn.commit()
    conn.close()
    print(f'Inserted: {inserted}, Skipped: {skipped}')

if __name__ == '__main__':
    import_questions()
