# e2ee.py

from Crypto.PublicKey import ECC
from Crypto.Cipher import AES
from Crypto.Hash import SHA256, HMAC
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import HKDF, PBKDF2
import json

class E2EE:
    def __init__(self, user_id, name, username, email, password):
        """
        Inicializa la clase E2EE para un usuario específico.
        
        Parámetros:
            user_id (int): ID único del usuario en la base de datos.
            name (str): Nombre completo del usuario.
            username (str): Nombre de usuario.
            email (str): Correo electrónico del usuario.
            password (str): Contraseña del usuario.
        """
        self.user_id = user_id
        self.name = name
        self.username = username
        self.email = email
        self.password = password

        # Genera el par de claves pública y privada
        self.private_key = self.generate_private_key()
        self.public_key = self.private_key.public_key()

        # Inicialización del Ratchet
        self.root_key = None
        self.send_chain_key = None
        self.recv_chain_key = None
        self.send_message_number = 0
        self.recv_message_number = 0

    def generate_private_key(self):
        """
        Genera una clave privada única para el usuario derivada de sus datos personales.
        
        Retorna:
            ECC.EccKey: Objeto de clave privada ECC.
        """
        # Combina los datos del usuario para crear una semilla
        seed_material = f"{self.user_id}{self.name}{self.username}{self.password}".encode('utf-8')
        
        # Deriva una semilla utilizando HKDF con sal aleatoria
        salt = get_random_bytes(16)
        derived_key = HKDF(
            master=seed_material,
            key_len=32,
            salt=salt,
            hashmod=SHA256,
            context=b'E2EE Private Key'
        )
        
        # Usa la semilla derivada para generar una clave privada ECC
        # Nota: PyCryptodome no soporta la creación directa de claves ECC a partir de una semilla.
        # Por lo tanto, se utiliza la semilla para generar un número entero dentro del rango válido para P-256.
        # Luego, se crea la clave privada a partir de este número.
        
        # Curve P-256 order
        curve_order = int('ffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551', 16)
        
        # Convierte la clave derivada a un entero
        private_int = int.from_bytes(derived_key, byteorder='big') % curve_order
        private_key = ECC.construct(curve='P-256', d=private_int)
        
        return private_key

    def export_public_key(self):
        """
        Exporta la clave pública en formato PEM.
    
        Retorna:
            str: Clave pública en formato PEM.
        """
        return self.public_key.export_key(format='PEM')
    
    def export_public_key_der_hex(self):
        """
        Exporta la clave pública en formato DER y la convierte a una cadena hexadecimal.

        Retorna:
            str: Clave pública en formato DER hexadecimal.
        """
        der_bytes = self.public_key.export_key(format='DER')
        return der_bytes.hex()

    def export_private_key_encrypted(self, password):
        """
        Exporta la clave privada encriptada utilizando la contraseña del usuario.
        
        Parámetros:
            password (str): Contraseña del usuario para encriptar la clave privada.
        
        Retorna:
            str: Clave privada encriptada en formato JSON hexadecimal.
        """
        # Deriva una clave de cifrado a partir de la contraseña usando PBKDF2 con sal
        salt = get_random_bytes(16)
        encryption_key = PBKDF2(password, salt, dkLen=32, count=100000, hmac_hash_module=SHA256)
        
        # Cifra la clave privada utilizando AES-256-GCM
        cipher = AES.new(encryption_key, AES.MODE_GCM)
        private_key_bytes = self.private_key.export_key(format='DER')
        ciphertext, tag = cipher.encrypt_and_digest(private_key_bytes)
        
        # Almacena el salt, nonce, tag y ciphertext
        encrypted_private_key = {
            'salt': salt.hex(),
            'nonce': cipher.nonce.hex(),
            'tag': tag.hex(),
            'ciphertext': ciphertext.hex()
        }
        
        return json.dumps(encrypted_private_key)

    @staticmethod
    def import_private_key_encrypted(encrypted_private_key_json, password):
        """
        Importa y descifra la clave privada a partir de datos encriptados.
        
        Parámetros:
            encrypted_private_key_json (str): Clave privada encriptada en formato JSON hexadecimal.
            password (str): Contraseña del usuario para descifrar la clave privada.
        
        Retorna:
            ECC.EccKey: Objeto de clave privada ECC.
        """
        encrypted_private_key = json.loads(encrypted_private_key_json)
        salt = bytes.fromhex(encrypted_private_key['salt'])
        nonce = bytes.fromhex(encrypted_private_key['nonce'])
        tag = bytes.fromhex(encrypted_private_key['tag'])
        ciphertext = bytes.fromhex(encrypted_private_key['ciphertext'])
        
        # Deriva la clave de cifrado a partir de la contraseña y la sal
        encryption_key = PBKDF2(password, salt, dkLen=32, count=100000, hmac_hash_module=SHA256)
        
        # Descifra la clave privada
        cipher = AES.new(encryption_key, AES.MODE_GCM, nonce=nonce)
        private_key_bytes = cipher.decrypt_and_verify(ciphertext, tag)
        
        # Importa la clave privada desde los bytes descifrados
        private_key = ECC.import_key(private_key_bytes)
        
        return private_key

    def compute_shared_secret(self, recipient_public_key_pem):
        """
        Calcula el secreto compartido utilizando ECDH con la clave pública del destinatario.
        
        Parámetros:
            recipient_public_key_pem (str): Clave pública del destinatario en formato PEM.
        
        Retorna:
            bytes: Secreto compartido derivado.
        """
        recipient_public_key = ECC.import_key(recipient_public_key_pem)
        # Realiza ECDH
        shared_point = self.private_key.d * recipient_public_key.pointQ
        shared_secret = int(shared_point.x).to_bytes(32, byteorder='big')
        return shared_secret

    def derive_ratchet_keys(self, shared_secret):
        """
        Deriva el root key, send_chain_key y recv_chain_key a partir del secreto compartido.
        
        Parámetros:
            shared_secret (bytes): Secreto compartido derivado de ECDH.
        
        Retorna:
            tuple: (root_key, send_chain_key, recv_chain_key)
        """
        key_material = HKDF(
            master=shared_secret,
            key_len=96,  # 32 bytes para root_key, 32 para send_chain_key, 32 para recv_chain_key
            salt=None,
            hashmod=SHA256,
            context=b'DoubleRatchet Initialization'
        )
        root_key = key_material[:32]
        send_chain_key = key_material[32:64]
        recv_chain_key = key_material[64:]
        return root_key, send_chain_key, recv_chain_key

    def initialize_ratchet(self, recipient_public_key_pem):
        """
        Inicializa el estado del ratchet al crear un nuevo chat.
        
        Parámetros:
            recipient_public_key_pem (str): Clave pública del destinatario en formato PEM.
        """
        # Calcula el secreto compartido utilizando ECDH
        shared_secret = self.compute_shared_secret(recipient_public_key_pem)
        
        # Deriva el root key y los chain keys
        self.root_key, self.send_chain_key, self.recv_chain_key = self.derive_ratchet_keys(shared_secret)
        
        # Inicializa los números de mensajes
        self.send_message_number = 0
        self.recv_message_number = 0

    def perform_ratchet_step(self, new_ephemeral_public_key_der):
        """
        Realiza un paso del ratchet al recibir una nueva clave efímera.
        
        Parámetros:
            new_ephemeral_public_key_der (str): Nueva clave efímera pública del destinatario en formato DER hexadecimal.
        """
        # Calcula el nuevo secreto compartido
        new_shared_secret = self.compute_shared_secret(new_ephemeral_public_key_der)
        
        # Deriva un nuevo root key y nuevos chain keys
        key_material = HKDF(
            master=new_shared_secret,
            key_len=96,
            salt=None,
            hashmod=SHA256,
            context=b'DoubleRatchet Ratchet Step'
        )
        new_root_key = key_material[:32]
        new_send_chain_key = key_material[32:64]
        new_recv_chain_key = key_material[64:]
        
        # Actualiza el root key y los chain keys
        self.root_key = new_root_key
        self.send_chain_key = new_send_chain_key
        self.recv_chain_key = new_recv_chain_key
        
        # Reinicia los números de mensajes
        self.send_message_number = 0
        self.recv_message_number = 0

    def derive_message_key(self, chain_key, message_number):
        """
        Deriva una clave de mensaje a partir de un chain key y el número de mensaje.
        
        Parámetros:
            chain_key (bytes): Chain key actual.
            message_number (int): Número de mensaje.
        
        Retorna:
            bytes: Clave de mensaje derivada.
        """
        # Simple KDF: SHA256(chain_key || message_number)
        kdf_input = chain_key + message_number.to_bytes(4, byteorder='big')
        message_key = SHA256.new(kdf_input).digest()
        return message_key

    def encrypt_message(self, plaintext):
        """
        Cifra el mensaje utilizando AES-256-GCM y actualiza el send_chain_key.
        
        Parámetros:
            plaintext (bytes): Mensaje en texto claro.
        
        Retorna:
            str: Mensaje cifrado en formato JSON hexadecimal.
        """
        if not self.send_chain_key:
            raise ValueError("send_chain_key no está establecido.")
        
        # Deriva la clave de mensaje
        message_key = self.derive_message_key(self.send_chain_key, self.send_message_number + 1)
        
        # Actualiza el send_chain_key (Chain key advancement)
        self.send_chain_key = SHA256.new(self.send_chain_key).digest()
        self.send_message_number += 1
        
        # Cifra el mensaje usando AES-256-GCM
        cipher = AES.new(message_key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext)
        
        # Construye el mensaje cifrado
        encrypted_message = {
            'nonce': cipher.nonce.hex(),
            'ciphertext': ciphertext.hex(),
            'tag': tag.hex(),
            'message_number': self.send_message_number
        }
        
        return json.dumps(encrypted_message)

    def decrypt_message(self, encrypted_message_json):
        """
        Descifra el mensaje cifrado y verifica su integridad.
        
        Parámetros:
            encrypted_message_json (str): Mensaje cifrado en formato JSON hexadecimal.
        
        Retorna:
            bytes: Mensaje en texto claro.
        
        Excepciones:
            ValueError: Si la autenticidad del mensaje no puede ser verificada.
        """
        if not self.recv_chain_key:
            raise ValueError("recv_chain_key no está establecido.")
        
        encrypted_message = json.loads(encrypted_message_json)
        nonce = bytes.fromhex(encrypted_message['nonce'])
        ciphertext = bytes.fromhex(encrypted_message['ciphertext'])
        tag = bytes.fromhex(encrypted_message['tag'])
        message_number = encrypted_message['message_number']
        
        # Verifica si hay saltos en los mensajes
        if message_number != self.recv_message_number + 1:
            raise ValueError("Número de mensaje inesperado. Potencial ataque de reenvío.")
        
        # Deriva la clave de mensaje
        message_key = self.derive_message_key(self.recv_chain_key, message_number)
        
        # Actualiza el recv_chain_key (Chain key advancement)
        self.recv_chain_key = SHA256.new(self.recv_chain_key).digest()
        self.recv_message_number += 1
        
        # Descifra el mensaje usando AES-256-GCM
        cipher = AES.new(message_key, AES.MODE_GCM, nonce=nonce)
        try:
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
            return plaintext
        except ValueError:
            raise ValueError("La autenticidad del mensaje no pudo ser verificada.")

    def export_public_keys_for_chat(self):
        """
        Prepara las claves públicas necesarias para iniciar un chat.
        
        Retorna:
            dict: Diccionario con las claves públicas necesarias.
        """
        return {
            'identity_public_key': self.export_public_key()
            # Aquí puedes añadir otras claves públicas necesarias para el Double Ratchet si lo implementas
        }

    def serialize_ratchet_state(self):
        """
        Serializa el estado actual del ratchet para almacenamiento o transmisión.
        
        Retorna:
            str: Estado del ratchet en formato JSON hexadecimal.
        """
        state = {
            'root_key': self.root_key.hex() if self.root_key else None,
            'send_chain_key': self.send_chain_key.hex() if self.send_chain_key else None,
            'recv_chain_key': self.recv_chain_key.hex() if self.recv_chain_key else None,
            'send_message_number': self.send_message_number,
            'recv_message_number': self.recv_message_number
        }
        return json.dumps(state)

    def deserialize_ratchet_state(self, state_json):
        """
        Deserializa el estado del ratchet desde un JSON.
        
        Parámetros:
            state_json (str): Estado del ratchet en formato JSON hexadecimal.
        """
        state = json.loads(state_json)
        self.root_key = bytes.fromhex(state['root_key']) if state['root_key'] else None
        self.send_chain_key = bytes.fromhex(state['send_chain_key']) if state['send_chain_key'] else None
        self.recv_chain_key = bytes.fromhex(state['recv_chain_key']) if state['recv_chain_key'] else None
        self.send_message_number = state['send_message_number']
        self.recv_message_number = state['recv_message_number']
