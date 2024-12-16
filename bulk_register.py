# regenerate_keys.py

from ecpy.curves     import Curve,Point
from ecpy.keys       import ECPublicKey, ECPrivateKey
from ecpy.ecdsa      import ECDSA
import sqlite3

def regenerate_keys():
    EC = Curve.get_curve('secp256k1')
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users')
    users = cursor.fetchall()
    for user in users:
        user_id = user[0]
        key_pair = EC.genKeyPair()
        private_key = key_pair.getPrivate('hex').padStart(64, '0')
        public_key = key_pair.getPublic(False, 'hex')  # Clave pública no comprimida, 130 caracteres
        cursor.execute('UPDATE users SET private_key = ?, public_key = ? WHERE id = ?', (private_key, public_key, user_id))
        print(f"Regeneradas claves para usuario_id: {user_id}")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    regenerate_keys()
