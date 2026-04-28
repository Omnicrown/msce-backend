from flask import Flask, request, jsonify, Response, abort
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os, time, functools, base64

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'msce.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ADMIN_USER = 'admin'
ADMIN_PASS = generate_password_hash('msce@admin2025')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                code TEXT,
                created INTEGER DEFAULT (strftime('%s','now'))
            );
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                year INTEGER,
                paper_type TEXT NOT NULL,
                filename TEXT NOT NULL,
                filesize INTEGER,
                uploaded INTEGER DEFAULT (strftime('%s','now')),
                FOREIGN KEY(subject_id) REFERENCES subjects(id)
            );
        """)
        subjects = [
            ('Mathematics','MAT'),('English','ENG'),('Biology','BIO'),
            ('Chemistry','CHE'),('Physics','PHY'),('History','HIS'),
            ('Geography','GEO'),('Chichewa','CHI'),('Agriculture','AGR'),
            ('Computer Studies','COM'),('Business Studies','BUS'),('French','FRE')
        ]
        for name, code in subjects:
            try:
                db.execute("INSERT INTO subjects(name,code) VALUES(?,?)", (name, code))
            except:
                pass
        db.commit()

init_db()

def require_admin(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Basic '):
            abort(401)
        try:
            creds = base64.b64decode(auth[6:]).decode()
            user, pwd = creds.split(':', 1)
        except:
            abort(401)
        if user != ADMIN_USER or not check_password_hash(ADMIN_PASS, pwd):
            abort(403)
        return f(*args, **kwargs)
    return wrapper

@app.route('/')
def home():
    return jsonify({'status': 'MSCE Backend running'})

@app.route('/subjects')
def list_subjects():
    with get_db() as db:
        rows = db.execute("SELECT * FROM subjects ORDER BY name").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/papers')
def list_papers():
    subject_id = request.args.get('subject_id')
    paper_type = request.args.get('paper_type')
    query = "SELECT p.*, s.name as subject_name FROM papers p JOIN subjects s ON p.subject_id=s.id WHERE 1=1"
    params = []
    if subject_id:
        query += " AND p.subject_id=?"
        params.append(subject_id)
    if paper_type:
        query += " AND p.paper_type=?"
        params.append(paper_type)
    query += " ORDER BY p.year DESC"
    with get_db() as db:
        rows = db.execute(query, params).fetchall()
    return jsonify([dict(r) for r in rows])

@app.route('/view/<int:paper_id>')
def view_paper(paper_id):
    with get_db() as db:
        paper = db.execute("SELECT * FROM papers WHERE id=?", (paper_id,)).fetchone()
    if not paper:
        abort(404)
    filepath = os.path.join(UPLOAD_FOLDER, paper['filename'])
    if not os.path.exists(filepath):
        abort(404)
    with open(filepath, 'rb') as f:
        data = f.read()
    response = Response(data, mimetype='application/pdf')
    response.headers['Content-Disposition'] = 'inline'
    response.headers['Cache-Control'] = 'no-store'
    return response

@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if data.get('username') == ADMIN_USER and check_password_hash(ADMIN_PASS, data.get('password', '')):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Wrong credentials'}), 401

@app.route('/admin/upload', methods=['POST'])
@require_admin
def upload_paper():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400
    file = request.files['file']
    subject_id = request.form.get('subject_id')
    title = request.form.get('title', '').strip()
    year = request.form.get('year')
    paper_type = request.form.get('paper_type', 'past_paper')
    if not subject_id or not title:
        return jsonify({'error': 'subject_id and title required'}), 400
    filename = secure_filename(str(int(time.time())) + '_' + file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    filesize = os.path.getsize(filepath)
    with get_db() as db:
        cur = db.execute(
            "INSERT INTO papers(subject_id,title,year,paper_type,filename,filesize) VALUES(?,?,?,?,?,?)",
            (subject_id, title, year, paper_type, filename, filesize)
        )
        db.commit()
    return jsonify({'success': True, 'paper_id': cur.lastrowid})

@app.route('/admin/papers/<int:paper_id>', methods=['DELETE'])
@require_admin
def delete_paper(paper_id):
    with get_db() as db:
        paper = db.execute("SELECT * FROM papers WHERE id=?", (paper_id,)).fetchone()
        if not paper:
            abort(404)
        filepath = os.path.join(UPLOAD_FOLDER, paper['filename'])
        if os.path.exists(filepath):
            os.remove(filepath)
        db.execute("DELETE FROM papers WHERE id=?", (paper_id,))
        db.commit()
    return jsonify({'success': True})

@app.route('/admin/subjects', methods=['POST'])
@require_admin
def add_subject():
    data = request.get_json()
    name = data.get('name', '').strip()
    code = data.get('code', '').strip()
    if not name:
        return jsonify({'error': 'Name required'}), 400
    with get_db() as db:
        cur = db.execute("INSERT INTO subjects(name,code) VALUES(?,?)", (name, code))
        db.commit()
    return jsonify({'success': True, 'id': cur.lastrowid})

@app.route('/admin/stats')
@require_admin
def stats():
    with get_db() as db:
        total = db.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        subjects = db.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
        per_type = db.execute("SELECT paper_type, COUNT(*) as cnt FROM papers GROUP BY paper_type").fetchall()
    return jsonify({
        'total_papers': total,
        'total_subjects': subjects,
        'by_type': {r['paper_type']: r['cnt'] for r in per_type}
    })

if __name__ == '__main__':
    app.run(debug=True)