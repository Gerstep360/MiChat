
# MiChat

Bienvenido a **MiChat**, una aplicación de chat desarrollada con Flask que implementa características modernas para una comunicación segura y eficiente entre usuarios. Este proyecto está diseñado para proporcionar una experiencia de chat en tiempo real con funcionalidades de cifrado de extremo a extremo (E2EE), asegurando que solo los participantes en la conversación puedan leer los mensajes intercambiados.

---

## Tabla de Contenidos

1. [Características](#características)
2. [Tecnologías Utilizadas](#tecnologías-utilizadas)
3. [Instalación](#instalación)
4. [Configuración](#configuración)
5. [Uso](#uso)
6. [Estructura del Proyecto](#estructura-del-proyecto)
7. [Scripts Adicionales](#scripts-adicionales)
8. [Implementación de E2EE](#implementación-de-e2ee)
9. [Contribuciones](#contribuciones)
10. [Licencia](#licencia)

---

## Características

- **Registro y Autenticación de Usuarios**: Permite a los usuarios registrarse y autenticarse de manera segura.
- **Verificación de Correo Electrónico**: Envía un código de verificación al correo electrónico del usuario para confirmar su cuenta.
- **Gestión de Perfiles**: Los usuarios pueden subir y actualizar su foto de perfil.
- **Lista de Chats**: Muestra una lista de conversaciones existentes con otros usuarios.
- **Mensajería en Tiempo Real**: Utiliza Socket.IO para la comunicación en tiempo real entre los usuarios.
- **Notificaciones**: Informa a los usuarios sobre nuevos mensajes mediante notificaciones del navegador.
- **Cifrado de Extremo a Extremo (E2EE)**: Planeado para asegurar que solo los participantes en una conversación puedan leer los mensajes.
- **Gestión de Usuarios de Prueba**: Incluye un script para generar usuarios de prueba en la base de datos.
- **Limpieza de Datos y Reinicio**: Scripts para eliminar datos temporales y vaciar la base de datos.

---

## Tecnologías Utilizadas

### Backend:
- Python
- Flask
- Flask-SocketIO
- SQLite
- Werkzeug
- Crypto

### Frontend:
- HTML5
- CSS3
- JavaScript
- TweetNaCl.js (Planeado para E2EE)

### Otros:
- Flask-Session
- smtplib (Para envío de correos de verificación)

---

## Instalación

Sigue estos pasos para configurar y ejecutar la aplicación en tu entorno local.

### 1. Clonar el Repositorio

```bash
git clone https://github.com/tu_usuario/mi-chat.git
cd mi-chat
```

### 2. Crear un Entorno Virtual (Opcional)

Puedes usar un entorno virtual para gestionar las dependencias y evitar conflictos con otras instalaciones de Python. Esto es opcional:

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```
### 4. Configurar Variables de Entorno 

Crea un archivo `.env` en la raíz del proyecto y añade las siguientes variables (ajusta los valores según tu configuración):

```env
# Configuración del servidor de correo
EMAIL_USER=ejemplo@gmail.com
EMAIL_PASSWORD=tu_contraseña_de_aplicación

# Clave secreta de Flask
SECRET_KEY=tu_secret_key_api
```
`

Si no tienes una clave secreta para Flask, usa el script `secret.py` para generarla automáticamente:

```bash
python -c "import os; print(os.urandom(24).hex())"
```

Pega la clave generada en el archivo `.env` como `SECRET_KEY`.

**Nota Importante**: Es fundamental que no compartas tu archivo `.env` públicamente, ya que contiene información sensible.

### 5. Inicializar la Base de Datos

Ejecuta el siguiente comando en la terminal para crear las tablas necesarias en la base de datos:

```bash
python
>>> from database import init_db
>>> init_db()
>>> exit()
```

### 6. Generar Usuarios de Prueba (Opcional)

Ejecuta el script `crear_usuarios.py` para generar usuarios de prueba en la base de datos:

```bash
python crear_usuarios.py
```

Esto también creará un archivo `usuarios.txt` con las credenciales generadas.

### 7. Ejecutar la Aplicación

Inicia el servidor Flask ejecutando:

```bash
python server.py
```

La aplicación estará disponible en [http://127.0.0.1:5000/](http://127.0.0.1:5000/).

---

## Configuración

### Configuración del Servidor de Correo

Para que la verificación de correo electrónico funcione correctamente, sigue estos pasos para crear una contraseña de aplicación de Google:

1. **Habilitar la Verificación en Dos Pasos** (Opcional pero Recomendado):
   - Ve a [Tu cuenta de Google](https://myaccount.google.com/security).
   - En la sección "Iniciar sesión en Google", selecciona "Verificación en dos pasos" y sigue las instrucciones para configurarla.

2. **Crear una Contraseña de Aplicación**:
   - Accede al [Panel de Contraseñas de Aplicación](https://myaccount.google.com/apppasswords).
   - Selecciona "Otro (Nombre personalizado)".
   - Escribe un nombre descriptivo, por ejemplo, "MiChat", y haz clic en "Generar".
   - Copia la contraseña generada y úsala como `EMAIL_PASSWORD` en tu archivo `.env`.

Ejemplo de `.env` después de crear la contraseña de aplicación:

```env
# Configuración del servidor de correo
EMAIL_USER=ejemplo@gmail.com
EMAIL_PASSWORD=abcd1234efgh5678

# Clave secreta de Flask
SECRET_KEY=tu_secret_key_api
```

---

## Estructura del Proyecto

```
mi-chat/
├── crear_usuarios.py           # Script para generar usuarios de prueba
├── resetear_datos.py           # Script para limpiar datos y vaciar la base de datos
├── e2ee.py                     # Archivo planeado para implementar E2EE
├── secret.py                   # Script para generar claves secretas para Flask
├── server.py                   # Servidor Flask principal
├── database.py                 # Conexión y gestión de la base de datos
├── email_verification.py       # Envío de correos de verificación
├── requirements.txt            # Dependencias del proyecto
├── .env                        # Variables de entorno
├── static/
│   ├── css/
│   │   └── styles.css          # Estilos CSS
│   ├── js/
│   │   └── menu_chat.js        # Lógica del menú de chat
│   ├── img/
│   │   ├── none.jpg            # Imagen predeterminada para perfiles
│   │   └── notification_icon.png # Icono para notificaciones
│   └── uploads/                # Carpeta para subir archivos
├── templates/
│   ├── register.html           # Registro de usuarios
│   ├── verify.html             # Verificación de usuarios
│   ├── login.html              # Inicio de sesión
│   └── chat_list.html          # Lista de chats
└── README.md                   # Este archivo
```

---

## Scripts Adicionales

### **crear_usuarios.py**
Este script genera usuarios ficticios para pruebas en la base de datos, con datos realistas y contraseñas encriptadas. Además, genera un archivo `usuarios.txt` con las credenciales generadas.

### **resetear_datos.py**
Permite limpiar el entorno de desarrollo eliminando:
- Archivos temporales (`flask_session`, `__pycache__`, etc.).
- La base de datos.
- El archivo `usuarios.txt`.

También incluye la función `vaciar_base_de_datos()` para eliminar los datos de todas las tablas de la base de datos sin borrar el archivo.

### **secret.py**
Genera una clave secreta aleatoria para ser utilizada como `SECRET_KEY` en Flask.

---
## Implementación de E2EE

Actualmente, MiChat está en proceso de implementación del Cifrado de Extremo a Extremo (E2EE). Este mecanismo asegurará que los mensajes sean cifrados en el frontend antes de ser enviados al servidor y almacenados en la base de datos de forma cifrada.

---

## Contribuciones

¡Las contribuciones son bienvenidas! Si deseas mejorar este proyecto, sigue estos pasos:

1. Haz un fork del repositorio.
2. Crea una nueva rama: `git checkout -b feature/nueva-funcionalidad`.
3. Realiza tus cambios: `git commit -m 'Añadir nueva funcionalidad'`.
4. Haz push a la rama: `git push origin feature/nueva-funcionalidad`.
5. Abre un Pull Request.

---

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Para más detalles, consulta el archivo LICENSE.
