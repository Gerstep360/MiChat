// Asegúrate de incluir elliptic.js y CryptoJS en tu entorno antes de ejecutar este código
const EC = new elliptic.ec('secp256k1'); // Curva compatible

const CryptoModule = (() => {
    // Generar claves del remitente
    function generateSenderKeys() {
        const senderKeyPair = EC.genKeyPair();
        return {
            privateKey: senderKeyPair.getPrivate('hex').padStart(64, '0'), // 64 caracteres
            publicKey: senderKeyPair.getPublic(false, 'hex'), // Clave pública no comprimida, 130 caracteres
        };
    }

    // Generar claves del destinatario
    function generateRecipientKeys() {
        const recipientKeyPair = EC.genKeyPair();
        return {
            privateKey: recipientKeyPair.getPrivate('hex').padStart(64, '0'), // 64 caracteres
            publicKey: recipientKeyPair.getPublic(false, 'hex'), // Clave pública no comprimida, 130 caracteres
        };
    }

    // Derivar clave compartida
    function deriveSharedKey(privateKey, publicKey) {
        const privateKeyObject = EC.keyFromPrivate(privateKey, 'hex');
        const publicKeyObject = EC.keyFromPublic(publicKey, 'hex');
        const sharedSecret = privateKeyObject.derive(publicKeyObject.getPublic()).toString(16);
        // Asegurar que la clave compartida tenga 64 caracteres
        return sharedSecret.padStart(64, '0').slice(0, 64);
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
