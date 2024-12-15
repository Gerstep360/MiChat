// Configuración de Elliptic.js
const EC = new elliptic.ec('curve25519');

// Crear el objeto global `CryptoModule`
const CryptoModule = (() => {
    // Generar claves del remitente
    function generateSenderKeys() {
        const senderKeyPair = EC.genKeyPair();
        return {
            privateKey: senderKeyPair.getPrivate('hex'), // Clave privada del remitente
            publicKey: senderKeyPair.getPublic('hex'),  // Clave pública del remitente
        };
    }

    // Generar claves del destinatario
    function generateRecipientKeys() {
        const recipientKeyPair = EC.genKeyPair();
        return {
            privateKey: recipientKeyPair.getPrivate('hex'), // Clave privada del destinatario
            publicKey: recipientKeyPair.getPublic('hex'),   // Clave pública del destinatario
        };
    }

    // Derivar clave compartida
    function deriveSharedKey(privateKey, publicKey) {
        const privateKeyObject = EC.keyFromPrivate(privateKey, 'hex');
        const publicKeyObject = EC.keyFromPublic(publicKey, 'hex');
        return privateKeyObject.derive(publicKeyObject.getPublic()).toString(16); // Clave compartida
    }

    // Función para cifrar un mensaje
    function encryptMessage(message, sharedKey) {
        return CryptoJS.AES.encrypt(message, sharedKey).toString();
    }

    // Función para descifrar un mensaje
    function decryptMessage(encryptedMessage, sharedKey) {
        const bytes = CryptoJS.AES.decrypt(encryptedMessage, sharedKey);
        return bytes.toString(CryptoJS.enc.Utf8);
    }

    // Exponer las funciones necesarias
    return {
        generateSenderKeys,
        generateRecipientKeys,
        deriveSharedKey,
        encryptMessage,
        decryptMessage,
    };
})();
