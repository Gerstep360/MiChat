// chat.js

let socket;

let currentUserId;
function initializeChat() {
    checkSession();
    loadCurrentUserInfo();
    // Obtener el user_id del otro usuario del parámetro de la URL
    const urlParams = new URLSearchParams(window.location.search);
    const chatUserId = urlParams.get('user_id');
    if (!chatUserId) {
        alert('No se especificó un usuario para chatear.');
        window.location.href = '/chat_list';
        return;
    }

    // Obtener información del usuario con el que se está chateando
    fetch(`/get_user_info?user_id=${chatUserId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status) {
                document.getElementById('chat-with').innerText = `Chat con ${data.user.username}`;
                document.getElementById('chat-user-image').src = data.user.profile_picture;
                document.getElementById('chat-user-status').innerText = data.user.status || 'En línea';
                // Cargar mensajes anteriores
                loadMessages(chatUserId);
                // Configurar WebSocket para recibir mensajes en tiempo real
                setupWebSocket(chatUserId);
            } else {
                alert('No se pudo cargar el chat.');
                window.location.href = '/chat_list';
            }
        });

    // Manejar envío de mensajes
    const messageForm = document.getElementById('message-form');
    messageForm.addEventListener('submit', function(e) {
        e.preventDefault();
        sendMessage(chatUserId);
    });
}

// Verificar si el usuario está autenticado
function checkSession() {
    fetch('/check_session')
        .then(response => {
            if (response.status === 401) {
                window.location.href = '/login';
            }
        });
}

// Cargar información del usuario actual (opcional)
function loadCurrentUserInfo() {
    fetch('/get_current_user')
        .then(response => response.json())
        .then(data => {
            if (data.status) {
                currentUserId = data.user.id;
                // ... resto del código ...
            } else {
                console.error('No se pudo cargar la información del usuario.');
            }
        });
}

// Función para cargar mensajes anteriores
function loadMessages(chatUserId) {
    fetch(`/get_messages?user_id=${chatUserId}`)
        .then(response => response.json())
        .then(data => {
            const chatWindow = document.getElementById('chat-window');
            chatWindow.innerHTML = ''; // Limpiar el chat
            if (data.messages.length === 0) {
                const noMessages = document.createElement('p');
                noMessages.innerText = 'No hay mensajes en este chat. ¡Inicia la conversación!';
                chatWindow.appendChild(noMessages);
            } else {
                data.messages.forEach(msg => {
                    const messageBubble = document.createElement('div');
                    messageBubble.className = msg.sender === 'me' ? 'message-bubble me' : 'message-bubble';
                    messageBubble.innerText = msg.content;
                    chatWindow.appendChild(messageBubble);
                });
                // Desplazar hacia abajo
                chatWindow.scrollTop = chatWindow.scrollHeight;
            }
        });
}


// Enviar mensaje a través de Socket.IO
function sendMessage(chatUserId) {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    if (message !== '') {
        socket.emit('send_message', {
            room: `chat_${chatUserId}`,
            message: message,
            recipient_id: chatUserId
        });
        messageInput.value = '';
    }
}

// Configurar WebSocket para recibir y enviar mensajes
function setupWebSocket(chatUserId) {
    if (!socket) {
        socket = io();
        // Manejar recepción de mensajes
        socket.on('receive_message', function(data) {
            const chatMessages = document.getElementById('chat-messages');
            const messageBubble = document.createElement('div');

            if (data.sender_id === currentUserId) {
                // Es el mensaje que envió el usuario actual
                messageBubble.className = 'message-bubble me';
            } else if (data.sender_id === chatUserId) {
                // Es un mensaje del otro usuario en el chat
                messageBubble.className = 'message-bubble other';
                // Mostrar notificación si la ventana no está enfocada
                if (!document.hasFocus()) {
                    showNotification(data.sender_username, data.message, chatUserId, data.sender_profile_picture);
                }
            } else {
                // Mensaje de otro usuario en otro chat
                return;
            }

            messageBubble.innerText = data.message;
            chatMessages.appendChild(messageBubble);
            // Desplazar hacia abajo
            chatMessages.scrollTop = chatMessages.scrollHeight;
        });
    }
    // Unirse a una sala específica para el chat
    socket.emit('join', { room: `chat_${chatUserId}` });
}

// Mostrar notificación de nuevo mensaje
function showNotification(title, message, senderId, profilePicture) {
    if (Notification.permission === 'granted') {
        const notification = new Notification(title, {
            body: message,
            icon: profilePicture || '/static/img/default_profile.png'
        });
        notification.onclick = function() {
            window.focus();
            window.location.href = `/chat?user_id=${senderId}`;
        };
    }
}
function formatTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}
// Ejecutar la inicialización al cargar la página
window.onload = initializeChat;
