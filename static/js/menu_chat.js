// menu_chat.js

let socket;
let currentUserId;
let currentChatUserId;
let typingStatusTimeout;
let currentChatRoom;

function initializeApp() {
    checkSession();
    loadCurrentUserInfo();
    loadChatList();

    // Solicitar permiso de notificaciones
    if (Notification.permission !== 'granted' && Notification.permission !== 'denied') {
        Notification.requestPermission();
    }
}

// Verificar si el usuario está autenticado
function checkSession(redirectIfAuthenticated = false) {
    fetch('/check_session')
        .then(response => {
            if (response.status === 401) {
                if (window.location.pathname !== '/login') {
                    window.location.href = '/login';
                }
            } else {
                if (redirectIfAuthenticated && window.location.pathname !== '/chat_list') {
                    window.location.href = '/chat_list';
                }
            }
        });
}

// Cargar información del usuario actual
function loadCurrentUserInfo() {
    fetch('/get_current_user')
        .then(response => response.json())
        .then(data => {
            if (data.status) {
                currentUserId = data.user.id;
                const profilePicture = document.getElementById('my-profile-picture');
                profilePicture.src = data.user.profile_picture;
                // Actualizar imagen en el modal
                const profileModalImage = document.getElementById('profile-modal-image');
                profileModalImage.src = data.user.profile_picture;

                // Configurar WebSocket después de obtener el ID del usuario
                setupWebSocket();
            } else {
                console.error('No se pudo cargar la información del usuario.');
            }
        });
}

// Función para cargar la lista de chats
function loadChatList() {
    fetch('/get_chats')
        .then(response => response.json())
        .then(data => {
            const chatList = document.getElementById('chat-list');
            chatList.innerHTML = ''; // Limpiar la lista
            if (data.chats.length === 0) {
                const noChatsMessage = document.createElement('p');
                noChatsMessage.innerText = 'No hay chats. Agrega uno para poder interactuar.';
                chatList.appendChild(noChatsMessage);
            } else {
                data.chats.forEach(chat => {
                    const chatCard = document.createElement('div');
                    chatCard.className = 'chat-card';
                    chatCard.setAttribute('data-chat-id', chat.chat_id);
                    chatCard.innerHTML = `
                        <img src="${chat.profile_picture}" alt="${chat.username}">
                        <div class="chat-info">
                            <h4>${chat.username}</h4>
                            <p>${chat.last_message}</p>
                        </div>
                    `;
                    chatCard.addEventListener('click', function() {
                        // Cargar el chat en el panel derecho
                        loadChatWindow(chat.user_id);
                    });
                    chatList.appendChild(chatCard);
                });
            }
        })
        .catch(error => {
            console.error('Error al cargar la lista de chats:', error);
        });
}

// Función para cargar la ventana de chat
function loadChatWindow(chatUserId) {
    currentChatUserId = chatUserId;

    // Mostrar la ventana de chat y ocultar el mensaje de bienvenida
    document.getElementById('chat-window').style.display = 'flex';
    document.getElementById('welcome-message').style.display = 'none';

    // Obtener el chat_id
    fetch(`/get_chat_id?user_id=${chatUserId}`)
        .then(response => response.json())
        .then(data => {
            if (data.chat_id) {
                currentChatRoom = data.chat_id; // Usar chat_id como nombre de la sala
                // Unirse a la sala del chat
                socket.emit('join', { room: `chat_${currentChatRoom}` });
                // Cargar mensajes
                loadMessages();
            } else {
                alert('No se pudo obtener el chat.');
            }
        });

    // Obtener información del usuario
    fetch(`/get_user_info?user_id=${chatUserId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status) {
                document.getElementById('chat-with').innerText = `${data.user.username}`;
                document.getElementById('chat-user-image').src = data.user.profile_picture;
                document.getElementById('chat-user-modal-image').src = data.user.profile_picture;

                // Mostrar estado en línea o última vez visto
                updateUserStatus(data.user.status, data.user.last_seen);
            } else {
                alert('No se pudo cargar el chat.');
            }
        });

    // Manejar envío de mensajes
    const messageForm = document.getElementById('message-form');
    messageForm.onsubmit = function(e) {
        e.preventDefault();
        sendMessage();
    };

    // Manejar evento de input para detectar cuando el usuario está escribiendo
    const messageInput = document.getElementById('message-input');
    messageInput.oninput = function() {
        socket.emit('typing', { recipient_id: currentChatUserId });
    };
}

// Función para cargar mensajes anteriores
function loadMessages() {
    fetch(`/get_messages?chat_id=${currentChatRoom}`)
        .then(response => response.json())
        .then(data => {
            const chatMessages = document.getElementById('chat-messages');
            chatMessages.innerHTML = ''; // Limpiar el chat
            if (data.messages.length === 0) {
                const noMessages = document.createElement('p');
                noMessages.innerText = 'No hay mensajes en este chat. ¡Inicia la conversación!';
                chatMessages.appendChild(noMessages);
            } else {
                data.messages.forEach(msg => {
                    displayMessage(msg);
                });
                // Desplazar hacia abajo
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        });
}

// Enviar mensaje a través de Socket.IO
function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    if (message !== '') {
        socket.emit('send_message', {
            room: `chat_${currentChatRoom}`,
            message: message,
            recipient_id: currentChatUserId
        });
        messageInput.value = '';
    }
}

// Configurar WebSocket para recibir y enviar mensajes
function setupWebSocket() {
    if (!socket) {
        socket = io();

        socket.on('connect', () => {
            // Unirse a la sala personal del usuario
            socket.emit('join_personal', { user_id: currentUserId });
        });

        // Manejar recepción de mensajes
        socket.on('receive_message', function(data) {
            if (data.chat_id == currentChatRoom) {
                displayMessage(data);
            } else {
                // Mostrar notificación o indicador de nuevo mensaje en la lista de chats
                showNotification(data.sender_username, data.message || data.content, data.sender_id, data.sender_profile_picture);
                // Recargar la lista de chats para mostrar el nuevo chat
                loadChatList();
            }
            updateChatListWithNewMessage(data.chat_id, data.message || data.content);
        });

        // Manejar evento de "escribiendo..."
        socket.on('user_typing', function(data) {
            if (data.sender_id === currentChatUserId) {
                showTypingStatus();
            }
        });

        // Manejar actualización de estado
        socket.on('user_status_update', function(data) {
            if (data.user_id === currentChatUserId) {
                updateUserStatus(data.status, data.last_seen);
            }
        });

        // Manejar actualización de la lista de chats
        socket.on('update_chat_list', function() {
            loadChatList();
        });
    } else {
        // Dejar la sala anterior
        socket.emit('leave_room', { room: `chat_${currentChatRoom}` });
        // Unirse a la nueva sala
        socket.emit('join', { room: `chat_${currentChatRoom}` });
    }
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
            // Cargar el chat correspondiente
            loadChatWindow(senderId);
        };
    }
}

// Mostrar mensaje en la ventana de chat
function displayMessage(data) {
    const chatMessages = document.getElementById('chat-messages');
    const messageBubble = document.createElement('div');
    messageBubble.classList.add('message-bubble');

    const messageContent = document.createElement('div');
    messageContent.classList.add('message-content');
    messageContent.innerText = data.message || data.content; // Manejar mensajes cargados y nuevos

    if (data.sender_id === currentUserId) {
        messageBubble.classList.add('me');
    } else {
        messageBubble.classList.add('other');
    }

    // Añadir el nombre de usuario y la imagen de perfil
    const senderInfo = document.createElement('div');
    senderInfo.classList.add('sender-info');

    const senderName = document.createElement('span');
    senderName.classList.add('sender-name');
    senderName.innerText = data.sender_username;

    const senderImage = document.createElement('img');
    senderImage.classList.add('sender-image');
    senderImage.src = data.sender_profile_picture;

    senderInfo.appendChild(senderImage);
    senderInfo.appendChild(senderName);

    messageBubble.appendChild(senderInfo);
    messageBubble.appendChild(messageContent);
    chatMessages.appendChild(messageBubble);

    // Desplazar hacia abajo
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Mostrar estado de "escribiendo..."
function showTypingStatus() {
    const statusElement = document.getElementById('chat-user-status');
    statusElement.innerText = 'Escribiendo...';
    // Ocultar el estado después de un tiempo
    clearTimeout(typingStatusTimeout);
    typingStatusTimeout = setTimeout(() => {
        updateUserStatus('online'); // Asumiendo que el usuario sigue en línea
    }, 2000);
}

// Actualizar el estado del usuario (en línea, offline)
function updateUserStatus(status, lastSeen = null) {
    const statusElement = document.getElementById('chat-user-status');
    if (status === 'online') {
        statusElement.innerText = 'En línea';
    } else if (status === 'offline' && lastSeen) {
        statusElement.innerText = `Últ. vez ${formatDate(lastSeen)}`;
    } else {
        statusElement.innerText = '';
    }
}

// Actualizar la lista de chats con el nuevo mensaje
function updateChatListWithNewMessage(chatId, lastMessage) {
    const chatCards = document.getElementsByClassName('chat-card');
    let chatCardFound = false;

    Array.from(chatCards).forEach(card => {
        const cardChatId = card.getAttribute('data-chat-id');
        if (cardChatId == chatId) {
            const lastMessageElement = card.querySelector('.chat-info p');
            lastMessageElement.innerText = lastMessage;
            chatCardFound = true;
        }
    });

    if (!chatCardFound) {
        // Si no se encontró la tarjeta, recargar la lista de chats
        loadChatList();
    }
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

// Abrir el modal para iniciar un nuevo chat y cargar la lista de usuarios
function openNewChatModal() {
    document.getElementById('new-chat-modal').style.display = 'block';
    loadUserList();
}

// Cerrar el modal de nuevo chat
function closeNewChatModal() {
    document.getElementById('new-chat-modal').style.display = 'none';
}

// Cargar la lista de usuarios
function loadUserList() {
    fetch('/get_users')
        .then(response => response.json())
        .then(data => {
            const userList = document.getElementById('user-list');
            userList.innerHTML = ''; // Limpiar la lista
            if (data.users.length === 0) {
                const noUsersMessage = document.createElement('p');
                noUsersMessage.innerText = 'No hay usuarios registrados aparte de ti.';
                userList.appendChild(noUsersMessage);
            } else {
                data.users.forEach(user => {
                    const userCard = document.createElement('div');
                    userCard.className = 'user-card';
                    userCard.innerHTML = `
                        <img src="${user.profile_picture}" alt="${user.username}">
                        <div class="user-info">
                            <h4>${user.username}</h4>
                        </div>
                    `;
                    userCard.addEventListener('click', function() {
                        startChatWithUser(user.username);
                    });
                    userList.appendChild(userCard);
                });
            }
        });
}

// Iniciar chat con un usuario seleccionado
function startChatWithUser(username) {
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
}

// Búsqueda de usuarios en el modal
function searchUsers() {
    const input = document.getElementById('search-users-input').value.toLowerCase();
    const userCards = document.getElementsByClassName('user-card');
    Array.from(userCards).forEach(card => {
        const username = card.querySelector('.user-info h4').innerText.toLowerCase();
        if (username.includes(input)) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

// Formatear fecha y hora
function formatDate(dateString) {
    const date = new Date(dateString);
    const options = { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' };
    return date.toLocaleDateString('es-ES', options);
}

// Funciones para el modal de perfil


function closeProfileModal() {
    const modal = document.getElementById('profile-modal');
    modal.classList.add('closing'); // Añadir clase de animación de cierre

    // Esperar a que termine la animación antes de ocultarlo
    setTimeout(() => {
        modal.classList.remove('closing', 'show');
        modal.style.display = 'none';
    }, 500); // Tiempo coincide con la duración de la animación en CSS
}

function openProfileModal() {
    const modal = document.getElementById('profile-modal');
    modal.style.display = 'block';
    modal.classList.add('show'); // Activar clase para mostrar el modal
}

// Funciones para el modal de perfil del usuario del chat
function openChatUserProfileModal() {
    document.getElementById('chat-user-profile-modal').style.display = 'block';
}

function closeChatUserProfileModal() {
    document.getElementById('chat-user-profile-modal').style.display = 'none';
}

// Ejecutar la inicialización al cargar la página
window.onload = initializeApp;
function toggleSettingsMenu() {
    const settingsMenu = document.getElementById('settings-menu');
    if (settingsMenu.style.display === 'block') {
        settingsMenu.style.display = 'none';
    } else {
        settingsMenu.style.display = 'block';
    }
}

// Cerrar el menú si el usuario hace clic fuera de él
window.onclick = function(event) {
    if (!event.target.matches('.settings-button')) {
        const settingsMenu = document.getElementById('settings-menu');
        if (settingsMenu && settingsMenu.style.display === 'block') {
            settingsMenu.style.display = 'none';
        }
    }
}

function logout() {
    fetch('/logout', {
        method: 'GET'
    }).then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        }
    });
}

function deleteProfilePicture() {
    fetch('/delete_profile_picture', {
        method: 'POST'
    }).then(response => response.json())
      .then(data => {
          if (data.status === 'success') {
              const timestamp = new Date().getTime();
              document.getElementById('my-profile-picture').src = data.profile_picture + '?t=' + timestamp;
              document.getElementById('profile-modal-image').src = data.profile_picture + '?t=' + timestamp;
          } else {
              alert('Error al eliminar la foto de perfil.');
          }
      });
}

function changeProfilePicture() {
    // Crear un input de tipo file oculto
    const inputFile = document.createElement('input');
    inputFile.type = 'file';
    inputFile.accept = 'image/*';
    inputFile.onchange = function() {
        const file = inputFile.files[0];
        if (file) {
            // Validar el tamaño del archivo (opcional)
            const maxSize = 5 * 1024 * 1024; // 5 MB
            if (file.size > maxSize) {
                alert('El archivo es demasiado grande. Tamaño máximo: 5 MB.');
                return;
            }
            // Enviar el archivo al servidor para actualizar la foto de perfil
            const formData = new FormData();
            formData.append('profile_picture', file);
            fetch('/change_profile_picture', {
                method: 'POST',
                body: formData
            }).then(response => response.json())
              .then(data => {
                  if (data.status === 'success') {
                      const timestamp = new Date().getTime();
                      document.getElementById('my-profile-picture').src = data.profile_picture + '?t=' + timestamp;
                      document.getElementById('profile-modal-image').src = data.profile_picture + '?t=' + timestamp;
                  } else {
                      alert('Error al cambiar la foto de perfil.');
                  }
              });
        }
    };
    // Simular clic en el input file
    inputFile.click();
}
document.querySelector('.settings-button').addEventListener('click', function () {
    const dropdown = this.closest('.settings-dropdown');
    dropdown.classList.toggle('active'); // Alternar la clase 'active'
});
