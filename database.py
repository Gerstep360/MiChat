# database.py 

import sqlite3

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Crear tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            display_name TEXT,
            email TEXT UNIQUE NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            profile_picture TEXT,
            status TEXT,
            is_verified INTEGER DEFAULT 0
            -- No incluimos last_seen aquí
        )
    ''')
    
    # Verificar si las columnas 'last_seen' y 'public_key' existen
    cursor.execute("PRAGMA table_info(users);")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Agregar 'last_seen' si no existe
    if 'last_seen' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN last_seen DATETIME;')
    
    # Agregar 'public_key' si no existe
    if 'public_key' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN public_key TEXT;')
    
    # Crear tabla de chats
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER,
            user2_id INTEGER,
            FOREIGN KEY(user1_id) REFERENCES users(id),
            FOREIGN KEY(user2_id) REFERENCES users(id)
        )
    ''')
    
    # Crear tabla de mensajes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            sender_id INTEGER,
            recipient_id INTEGER,
            content TEXT,
            nonce TEXT,  -- Para almacenar el nonce utilizado en el cifrado
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(chat_id) REFERENCES chats(chat_id),
            FOREIGN KEY(sender_id) REFERENCES users(id),
            FOREIGN KEY(recipient_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()
