import sqlite3

def remove_private_key_encrypted():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Renombrar la tabla antigua
    cursor.execute('ALTER TABLE users RENAME TO users_old;')
    
    # Crear la nueva tabla sin la columna 'private_key_encrypted'
    cursor.execute('''
        CREATE TABLE users (
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
            public_key TEXT
        )
    ''')
    
    # Copiar los datos de la tabla antigua a la nueva
    cursor.execute('''
        INSERT INTO users (id, username, display_name, email, phone, password, profile_picture, status, is_verified, last_seen, public_key)
        SELECT id, username, display_name, email, phone, password, profile_picture, status, is_verified, last_seen, public_key
        FROM users_old;
    ''')
    
    # Eliminar la tabla antigua
    cursor.execute('DROP TABLE users_old;')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    remove_private_key_encrypted()
