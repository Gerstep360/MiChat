// main.js


// Inicializar la aplicación
function initializeApp() {
    checkSession();
    loadChatList();
    // Solicitar permiso de notificaciones
    if (Notification.permission !== 'granted' && Notification.permission !== 'denied') {
        Notification.requestPermission();
    }
}
// Verificar si el usuario está autenticado y redirigir
function checkSession() {
    fetch('/check_session')
        .then(response => {
            if (response.status === 200) {
                // Usuario autenticado, redirigir a la lista de chats
                window.location.href = '/chat_list';
            }
        });
}


// Registro de usuario
if (document.getElementById('register-form')) {
    document.getElementById('register-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(document.getElementById('register-form'));
        fetch('/register', {
            method: 'POST',
            body: formData
        }).then(response => response.json())
          .then(data => {
              alert(data.status || data.error);
              if (data.status) {
                  window.location.href = '/verify';
              }
          });
    });
}

// Verificación de código
if (document.getElementById('verify-form')) {
    document.getElementById('verify-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const data = {
            code: document.getElementById('code').value
        };
        fetch('/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }).then(response => response.json())
          .then(data => {
              alert(data.status || data.error);
              if (data.status) {
                  window.location.href = '/chat_list';
              }
          });
    });
}

// Login de usuario
if (document.getElementById('login-form')) {
    document.getElementById('login-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const data = {
            email_or_phone: document.getElementById('email_or_phone').value,
            password: document.getElementById('password').value
        };
        fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }).then(response => response.json())
          .then(data => {
              alert(data.status || data.error);
              if (data.status) {
                  window.location.href = '/chat_list';
              }
          });
    });
}

// Cargar lista de chats al entrar en chat_list.html
function loadChatList() {
    // Verificar si el usuario está autenticado
    fetch('/check_session')
        .then(response => {
            if (response.status === 401) {
                window.location.href = '/login';
            } else {
                // Obtener la lista de chats del servidor
                fetch('/get_chats')
                    .then(response => response.json())
                    .then(data => {
                        const chatList = document.getElementById('chat-list');
                        chatList.innerHTML = ''; // Limpiar la lista
                        data.chats.forEach(chat => {
                            const chatCard = document.createElement('div');
                            chatCard.className = 'chat-card';
                            chatCard.innerHTML = `
                                <img src="${chat.profile_picture}" alt="${chat.username}" width="60" height="60">
                                <div class="chat-info">
                                    <h4>${chat.username}</h4>
                                    <p>${chat.last_message}</p>
                                </div>
                            `;
                            chatCard.addEventListener('click', function() {
                                // Redirigir al chat con este usuario
                                window.location.href = `/chat?user_id=${chat.user_id}`;
                            });
                            chatList.appendChild(chatCard);
                        });
                    });
            }
        });
}

// Abrir el modal para iniciar un nuevo chat
function openNewChatModal() {
    document.getElementById('new-chat-modal').style.display = 'block';
}

// Cerrar el modal de nuevo chat
function closeNewChatModal() {
    document.getElementById('new-chat-modal').style.display = 'none';
}

// Enviar solicitud para iniciar un nuevo chat
if (document.getElementById('new-chat-form')) {
    document.getElementById('new-chat-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const username = document.getElementById('new-chat-username').value;
        fetch('/start_chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: username })
        }).then(response => response.json())
          .then(data => {
              if (data.status) {
                  closeNewChatModal();
                  loadChatList();
              } else {
                  alert(data.error);
              }
          });
    });
}

// Inicializar el chat individual en chat.html
function initializeChat() {
    // Verificar si el usuario está autenticado
    fetch('/check_session')
        .then(response => {
            if (response.status === 401) {
                window.location.href = '/login';
            } else {
                const urlParams = new URLSearchParams(window.location.search);
                const chatUserId = urlParams.get('user_id');
                // Obtener información del usuario con el que se está chateando
                fetch(`/get_user_info?user_id=${chatUserId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.status) {
                            document.getElementById('chat-with').innerText = `Chat con ${data.user.username}`;
                            document.getElementById('chat-user-image').src = data.user.profile_picture;
                            document.getElementById('chat-user-status').innerText = data.user.status;
                            // Cargar mensajes anteriores
                            loadMessages(chatUserId);
                            // Configurar WebSocket para recibir mensajes en tiempo real
                            setupWebSocket(chatUserId);
                        } else {
                            alert('No se pudo cargar el chat.');
                            window.location.href = '/chat_list';
                        }
                    });
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
            data.messages.forEach(msg => {
                const messageBubble = document.createElement('div');
                messageBubble.className = msg.sender === 'me' ? 'message-bubble me' : 'message-bubble';
                messageBubble.innerText = msg.content; // En una implementación real, descifrar el mensaje
                chatWindow.appendChild(messageBubble);
            });
            // Desplazar hacia abajo
            chatWindow.scrollTop = chatWindow.scrollHeight;
        });
}

// Enviar mensaje
if (document.getElementById('message-form')) {
    document.getElementById('message-form').addEventListener('submit', function(e) {
        e.preventDefault();
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();
        if (message !== '') {
            const urlParams = new URLSearchParams(window.location.search);
            const chatUserId = urlParams.get('user_id');
            // Enviar mensaje al servidor
            fetch('/send_message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ recipient_id: chatUserId, message: message })
            }).then(response => response.json())
              .then(data => {
                  if (data.status) {
                      // Mostrar el mensaje en el chat
                      const chatWindow = document.getElementById('chat-window');
                      const messageBubble = document.createElement('div');
                      messageBubble.className = 'message-bubble me';
                      messageBubble.innerText = message;
                      chatWindow.appendChild(messageBubble);
                      messageInput.value = '';
                      // Desplazar hacia abajo
                      chatWindow.scrollTop = chatWindow.scrollHeight;
                  } else {
                      alert('No se pudo enviar el mensaje.');
                  }
              });
        }
    });
}

// Configurar WebSocket para recibir mensajes en tiempo real
let socket;
function setupWebSocket(chatUserId) {
    socket = new WebSocket(`ws://${window.location.host}/ws?user_id=${chatUserId}`);
    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.type === 'message') {
            // Mostrar el mensaje recibido
            const chatWindow = document.getElementById('chat-window');
            const messageBubble = document.createElement('div');
            messageBubble.className = 'message-bubble';
            messageBubble.innerText = data.message;
            chatWindow.appendChild(messageBubble);
            // Desplazar hacia abajo
            chatWindow.scrollTop = chatWindow.scrollHeight;
            // Mostrar notificación
            showNotification(data.sender_username, data.message, data.sender_id);
        }
    };
}

// Mostrar notificación de nuevo mensaje
function showNotification(title, message, senderId) {
    if (Notification.permission === 'granted') {
        const notification = new Notification(title, {
            body: message,
            icon: '/static/img/notification_icon.png'
        });
        notification.onclick = function() {
            window.focus();
            window.location.href = `/chat?user_id=${senderId}`;
        };
    } else if (Notification.permission !== 'denied') {
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                showNotification(title, message, senderId);
            }
        });
    }
}

// Solicitar permiso de notificaciones al cargar la aplicación
if (Notification.permission !== 'granted' && Notification.permission !== 'denied') {
    Notification.requestPermission();
}

// Búsqueda de chats
function searchChats() {
    const input = document.getElementById('search-input').value.toLowerCase();
    const chatCards = document.getElementsByClassName('chat-card');
    Array.from(chatCards).forEach(card => {
        const username = card.querySelector('.chat-info h4').innerText.toLowerCase();
        if (username.includes(input)) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}
