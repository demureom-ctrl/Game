from flask import Flask, request, jsonify, send_file
import sqlite3
import os
import json
import random

DB_PATH = 'questions.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Use IF NOT EXISTS for questions table
    cur.execute('''CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        difficulty INTEGER NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        options TEXT
    )''')

    # Only seed questions if empty
    # Update: Always try to seed new questions (avoid duplicates)
    try:
        from seeds import DATA as seed
        if seed:
            # Get existing questions (simplified check by question text)
            existing_qs = set(r['question'] for r in cur.execute('SELECT question FROM questions').fetchall())
            
            new_qs = [q for q in seed if q[2] not in existing_qs]
            
            if new_qs:
                cur.executemany('INSERT INTO questions (category,difficulty,question,answer,options) VALUES (?,?,?,?,?)', new_qs)
                print(f"Added {len(new_qs)} new questions to database.")
    except ImportError:
        pass
    
    # --- Proverbs Table ---
    cur.execute('''CREATE TABLE IF NOT EXISTS proverbs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL
    )''')
    
    # Check if proverbs are seeded
    cur.execute('SELECT count(*) FROM proverbs')
    if cur.fetchone()[0] == 0:
        try:
            from seeds import PROVERBS
            if PROVERBS:
                 cur.executemany('INSERT INTO proverbs (content) VALUES (?)', [(p,) for p in PROVERBS])
        except ImportError:
            pass


    # --- Words Table (Heads Up) ---
    cur.execute('''CREATE TABLE IF NOT EXISTS words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        content TEXT NOT NULL
    )''')
    
    # Always try to seed words (INSERT OR IGNORE duplicates)
    try:
        from seeds import WORDS
        if WORDS:
            # Check if each word exists to avoid duplicates (naive check but safe for this scale)
            # Or better: use a unique index or simple Select check.
            # SQLite doesn't have "INSERT IGNORE" exactly like MySQL without unique constraint.
            # Let's just check existence.
            existing = set((r['category'], r['content']) for r in cur.execute('SELECT category, content FROM words').fetchall())
            
            new_words = [w for w in WORDS if (w[0], w[1]) not in existing]
            
            if new_words:
                cur.executemany('INSERT INTO words (category, content) VALUES (?, ?)', new_words)
                print(f"Added {len(new_words)} new words to database.")
    except ImportError:
        pass

    conn.commit()
    conn.close()

app = Flask(__name__, static_folder='.')

# Initialize DB at import time (avoid relying on decorator availability)
init_db()

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/api/categories')
def categories():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT DISTINCT category FROM questions')
    rows = cur.fetchall()
    cats = [r['category'] for r in rows]
    conn.close()
    return jsonify(cats)

@app.route('/api/start', methods=['POST'])
def start():
    data = request.get_json() or {}
    selected = data.get('selectedCategories', [])
    questions_out = []
    conn = get_db_connection()
    cur = conn.cursor()
    id_counter = 1
    for cat in selected:
        cat_name = cat.get('name')
        mode = cat.get('mode','text')
        for level in range(1,6):
            cur.execute('SELECT * FROM questions WHERE category=? AND difficulty=?', (cat_name, level))
            pool = cur.fetchall()
            if not pool:
                continue
            qrow = random.choice(pool)
            options = json.loads(qrow['options']) if qrow['options'] else []
            questions_out.append({
                'id': id_counter,
                'category': qrow['category'],
                'points': level * 100,
                'question': qrow['question'],
                'answer': qrow['answer'],
                'difficulty': level,
                'answered': False,
                'mode': mode,
                'options': options
            })
            id_counter += 1
    conn.close()
    return jsonify({'questions': questions_out})

@app.route('/api/questions', methods=['POST'])
def add_question():
    data = request.get_json() or {}
    category = data.get('category')
    difficulty = int(data.get('difficulty',1))
    question = data.get('question')
    answer = data.get('answer')
    options = data.get('options') or []
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('INSERT INTO questions (category,difficulty,question,answer,options) VALUES (?,?,?,?,?)', (category,difficulty,question,answer,json.dumps(options)))
    conn.commit()
    qid = cur.lastrowid
    conn.close()
    return jsonify({'id': qid}), 201


@app.route('/api/questions', methods=['GET'])
def list_questions():
    conn = get_db_connection()
    cur = conn.cursor()
    cat = request.args.get('category')
    if cat:
        cur.execute('SELECT * FROM questions WHERE category=?', (cat,))
    else:
        cur.execute('SELECT * FROM questions')
    rows = cur.fetchall()
    out = []
    for r in rows:
        out.append({'id': r['id'], 'category': r['category'], 'difficulty': r['difficulty'], 'question': r['question'], 'answer': r['answer'], 'options': json.loads(r['options']) if r['options'] else []})
    conn.close()
    return jsonify(out)


@app.route('/api/questions/<int:qid>', methods=['GET', 'PUT', 'DELETE'])
def question_detail(qid):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'GET':
        cur.execute('SELECT * FROM questions WHERE id=?', (qid,))
        r = cur.fetchone()
        conn.close()
        if not r:
            return jsonify({'error':'not found'}), 404
        return jsonify({'id': r['id'], 'category': r['category'], 'difficulty': r['difficulty'], 'question': r['question'], 'answer': r['answer'], 'options': json.loads(r['options']) if r['options'] else []})

    if request.method == 'PUT':
        data = request.get_json() or {}
        category = data.get('category')
        difficulty = int(data.get('difficulty',1))
        question = data.get('question')
        answer = data.get('answer')
        options = data.get('options') or []
        cur.execute('UPDATE questions SET category=?, difficulty=?, question=?, answer=?, options=? WHERE id=?', (category,difficulty,question,answer,json.dumps(options), qid))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})

    if request.method == 'DELETE':
        cur.execute('DELETE FROM questions WHERE id=?', (qid,))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})


@app.route('/admin')
def admin_ui():
    return send_file('admin.html')

# --- PROVERBS API (Wala Kilma) ---
@app.route('/api/proverbs', methods=['GET', 'POST'])
def handle_proverbs():
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'GET':
        cur.execute('SELECT * FROM proverbs')
        rows = cur.fetchall()
        out = [{'id': r['id'], 'content': r['content']} for r in rows]
        conn.close()
        return jsonify(out)
    else: # POST
        data = request.get_json()
        content = data.get('content')
        if not content:
            conn.close()
            return jsonify({'error': 'Content required'}), 400
        cur.execute('INSERT INTO proverbs (content) VALUES (?)', (content,))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return jsonify({'id': new_id}), 201

@app.route('/api/proverbs/<int:pid>', methods=['PUT', 'DELETE'])
def proverb_detail(pid):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'PUT':
        data = request.get_json()
        content = data.get('content')
        cur.execute('UPDATE proverbs SET content=? WHERE id=?', (content, pid))
        conn.commit()
        conn.close()
        return jsonify({'status': 'updated'})
    else: # DELETE
        cur.execute('DELETE FROM proverbs WHERE id=?', (pid,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'deleted'})

@app.route('/api/proverbs/random')
def random_proverb():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM proverbs ORDER BY RANDOM() LIMIT 1')
    row = cur.fetchone()
    conn.close()
    if row:
        return jsonify({'id': row['id'], 'content': row['content']})
    return jsonify({'error': 'No proverbs found'}), 404

# --- WORDS API (Heads Up) ---
@app.route('/api/words', methods=['GET', 'POST'])
def handle_words():
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'GET':
        cur.execute('SELECT * FROM words')
        rows = cur.fetchall()
        out = [{'id': r['id'], 'category': r['category'], 'content': r['content']} for r in rows]
        conn.close()
        return jsonify(out)
    else: # POST
        data = request.get_json()
        category = data.get('category')
        content = data.get('content')
        if not category or not content:
            conn.close()
            return jsonify({'error': 'Category and Content required'}), 400
        cur.execute('INSERT INTO words (category, content) VALUES (?, ?)', (category, content))
        conn.commit()
        new_id = cur.lastrowid
        conn.close()
        return jsonify({'id': new_id}), 201

@app.route('/api/words/<int:wid>', methods=['PUT', 'DELETE'])
def word_detail(wid):
    conn = get_db_connection()
    cur = conn.cursor()
    if request.method == 'PUT':
        data = request.get_json()
        category = data.get('category')
        content = data.get('content')
        cur.execute('UPDATE words SET category=?, content=? WHERE id=?', (category, content, wid))
        conn.commit()
        conn.close()
        return jsonify({'status': 'updated'})
    else: # DELETE
        cur.execute('DELETE FROM words WHERE id=?', (wid,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'deleted'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
