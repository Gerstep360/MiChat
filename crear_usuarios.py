import sqlite3
from werkzeug.security import generate_password_hash
import random
import string

# Función para obtener la conexión a la base de datos
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Datos de ejemplo para los usuarios
nombres = [
    "Carlos", "Ana", "Luis", "Sofía", "Juan", "Marta", "Pedro", "Lucía",
    "Jorge", "Elena", "Ricardo", "Gabriela", "Fernando", "Laura", "Alberto",
    "Camila", "Daniel", "Paula", "Sergio", "Valeria"
]

apellidos = [
    "Gómez", "Pérez", "López", "Martínez", "Rodríguez", "García", "Fernández",
    "Hernández", "Ruiz", "Díaz", "Vargas", "Morales", "Torres", "Ramírez",
    "Cruz", "Castro", "Jiménez", "Sánchez", "Gutiérrez", "Rojas"
]

# Generar usuarios con datos realistas
def generar_usuarios():
    usuarios = []
    for i in range(20):
        nombre = random.choice(nombres)
        apellido = random.choice(apellidos)
        username = f"{nombre.lower()}.{apellido.lower()}{random.randint(1, 99)}"
        email = f"{username}@example.com"
        telefono = f"+591{random.randint(60000000, 79999999)}"
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        usuarios.append({
            "username": username,
            "display_name": f"{nombre} {apellido}",
            "email": email,
            "phone": telefono,
            "password": password  # Contraseña en texto plano para escribirla al archivo
        })
    return usuarios

# Guardar usuarios en la base de datos
def guardar_usuarios(usuarios):
    conn = get_db_connection()
    cursor = conn.cursor()
    with open('usuarios.txt', 'w', encoding='utf-8') as file:  # Usar UTF-8 explícitamente
        file.write("Usuarios generados (contraseñas en texto plano):\n")
        file.write("-" * 50 + "\n")
        for usuario in usuarios:
            # Encriptar la contraseña
            hashed_password = generate_password_hash(usuario['password'])
            # Insertar en la base de datos
            cursor.execute('''
                INSERT INTO users (username, display_name, email, phone, password, profile_picture, status, is_verified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                usuario['username'], usuario['display_name'], usuario['email'],
                usuario['phone'], hashed_password, '/static/img/none.jpg', 'active', 1
            ))
            # Escribir usuario y contraseña en el archivo
            file.write(f"Usuario: {usuario['username']}\n")
            file.write(f"Email: {usuario['email']}\n")
            file.write(f"Teléfono: {usuario['phone']}\n")
            file.write(f"Contraseña: {usuario['password']}\n")
            file.write("-" * 50 + "\n")
    conn.commit()
    conn.close()

# Main
if __name__ == "__main__":
    usuarios = generar_usuarios()
    guardar_usuarios(usuarios)
    print("Usuarios generados y guardados en la base de datos. Revisa el archivo 'usuarios.txt'.")
