# e2ee.py

from Crypto.PublicKey import ECC
from Crypto.Cipher import AES
from Crypto.Hash import SHA256, HMAC
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import HKDF


class E2EE:
    def __init__(self):
        # Genera el par de claves de identidad (pública y privada)
        self.identity_key = ECC.generate(curve='P-256')
        self.identity_public_key = self.identity_key.public_key()

    def generate_ephemeral_key(self):
        # Genera un par de claves efímeras para cada sesión o mensaje
        self.ephemeral_key = ECC.generate(curve='P-256')
        self.ephemeral_public_key = self.ephemeral_key.public_key()

    def compute_shared_secret(self, recipient_public_key):
        # Calcula el secreto compartido utilizando ECDH
        shared_secret = self.ephemeral_key.d * recipient_public_key.pointQ
        return int(shared_secret.x).to_bytes(32, byteorder='big')

    def derive_keys(self, shared_secret):
        # Deriva claves de cifrado y MAC utilizando HKDF
        key_material = HKDF(
            master=shared_secret,
            key_len=64,
            salt=None,
            hashmod=SHA256,
            num_keys=2,
            context=b'E2EE Chat'
        )
        encryption_key = key_material[:32]
        mac_key = key_material[32:]
        return encryption_key, mac_key

    def encrypt_message(self, plaintext, encryption_key, mac_key):
        # Cifra el mensaje utilizando AES-256 en modo CBC
        iv = get_random_bytes(16)
        cipher = AES.new(encryption_key, AES.MODE_CBC, iv)
        # Asegurar que el plaintext es múltiplo del tamaño de bloque
        pad_len = 16 - (len(plaintext) % 16)
        padded_plaintext = plaintext + bytes([pad_len] * pad_len)
        ciphertext = cipher.encrypt(padded_plaintext)

        # Genera el MAC para garantizar la integridad
        mac = HMAC.new(mac_key, ciphertext, digestmod=SHA256).digest()

        return iv + ciphertext + mac

    def decrypt_message(self, encrypted_message, encryption_key, mac_key):
        # Extrae el IV, el ciphertext y el MAC
        iv = encrypted_message[:16]
        mac_received = encrypted_message[-32:]
        ciphertext = encrypted_message[16:-32]

        # Verifica el MAC
        mac_calculated = HMAC.new(mac_key, ciphertext, digestmod=SHA256).digest()
        if mac_calculated != mac_received:
            raise ValueError("El MAC no coincide. El mensaje puede haber sido alterado.")

        # Descifra el mensaje
        cipher = AES.new(encryption_key, AES.MODE_CBC, iv)
        padded_plaintext = cipher.decrypt(ciphertext)

        # Elimina el padding
        pad_len = padded_plaintext[-1]
        plaintext = padded_plaintext[:-pad_len]

        return plaintext

    def export_public_keys(self):
        # Exporta las claves públicas en formato DER
        identity_pubkey_der = self.identity_public_key.export_key(format='DER')
        ephemeral_pubkey_der = self.ephemeral_public_key.export_key(format='DER')
        return identity_pubkey_der, ephemeral_pubkey_der

    def import_public_key(self, pubkey_der):
        # Importa una clave pública en formato DER
        return ECC.import_key(pubkey_der)
