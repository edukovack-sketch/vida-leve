import os
import sqlite3
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
import bleach
import bcrypt

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'vidaleve-secret-key-2026')

DB_PATH = os.path.join(os.path.dirname(__file__), 'vidaleve.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            senha_hash TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS contatos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            email TEXT,
            mensagem TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS orcamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            email TEXT,
            servico TEXT,
            mensagem TEXT,
            status TEXT DEFAULT 'pendente',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS trafego (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rota TEXT,
            ip TEXT,
            user_agent TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    # Cria admin padrão se não existir
    admin_check = c.execute('SELECT id FROM usuarios WHERE username = ?', ('admin',)).fetchone()
    if not admin_check:
        try:
            hash_senha = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
            c.execute('INSERT INTO usuarios (username, senha_hash) VALUES (?, ?)', ('admin', hash_senha))
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()

init_db()

def sanitizar(texto):
    if not texto:
        return texto
    return bleach.clean(texto.strip())

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Faça login para acessar.', 'aviso')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

@app.before_request
def log_trafego():
    try:
        conn = get_db()
        conn.execute(
            'INSERT INTO trafego (rota, ip, user_agent) VALUES (?, ?, ?)',
            (request.path, request.remote_addr, str(request.user_agent)[:200])
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

@app.route('/')
def index():
    return send_file(os.path.join(app.root_path, 'index.html'))

@app.route('/contato', methods=['GET', 'POST'])
def contato():
    if request.method == 'GET':
        return render_template('contato.html')

    nome = sanitizar(request.form.get('nome', ''))
    telefone = sanitizar(request.form.get('telefone', ''))
    email = sanitizar(request.form.get('email', ''))
    mensagem = sanitizar(request.form.get('mensagem', ''))

    if not nome or not mensagem:
        return jsonify({'sucesso': False, 'erro': 'Nome e mensagem são obrigatórios.'}), 400

    conn = get_db()
    conn.execute(
        'INSERT INTO contatos (nome, telefone, email, mensagem) VALUES (?, ?, ?, ?)',
        (nome, telefone, email, mensagem)
    )
    conn.commit()
    conn.close()

    return jsonify({'sucesso': True, 'mensagem': 'Mensagem enviada com sucesso!'})

@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')

@app.route('/servicos')
def servicos():
    return render_template('servicos.html')


@app.route('/sobre')
def sobre():
    return redirect(url_for('index') + '#sobre')


@app.route('/trabalhe-conosco')
def trabalhe_conosco():
    return redirect(url_for('index') + '#trabalhe-conosco')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        senha = request.form.get('senha', '')

        conn = get_db()
        user = conn.execute(
            'SELECT * FROM usuarios WHERE username = ?', (username,)
        ).fetchone()
        conn.close()

        if user and bcrypt.checkpw(senha.encode('utf-8'), user['senha_hash']):
            session['usuario_id'] = user['id']
            session['username'] = user['username']
            flash('Login realizado com sucesso!', 'sucesso')
            return redirect(url_for('admin'))
        else:
            flash('Usuário ou senha inválidos.', 'erro')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu da conta.', 'sucesso')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    conn = get_db()

    total_contatos = conn.execute('SELECT COUNT(*) FROM contatos').fetchone()[0]
    total_orcamentos = conn.execute('SELECT COUNT(*) FROM orcamentos').fetchone()[0]
    pendentes = conn.execute("SELECT COUNT(*) FROM orcamentos WHERE status = 'pendente'").fetchone()[0]

    # Contatos dos últimos 7 dias
    dias = []
    contagem = []
    for i in range(6, -1, -1):
        data = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        label = (datetime.now() - timedelta(days=i)).strftime('%d/%m')
        count = conn.execute(
            "SELECT COUNT(*) FROM contatos WHERE DATE(criado_em) = ?", (data,)
        ).fetchone()[0]
        dias.append(label)
        contagem.append(count)

    contatos_recentes = conn.execute(
        'SELECT * FROM contatos ORDER BY criado_em DESC LIMIT 10'
    ).fetchall()
    orcamentos_recentes = conn.execute(
        'SELECT * FROM orcamentos ORDER BY criado_em DESC LIMIT 10'
    ).fetchall()

    conn.close()

    return render_template('admin.html',
        total_contatos=total_contatos,
        total_orcamentos=total_orcamentos,
        pendentes=pendentes,
        labels=dias,
        dados=contagem,
        contatos_recentes=contatos_recentes,
        orcamentos_recentes=orcamentos_recentes
    )

@app.route('/admin/contatos')
@login_required
def admin_contatos():
    conn = get_db()
    contatos = conn.execute('SELECT * FROM contatos ORDER BY criado_em DESC').fetchall()
    conn.close()
    return render_template('admin_contatos.html', contatos=contatos)

@app.route('/admin/contato/<int:id>', methods=['POST'])
@login_required
def apagar_contato(id):
    conn = get_db()
    conn.execute('DELETE FROM contatos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Contato apagado.', 'sucesso')
    return redirect(url_for('admin_contatos'))

@app.route('/api/stats')
@login_required
def api_stats():
    conn = get_db()
    dias = []
    contagem = []
    for i in range(6, -1, -1):
        data = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        label = (datetime.now() - timedelta(days=i)).strftime('%d/%m')
        count = conn.execute(
            "SELECT COUNT(*) FROM contatos WHERE DATE(criado_em) = ?", (data,)
        ).fetchone()[0]
        dias.append(label)
        contagem.append(count)

    trafego_dia = conn.execute(
        "SELECT COUNT(*) FROM trafego WHERE DATE(criado_em) = DATE('now')"
    ).fetchone()[0]

    conn.close()
    return jsonify({
        'dias': dias,
        'contagem': contagem,
        'trafego_hoje': trafego_dia
    })

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', '0') == '1', host='0.0.0.0', port=5000)
