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
            is_verified INTEGER DEFAULT 0,
            last_seen DATETIME,
            public_key TEXT NOT NULL,       -- Clave pública para E2EE
            private_key TEXT NOT NULL       -- Clave privada para E2EE
        )
    ''')
    
    # Crear tabla de chats
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER,
            user2_id INTEGER,
            derived_key TEXT,               -- Clave derivada para E2EE
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
        content TEXT,  -- Almacena el mensaje cifrado JSON
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(chat_id) REFERENCES chats(chat_id),
        FOREIGN KEY(sender_id) REFERENCES users(id),
        FOREIGN KEY(recipient_id) REFERENCES users(id)
    )
    ''')
        
    conn.commit()
    conn.close()
