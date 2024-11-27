# server.py

from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from flask_session import Session
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import random
import string
from datetime import datetime
from database import get_db_connection, init_db
from email_verification import send_verification_email

import sqlite3
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.urandom(24)  # Genera una clave secreta aleatoria
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
socketio = SocketIO(app, manage_session=False)

# Configuración de subida de archivos
UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ruta para la página principal
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('chat_list'))
    else:
        return redirect(url_for('login_page'))

# Ruta para la página de registro (GET)
@app.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')

# Ruta para el registro de usuario (POST)
@app.route('/register', methods=['POST'])
def register_user():
    username = request.form['username']
    display_name = request.form['display_name']
    email = request.form['email']
    phone = request.form['phone']
    password = request.form['password']

    # Manejar imagen de perfil
    file = request.files.get('profile_picture')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        profile_picture_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Crear el directorio si no existe
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        file.save(profile_picture_path)
        # Guardar la ruta relativa para usar en la aplicación
        profile_picture_url = '/' + profile_picture_path.replace('\\', '/')
    else:
        profile_picture_url = '/static/img/default_profile.png'

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE email = ? OR phone = ?', (email, phone))
    existing_user = cursor.fetchone()
    if existing_user:
        conn.close()
        return jsonify({'error': 'El usuario ya existe.'}), 400

    # Generar código de verificación
    verification_code = ''.join(random.choices(string.digits, k=6))
    session['verification_code'] = verification_code
    session['email'] = email
    session['username'] = username
    session['display_name'] = display_name
    session['password'] = generate_password_hash(password)
    session['phone'] = phone
    session['profile_picture'] = profile_picture_url

    # Enviar correo de verificación
    send_verification_email(email, verification_code)

    conn.close()
    return jsonify({'status': 'Se ha enviado un código de verificación a tu correo.'}), 200

# Ruta para la página de verificación (GET)
@app.route('/verify', methods=['GET'])
def verify_page():
    return render_template('verify.html')

# Ruta para verificar el código (POST)
@app.route('/verify', methods=['POST'])
def verify_code():
    code = request.json['code']
    if code == session.get('verification_code'):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, email, phone, password, profile_picture, display_name, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (session['username'], session['email'], session['phone'], session['password'], session['profile_picture'], session['display_name'], 1))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        session['user_id'] = user_id
        return jsonify({'status': 'Usuario verificado y registrado.'}), 200
    else:
        return jsonify({'error': 'Código de verificación incorrecto.'}), 400

# Ruta para la página de inicio de sesión (GET)
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

# Ruta para el inicio de sesión (POST)
@app.route('/login', methods=['POST'])
def login_user():
    data = request.json
    email_or_phone = data['email_or_phone']
    password = data['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ? OR phone = ?', (email_or_phone, email_or_phone))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({'status': 'Login exitoso.'}), 200
    else:
        return jsonify({'error': 'Credenciales incorrectas.'}), 400

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

# Ruta para verificar la sesión
@app.route('/check_session', methods=['GET'])
def check_session():
    if 'user_id' in session:
        return jsonify({'status': 'Autenticado'}), 200
    else:
        return jsonify({'status': 'No autenticado'}), 401



# Obtener la lista de chats del usuario
@app.route('/get_chats', methods=['GET'])
def get_chats():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    user_id = session['user_id']
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row  # Asegurarse de obtener diccionarios
    cursor = conn.cursor()
    cursor.execute('''
        SELECT chats.chat_id, 
               CASE WHEN chats.user1_id = ? THEN chats.user2_id ELSE chats.user1_id END AS user_id,
               u.username, u.profile_picture,
               (SELECT content FROM messages WHERE chat_id = chats.chat_id ORDER BY timestamp DESC LIMIT 1) AS last_message
        FROM chats
        JOIN users u ON u.id = CASE WHEN chats.user1_id = ? THEN chats.user2_id ELSE chats.user1_id END
        WHERE chats.user1_id = ? OR chats.user2_id = ?
    ''', (user_id, user_id, user_id, user_id))
    chats = cursor.fetchall()
    conn.close()
    chat_list = []
    for chat in chats:
        chat_list.append({
            'chat_id': chat['chat_id'],
            'user_id': chat['user_id'],
            'username': chat['username'],
            'profile_picture': chat['profile_picture'] or '/static/img/default_profile.png',
            'last_message': chat['last_message'] or ''
        })
    return jsonify({'chats': chat_list}), 200

# Ruta para iniciar un nuevo chat
@app.route('/start_chat', methods=['POST'])
def start_chat():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    user_id = session['user_id']
    data = request.json
    username = data.get('username')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'Usuario no encontrado.'}), 404
    recipient_id = user['id']
    # Verificar si ya existe un chat
    cursor.execute('''
        SELECT chat_id FROM chats WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
    ''', (user_id, recipient_id, recipient_id, user_id))
    chat = cursor.fetchone()
    if chat:
        conn.close()
        return jsonify({'status': 'Chat ya existente.'}), 200
    # Crear nuevo chat
    cursor.execute('INSERT INTO chats (user1_id, user2_id) VALUES (?, ?)', (user_id, recipient_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'Chat iniciado correctamente.'}), 200

# Ruta para la página de chat individual
@app.route('/chat', methods=['GET'])
def chat_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('chat.html')
# Obtener información del usuario actual
@app.route('/get_current_user', methods=['GET'])
def get_current_user():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, profile_picture FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        user_info = {
            'id': user['id'],
            'username': user['username'],
            'profile_picture': user['profile_picture'] or '/static/img/default_profile.png'
        }
        return jsonify({'status': True, 'user': user_info}), 200
    else:
        return jsonify({'error': 'Usuario no encontrado.'}), 404
# Obtener información de otro usuario
@app.route('/get_user_info', methods=['GET'])
def get_user_info():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    other_user_id = request.args.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, profile_picture, status, last_seen FROM users WHERE id = ?', (other_user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        user_info = {
            'id': user['id'],
            'username': user['username'],
            'profile_picture': user['profile_picture'] or '/static/img/default_profile.png',
            'status': user['status'],
            'last_seen': user['last_seen']
        }
        return jsonify({'status': True, 'user': user_info}), 200
    else:
        return jsonify({'error': 'Usuario no encontrado.'}), 404

# Notificar cambios de estado a los contactos
def notify_contacts_status_change(user_id, status, last_seen=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT user1_id AS contact_id FROM chats WHERE user2_id = ?
        UNION
        SELECT DISTINCT user2_id AS contact_id FROM chats WHERE user1_id = ?
    ''', (user_id, user_id))
    contacts = cursor.fetchall()
    conn.close()
    for contact in contacts:
        contact_id = contact['contact_id']
        emit('user_status_update', {
            'user_id': user_id,
            'status': status,
            'last_seen': last_seen.isoformat() if last_seen else None
        }, room=f'user_{contact_id}')

@socketio.on('typing')
def handle_typing(data):
    recipient_id = data.get('recipient_id')
    user_id = session.get('user_id')
    if not user_id:
        emit('error', {'error': 'No autenticado'})
        return
    # Emitir evento de 'escribiendo...' al destinatario
    emit('user_typing', {'sender_id': user_id}, room=f'user_{recipient_id}')

# Enviar mensaje (opcional si usas Socket.IO)
@app.route('/send_message', methods=['POST'])
def send_message():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    data = request.json
    recipient_id = data.get('recipient_id')
    message = data.get('message')
    user_id = session['user_id']
    # Obtener chat_id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT chat_id FROM chats WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
    ''', (user_id, recipient_id, recipient_id, user_id))
    chat = cursor.fetchone()
    if not chat:
        conn.close()
        return jsonify({'error': 'Chat no encontrado.'}), 404
    chat_id = chat['chat_id']
    # Insertar mensaje en la base de datos
    cursor.execute('INSERT INTO messages (chat_id, sender_id, recipient_id, content) VALUES (?, ?, ?, ?)',
                   (chat_id, user_id, recipient_id, message))
    conn.commit()
    conn.close()
    return jsonify({'status': 'Mensaje enviado.'}), 200
# Modificar el evento 'send_message' de Socket.IO
@socketio.on('send_message')
def handle_send_message(data):
    room = data['room']
    message = data['message']
    user_id = session.get('user_id')
    if not user_id:
        emit('error', {'error': 'No autenticado'})
        return

    recipient_id = data.get('recipient_id')
    if not recipient_id:
        emit('error', {'error': 'Destinatario no especificado'})
        return

    # Obtener chat_id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT chat_id FROM chats WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
    ''', (user_id, recipient_id, recipient_id, user_id))
    chat = cursor.fetchone()
    if not chat:
        # Crear un nuevo chat si no existe
        cursor.execute('INSERT INTO chats (user1_id, user2_id) VALUES (?, ?)', (user_id, recipient_id))
        conn.commit()
        chat_id = cursor.lastrowid
    else:
        chat_id = chat['chat_id']
    # Insertar mensaje en la base de datos
    cursor.execute('INSERT INTO messages (chat_id, sender_id, recipient_id, content) VALUES (?, ?, ?, ?)',
                   (chat_id, user_id, recipient_id, message))
    conn.commit()
    # Obtener información del remitente
    cursor.execute('SELECT username, profile_picture FROM users WHERE id = ?', (user_id,))
    sender_info = cursor.fetchone()
    conn.close()
    # Enviar el mensaje a la sala
    emit('receive_message', {
        'message': message,
        'sender_id': user_id,
        'sender_username': sender_info['username'],
        'sender_profile_picture': sender_info['profile_picture'] or '/static/img/default_profile.png',
        'chat_id': chat_id
    }, room=f'chat_{chat_id}')

    # Notificar al destinatario para que actualice su lista de chats
    emit('update_chat_list', {}, room=f'user_{recipient_id}')
    
# Obtener lista de usuarios (para iniciar un nuevo chat)
@app.route('/get_users', methods=['GET'])
def get_users():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, profile_picture FROM users WHERE id != ?', (user_id,))
    users = cursor.fetchall()
    conn.close()
    user_list = []
    for user in users:
        user_list.append({
            'id': user['id'],
            'username': user['username'],
            'profile_picture': user['profile_picture'] or '/static/img/default_profile.png'
        })
    return jsonify({'users': user_list}), 200

# Ruta para la lista de chats (interfaz)
@app.route('/chat_list', methods=['GET'])
def chat_list():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT profile_picture FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        profile_picture = user['profile_picture'] if user['profile_picture'] else '/static/img/default_profile.png'
        return render_template('chat_list.html', profile_picture=profile_picture)
    else:
        # Usuario no encontrado, limpiar sesión y redirigir al login
        session.clear()
        return redirect(url_for('login_page'))


# Obtener mensajes del chat
@app.route('/get_messages', methods=['GET'])
def get_messages():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    chat_id = request.args.get('chat_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT messages.sender_id, messages.content, messages.timestamp, users.username, users.profile_picture
        FROM messages
        JOIN users ON messages.sender_id = users.id
        WHERE messages.chat_id = ?
        ORDER BY messages.timestamp ASC
    ''', (chat_id,))
    messages = cursor.fetchall()
    conn.close()
    message_list = []
    for msg in messages:
        message_list.append({
            'sender_id': msg['sender_id'],
            'content': msg['content'],
            'timestamp': msg['timestamp'],
            'sender_username': msg['username'],
            'sender_profile_picture': msg['profile_picture'] or '/static/img/default_profile.png'
        })
    return jsonify({'messages': message_list}), 200

# Manejo de eventos de Socket.IO
@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        user_id = session['user_id']
        # Unirse a la sala personal
        join_room(f'user_{user_id}')
        # Actualizar estado a 'online'
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET status = ? WHERE id = ?', ('online', user_id))
        conn.commit()
        conn.close()
        # Notificar a los contactos
        notify_contacts_status_change(user_id, 'online')
    else:
        return False

@socketio.on('disconnect')
def handle_disconnect():
    if 'user_id' in session:
        user_id = session['user_id']
        # Actualizar `last_seen` y estado a 'offline'
        conn = get_db_connection()
        cursor = conn.cursor()
        last_seen = datetime.utcnow()
        cursor.execute('UPDATE users SET status = ?, last_seen = ? WHERE id = ?', ('offline', last_seen, user_id))
        conn.commit()
        conn.close()
        # Notificar a los contactos
        notify_contacts_status_change(user_id, 'offline', last_seen)

@socketio.on('join')
def handle_join(data):
    room = data['room']
    join_room(room)

@socketio.on('leave_room')
def handle_leave_room(data):
    room = data['room']
    leave_room(room)
    
# Obtener el chat_id entre dos usuarios
@app.route('/get_chat_id', methods=['GET'])
def get_chat_id():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    user_id = session['user_id']
    other_user_id = request.args.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT chat_id FROM chats WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
    ''', (user_id, other_user_id, other_user_id, user_id))
    chat = cursor.fetchone()
    if not chat:
        # Crear un nuevo chat si no existe
        cursor.execute('INSERT INTO chats (user1_id, user2_id) VALUES (?, ?)', (user_id, other_user_id))
        conn.commit()
        chat_id = cursor.lastrowid
    else:
        chat_id = chat['chat_id']
    conn.close()
    return jsonify({'chat_id': chat_id}), 200


@socketio.on('send_message')
def handle_send_message(data):
    room = data['room']
    message = data['message']
    user_id = session.get('user_id')
    if not user_id:
        emit('error', {'error': 'No autenticado'})
        return

    recipient_id = data.get('recipient_id')
    if not recipient_id:
        emit('error', {'error': 'Destinatario no especificado'})
        return

    # Obtener chat_id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT chat_id FROM chats WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
    ''', (user_id, recipient_id, recipient_id, user_id))
    chat = cursor.fetchone()
    if not chat:
        conn.close()
        emit('error', {'error': 'Chat no encontrado.'})
        return
    chat_id = chat['chat_id']
    # Insertar mensaje en la base de datos
    cursor.execute('INSERT INTO messages (chat_id, sender_id, recipient_id, content) VALUES (?, ?, ?, ?)',
                   (chat_id, user_id, recipient_id, message))
    conn.commit()
    # Obtener información del remitente
    cursor.execute('SELECT username, profile_picture FROM users WHERE id = ?', (user_id,))
    sender_info = cursor.fetchone()
    conn.close()
    # Enviar el mensaje a la sala
    emit('receive_message', {
        'message': message,
        'sender_id': user_id,
        'sender_username': sender_info['username'],
        'sender_profile_picture': sender_info['profile_picture'] or '/static/img/default_profile.png',
        'chat_id': chat_id
    }, room=f'chat_{chat_id}')


if __name__ == '__main__':
    # Inicializar la base de datos
    init_db()
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)
