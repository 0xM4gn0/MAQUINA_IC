import os
import sqlite3
from flask import Flask, render_template, render_template_string, request, session, redirect, url_for
from werkzeug.security import check_password_hash
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'clinica.db')
DOCS_DIR = os.path.join(BASE_DIR, 'documentos')
app = Flask(__name__)
app.secret_key = 'lab-clinica-aurora-secret'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sobre-nosotros')
def about():
    return render_template('about.html')

@app.route('/noticias')
def news():
    return render_template('news.html')

@app.route('/plantilla')
def team():
    return render_template('team.html')

@app.route('/servicios')
def servicios():
    categoria = request.args.get('categoria')
    conn = get_db()
    cur = conn.cursor()
    categorias = [r['categoria'] for r in cur.execute('SELECT DISTINCT categoria FROM servicios ORDER BY categoria').fetchall()]
    resultados = []
    disponible = None
    if categoria is None:
        resultados = cur.execute('SELECT id, nombre, categoria FROM servicios ORDER BY id').fetchall()
    else:
        comprobacion = "SELECT id FROM servicios WHERE categoria = '" + categoria + "'"
        try:
            disponible = len(cur.execute(comprobacion).fetchall()) > 0
        except sqlite3.Error:
            disponible = False
        resultados = cur.execute('SELECT id, nombre, categoria FROM servicios WHERE categoria = ? ORDER BY id', (categoria,)).fetchall()
    conn.close()
    return render_template('servicios.html', categorias=categorias, categoria_activa=categoria, resultados=resultados, disponible=disponible)

def usuario_actual():
    if 'usuario' not in session:
        return None
    conn = get_db()
    row = conn.execute('SELECT * FROM users WHERE username = ?', (session['usuario'],)).fetchone()
    conn.close()
    return row

@app.route('/portal/login', methods=['GET', 'POST'])
def portal_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        conn = get_db()
        row = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if row is not None:
            almacenado = row['password']
            # Las contraseñas hasheadas (p. ej. la del sysadmin) se verifican con
            # check_password_hash; el resto siguen en texto plano (laboratorio).
            if almacenado.startswith(('pbkdf2:', 'scrypt:')):
                valida = check_password_hash(almacenado, password)
            else:
                valida = (almacenado == password)
            if valida:
                session['usuario'] = row['username']
                return redirect(url_for('portal_home'))
        error = 'Usuario o contraseña incorrectos.'
    return render_template('portal_login.html', error=error)

@app.route('/portal/logout')
def portal_logout():
    session.clear()
    return redirect(url_for('portal_login'))

@app.route('/portal')
def portal_home():
    user = usuario_actual()
    if user is None:
        return redirect(url_for('portal_login'))
    return render_template('portal.html', user=user)

@app.route('/portal/chatbot')
def portal_chatbot():
    user = usuario_actual()
    if user is None:
        return redirect(url_for('portal_login'))
    conn = get_db()
    conversaciones = conn.execute('SELECT id, titulo, creado_en FROM conversaciones WHERE usuario = ? ORDER BY id', (user['username'],)).fetchall()
    conn.close()
    return render_template('chatbot.html', user=user, conversaciones=conversaciones)

@app.route('/portal/chatbot/<int:conv_id>', methods=['GET', 'POST'])
def portal_conversacion(conv_id):
    user = usuario_actual()
    if user is None:
        return redirect(url_for('portal_login'))
    conn = get_db()
    conv = conn.execute('SELECT id, usuario, titulo, creado_en FROM conversaciones WHERE id = ?', (conv_id,)).fetchone()
    if conv is None:
        conn.close()
        return (render_template('conversacion.html', user=user, conv=None, mensajes=[]), 404)
    if request.method == 'POST':
        texto = request.form.get('mensaje', '').strip()
        if texto:
            conn.execute("INSERT INTO chat_mensajes (conversacion_id, autor, texto) VALUES (?, 'usuario', ?)", (conv_id, texto))
            conn.execute("INSERT INTO chat_mensajes (conversacion_id, autor, texto) VALUES (?, 'bot', ?)", (conv_id, responder_bot(texto)))
            conn.commit()
    mensajes = conn.execute('SELECT autor, texto, creado_en FROM chat_mensajes WHERE conversacion_id = ? ORDER BY id', (conv_id,)).fetchall()
    conn.close()
    return render_template('conversacion.html', user=user, conv=conv, mensajes=mensajes)

def responder_bot(mensaje):
    m = mensaje.lower()
    if 'hola' in m or 'buenas' in m:
        return '¡Hola! Soy AuroraBot, el asistente interno. ¿En qué puedo ayudarte?'
    if 'cita' in m or 'agenda' in m:
        return 'Para gestionar citas, entra en Agenda > Nueva cita y busca al paciente.'
    if 'informe' in m or 'radiolog' in m or 'pdf' in m:
        return 'Puedes exportar informes desde el visor, en el botón Exportar.'
    return 'Soy un asistente de demostración. Puedo orientarte sobre agenda, informes y protocolos internos.'

def es_admin(user):
    return user is not None and user['rol'] == 'Administrador de Sistemas'

@app.route('/admin')
def admin_home():
    user = usuario_actual()
    if user is None:
        return redirect(url_for('portal_login'))
    if not es_admin(user):
        return (render_template('admin_denegado.html', user=user), 403)
    os.makedirs(DOCS_DIR, exist_ok=True)
    docs = sorted(os.listdir(DOCS_DIR))
    return render_template('admin.html', user=user, docs=docs, subido=request.args.get('subido'), borrado=request.args.get('borrado'), error=request.args.get('error'))

@app.route('/admin/subir', methods=['POST'])
def admin_subir():
    user = usuario_actual()
    if not es_admin(user):
        return redirect(url_for('portal_login'))
    f = request.files.get('documento')
    if f and f.filename:
        nombre = os.path.basename(f.filename)
        if '.txt' not in nombre.lower():
            return redirect(url_for('admin_home', error='ext'))
        os.makedirs(DOCS_DIR, exist_ok=True)
        f.save(os.path.join(DOCS_DIR, nombre))
        return redirect(url_for('admin_home', subido=nombre))
    return redirect(url_for('admin_home'))

@app.route('/admin/borrar', methods=['POST'])
def admin_borrar():
    user = usuario_actual()
    if not es_admin(user):
        return redirect(url_for('portal_login'))
    nombre = os.path.basename(request.form.get('nombre', ''))
    if nombre:
        ruta = os.path.join(DOCS_DIR, nombre)
        if os.path.isfile(ruta):
            os.remove(ruta)
            return redirect(url_for('admin_home', borrado=nombre))
    return redirect(url_for('admin_home'))

@app.route('/admin/preview/<path:nombre>')
def admin_preview(nombre):
    user = usuario_actual()
    if not es_admin(user):
        return redirect(url_for('portal_login'))
    ruta = os.path.join(DOCS_DIR, os.path.basename(nombre))
    if not os.path.isfile(ruta):
        return (render_template('admin_preview.html', user=user, nombre=nombre, render='(documento no encontrado)'), 404)
    with open(ruta, 'r', errors='ignore') as fh:
        contenido = fh.read()
    contexto = {'clinica': 'Clínica Aurora Salud', 'anio': 2026}
    try:
        render = render_template_string(contenido, **contexto)
    except Exception as e:
        render = 'Error al renderizar la plantilla: %s' % e
    return render_template('admin_preview.html', user=user, nombre=nombre, render=render)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
