
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
7. [Implementación de E2EE](#implementación-de-e2ee)
8. [Contribuciones](#contribuciones)
9. [Licencia](#licencia)

---

## Características

- **Registro y Autenticación de Usuarios**: Permite a los usuarios registrarse y autenticarse de manera segura.
- **Verificación de Correo Electrónico**: Envía un código de verificación al correo electrónico del usuario para confirmar su cuenta.
- **Gestión de Perfiles**: Los usuarios pueden subir y actualizar su foto de perfil.
- **Lista de Chats**: Muestra una lista de conversaciones existentes con otros usuarios.
- **Mensajería en Tiempo Real**: Utiliza Socket.IO para la comunicación en tiempo real entre los usuarios.
- **Notificaciones**: Informa a los usuarios sobre nuevos mensajes mediante notificaciones del navegador.
- **Cifrado de Extremo a Extremo (E2EE)**: Planeado para asegurar que solo los participantes en una conversación puedan leer los mensajes.

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

### 2. Crear un Entorno Virtual

Es recomendable utilizar un entorno virtual para gestionar las dependencias del proyecto y evitar conflictos con otras instalaciones de Python en tu sistema.

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar Dependencias

Asegúrate de que el archivo requirements.txt contiene todas las dependencias necesarias.

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

**Nota Importante**: Es fundamental que no compartas tu archivo `.env` públicamente, ya que contiene información sensible.

### 5. Inicializar la Base de Datos

Ejecuta el siguiente comando en la terminal para crear las tablas necesarias en la base de datos:

```bash
python
>>> from database import init_db
>>> init_db()
>>> exit()
```

### 6. Ejecutar la Aplicación

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
├── e2ee.py
├── server.py
├── database.py
├── email_verification.py
├── requirements.txt
├── .env
├── static/
│   ├── css/
│   │   └── styles.css
│   ├── js/
│   │   └── menu_chat.js
│   ├── img/
│   │   ├── none.jpg
│   │   └── notification_icon.png
│   └── uploads/
├── templates/
│   ├── register.html
│   ├── verify.html
│   ├── login.html
│   └── chat_list.html
└── README.md
```

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
