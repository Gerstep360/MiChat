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
from dotenv import load_dotenv
import sqlite3
# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# Crear la aplicación Flask
app = Flask(__name__, static_folder='static', template_folder='templates')

# Configurar la clave secreta desde las variables de entorno
app.secret_key = os.getenv('SECRET_KEY')

# Configurar las sesiones
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Inicializar SocketIO
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
    public_key = request.form.get('public_key')
    private_key = request.form.get('private_key')
    # Validar que las claves E2EE estén presentes
    if not public_key or not private_key:
        return jsonify({'error': 'Claves E2EE faltantes.'}), 400
    # Manejar imagen de perfil
    # Manejar imagen de perfil
    file = request.files.get('profile_picture')
    if file and allowed_file(file.filename):
        # Renombrar el archivo al nombre completo del usuario
        # Asegurarse de que el nombre es seguro para usar en un sistema de archivos
        safe_username = secure_filename(username)
        # Obtener la extensión del archivo
        extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{safe_username}.{extension}"
        profile_picture_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Crear el directorio si no existe
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        
        file.save(profile_picture_path)
        # Guardar la ruta relativa para usar en la aplicación
        profile_picture_url = '/' + profile_picture_path.replace('\\', '/')
    else:
        profile_picture_url = '/static/img/none.jpg'

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
    session['public_key'] = public_key
    session['private_key'] = private_key
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
    code = request.json.get('code')
    if code == session.get('verification_code'):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, email, phone, password, profile_picture, display_name, is_verified, public_key, private_key)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['username'],
            session['email'],
            session['phone'],
            session['password'],
            session['profile_picture'],
            session['display_name'],
            1,
            session['public_key'],
            session['private_key']
        ))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        session['user_id'] = user_id
        # Limpiar las claves de la sesión
        session.pop('public_key', None)
        session.pop('private_key', None)
        session.pop('verification_code', None)
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
@app.route('/logout', methods=['GET'])
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
               u.username, u.profile_picture, u.public_key,
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
            'last_message': chat['last_message'] or '',
            'public_key': chat['public_key']
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
    # Incluir public_key y private_key en la consulta
    cursor.execute('SELECT id, username, profile_picture, public_key, private_key FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        user_info = {
            'id': user['id'],
            'username': user['username'],
            'profile_picture': user['profile_picture'] or '/static/img/default_profile.png',
            'public_key': user['public_key'],
            'private_key': user['private_key']
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
    # Incluir public_key en la consulta
    cursor.execute('SELECT id, username, profile_picture, status, last_seen, public_key FROM users WHERE id = ?', (other_user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        user_info = {
            'id': user['id'],
            'username': user['username'],
            'profile_picture': user['profile_picture'] or '/static/img/default_profile.png',
            'status': user['status'],
            'last_seen': user['last_seen'],
            'public_key': user['public_key']
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
    room = data.get('room')
    message = data.get('message', '').strip()
    user_id = session.get('user_id')


    if not message:
        print("Error: Mensaje vacío recibido en el backend.")
        emit('error', {'error': 'El mensaje está vacío.'}, room=request.sid)
        return

    # Validar usuario autenticado
    if not user_id:
        emit('error', {'error': 'No autenticado'}, room=request.sid)
        return

    # Validar contenido del mensaje
    if not message:
        emit('error', {'error': 'El mensaje está vacío.'}, room=request.sid)
        return

    # Validar destinatario
    recipient_id = data.get('recipient_id')
    if not recipient_id:
        emit('error', {'error': 'Destinatario no especificado'}, room=request.sid)
        return

    # Conexión a la base de datos
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener o crear el chat
    cursor.execute('''
        SELECT chat_id FROM chats WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
    ''', (user_id, recipient_id, recipient_id, user_id))
    chat = cursor.fetchone()

    if not chat:
        # Crear nuevo chat si no existe
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
    cursor.execute('SELECT username, profile_picture, public_key FROM users WHERE id = ?', (user_id,))
    sender_info = cursor.fetchone()
    conn.close()

    # Validar clave pública del remitente
    sender_public_key = sender_info['public_key']
    if not sender_public_key or len(sender_public_key) not in [130, 66]:
        print(f"Clave pública inválida para el usuario {user_id}: {sender_public_key}")
        sender_public_key = "Clave pública faltante o inválida"

    # Emitir mensaje al chat
    emit('receive_message', {
        'content': message,
        'sender_id': user_id,
        'sender_username': sender_info['username'] or "Usuario desconocido",
        'sender_profile_picture': sender_info['profile_picture'] or '/static/img/none.jpg',
        'sender_public_key': sender_public_key,
        'chat_id': chat_id
    }, room=f'chat_{chat_id}')

    # Notificar al destinatario para actualizar su lista de chats
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
def notify_profile_picture_update(socketio, user_id, new_profile_picture_url):
    """
    Notifica a todos los contactos del usuario que ha actualizado su foto de perfil.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    # Obtener todos los contactos del usuario
    cursor.execute('''
        SELECT DISTINCT user1_id AS contact_id FROM chats WHERE user2_id = ?
        UNION
        SELECT DISTINCT user2_id AS contact_id FROM chats WHERE user1_id = ?
    ''', (user_id, user_id))
    contacts = cursor.fetchall()
    conn.close()
    for contact in contacts:
        contact_id = contact['contact_id']
        data = {
            'user_id': user_id,
            'new_profile_picture_url': new_profile_picture_url
        }
        # Emitir el evento a la sala del contacto
        socketio.emit('profile_picture_update', data, room=f'user_{contact_id}')
# Ruta para cambiar la foto de perfil (POST)
@app.route('/change_profile_picture', methods=['POST'])
def change_profile_picture():
    try:
        if 'user_id' not in session:
            print("Usuario no autenticado.")
            return jsonify({'error': 'No autenticado'}), 401
        user_id = session['user_id']
        file = request.files.get('profile_picture')
        if file and allowed_file(file.filename):
            print(f"Archivo recibido: {file.filename}")
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT username, profile_picture FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            if not user:
                print(f"Usuario con ID {user_id} no encontrado.")
                conn.close()
                return jsonify({'error': 'Usuario no encontrado.'}), 404
            old_profile_picture = user['profile_picture']
            print(f"Foto de perfil anterior: {old_profile_picture}")

            # Eliminar la foto de perfil anterior si no es la predeterminada
            if old_profile_picture and old_profile_picture != '/static/img/default_profile.png':
                old_picture_path = os.path.join(app.root_path, 'static', 'uploads', os.path.basename(old_profile_picture))
                print(f"Intentando eliminar la foto de perfil anterior en: {old_picture_path}")
                if os.path.exists(old_picture_path):
                    try:
                        os.remove(old_picture_path)
                        print(f"Eliminado {old_picture_path}")
                    except Exception as e:
                        print(f"Error al eliminar {old_picture_path}: {e}")

            # Renombrar el archivo al nombre completo del usuario
            safe_username = secure_filename(user['username'])
            extension = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{safe_username}.{extension}"
            profile_picture_path = os.path.join(app.root_path, 'static', 'uploads', filename)
            print(f"Guardando la nueva foto de perfil en: {profile_picture_path}")

            # Guardar el nuevo archivo
            file.save(profile_picture_path)
            profile_picture_url = f"/static/uploads/{filename}"
            print(f"Foto de perfil actualizada a: {profile_picture_url}")

            # Actualizar la base de datos
            cursor.execute('UPDATE users SET profile_picture = ? WHERE id = ?', (profile_picture_url, user_id))
            conn.commit()
            conn.close()

            # Notificar a los contactos sobre la actualización de la foto de perfil
            notify_profile_picture_update(socketio, user_id, profile_picture_url)

            return jsonify({'status': 'success', 'profile_picture': profile_picture_url}), 200
        else:
            print("No se proporcionó una imagen válida.")
            return jsonify({'error': 'No se proporcionó una imagen válida.'}), 400
    except Exception as e:
        print(f"Error en change_profile_picture: {e}")
        return jsonify({'error': 'Error interno del servidor.'}), 500

# Ruta para eliminar la foto de perfil (POST)
@app.route('/delete_profile_picture', methods=['POST'])
def delete_profile_picture():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT profile_picture FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'Usuario no encontrado.'}), 404
    profile_picture = user['profile_picture']

    # Eliminar la foto de perfil si no es la predeterminada
    if profile_picture and profile_picture != '/static/img/none.jpg':
        picture_path = os.path.join(app.root_path, '../../', profile_picture.lstrip('/'))
        if os.path.exists(picture_path):
            os.remove(picture_path)
    
    # Actualizar la base de datos para usar la imagen predeterminada
    cursor.execute('UPDATE users SET profile_picture = ? WHERE id = ?', ('/static/img/default_profile.png', user_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success', 'profile_picture': '/static/img/default_profile.png'}), 200


if __name__ == '__main__':
    # Inicializar la base de datos
    init_db()
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)
