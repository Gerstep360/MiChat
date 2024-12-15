// Asegúrate de incluir elliptic.js y CryptoJS en tu entorno antes de ejecutar este código
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

// PASO 1: Generar claves para remitente y destinatario
console.log("=== Generación de claves ===");

const senderKeys = CryptoModule.generateSenderKeys();
const recipientKeys = CryptoModule.generateRecipientKeys();

console.log("Clave privada del remitente:", senderKeys.privateKey);
console.log("Clave pública del remitente:", senderKeys.publicKey);

console.log("Clave privada del destinatario:", recipientKeys.privateKey);
console.log("Clave pública del destinatario:", recipientKeys.publicKey);

// PASO 2: Derivar la clave compartida
console.log("\n=== Derivación de la clave compartida ===");

// En el remitente
const senderSharedKey = CryptoModule.deriveSharedKey(senderKeys.privateKey, recipientKeys.publicKey);
console.log("Clave compartida derivada por el remitente:", senderSharedKey);

// En el destinatario
const recipientSharedKey = CryptoModule.deriveSharedKey(recipientKeys.privateKey, senderKeys.publicKey);
console.log("Clave compartida derivada por el destinatario:", recipientSharedKey);

// Verificar que ambas claves compartidas sean iguales
console.assert(senderSharedKey === recipientSharedKey, "¡Error! Las claves compartidas no coinciden");

// PASO 3: Cifrar un mensaje en el remitente
console.log("\n=== Cifrado del mensaje ===");

const message = "Hola, este es un mensaje secreto";
const encryptedMessage = CryptoModule.encryptMessage(message, senderSharedKey);

console.log("Mensaje original:", message);
console.log("Mensaje cifrado:", encryptedMessage);

// PASO 4: Descifrar el mensaje en el destinatario
console.log("\n=== Descifrado del mensaje ===");

const decryptedMessage = CryptoModule.decryptMessage(encryptedMessage, recipientSharedKey);

console.log("Mensaje descifrado:", decryptedMessage);

// Verificar que el mensaje original y el descifrado coincidan
//console.assert(message === decryptedMessage, "¡Error! El mensaje descifrado no coincide con el original");
