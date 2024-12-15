# prueba_ee2e.py

from e2ee import E2EE

# Datos de Alice
alice_id = 1
alice_name = "Alice Smith"
alice_username = "alice"
alice_email = "alice@example.com"
alice_password = "alice_secure_password"

# Datos de Bob
bob_id = 2
bob_name = "Bob Johnson"
bob_username = "bob"
bob_email = "bob@example.com"
bob_password = "bob_secure_password"

# Inicialización de E2EE para Alice y Bob
alice_e2ee = E2EE(alice_id, alice_name, alice_username, alice_email, alice_password)
bob_e2ee = E2EE(bob_id, bob_name, bob_username, bob_email, bob_password)

# Exportar claves públicas para el intercambio
alice_public_keys = alice_e2ee.export_public_keys_for_chat()
bob_public_keys = bob_e2ee.export_public_keys_for_chat()

# Supongamos que Alice y Bob intercambian sus claves públicas de alguna manera segura
alice_identity_public_key = alice_public_keys['identity_public_key']
bob_identity_public_key = bob_public_keys['identity_public_key']

# Ambos calculan el secreto compartido
shared_secret_alice = alice_e2ee.compute_shared_secret(bob_identity_public_key)
shared_secret_bob = bob_e2ee.compute_shared_secret(alice_identity_public_key)

# Ambos derivan el root key y los chain keys
root_key_alice, send_chain_key_alice, recv_chain_key_alice = alice_e2ee.derive_ratchet_keys(shared_secret_alice)
root_key_bob, send_chain_key_bob, recv_chain_key_bob = bob_e2ee.derive_ratchet_keys(shared_secret_bob)

# Asignar chain keys de forma cruzada para sincronización
alice_e2ee.root_key = root_key_alice
alice_e2ee.send_chain_key = send_chain_key_alice
alice_e2ee.recv_chain_key = send_chain_key_bob  # Alice's recv_chain_key = Bob's send_chain_key

bob_e2ee.root_key = root_key_bob
bob_e2ee.send_chain_key = send_chain_key_bob
bob_e2ee.recv_chain_key = send_chain_key_alice  # Bob's recv_chain_key = Alice's send_chain_key

# Ahora, Alice y Bob pueden intercambiar mensajes de manera segura

# Alice envía un mensaje a Bob
plaintext_message_alice = "Hola Bob, ¿cómo estás?".encode('utf-8')  # Convertir a bytes
encrypted_message_alice = alice_e2ee.encrypt_message(plaintext_message_alice)
print(f"Alice envía: {encrypted_message_alice}")

# Bob recibe y descifra el mensaje de Alice
try:
    decrypted_message_bob = bob_e2ee.decrypt_message(encrypted_message_alice)
    print(f"Bob recibe: {decrypted_message_bob.decode('utf-8')}")
except ValueError as e:
    print(f"Error al descifrar el mensaje en Bob: {e}")

# Bob responde a Alice
plaintext_message_bob = "Hola Alice, estoy bien. Gracias por preguntar.".encode('utf-8')  # Convertir a bytes
encrypted_message_bob = bob_e2ee.encrypt_message(plaintext_message_bob)
print(f"Bob envía: {encrypted_message_bob}")

# Alice recibe y descifra el mensaje de Bob
try:
    decrypted_message_alice = alice_e2ee.decrypt_message(encrypted_message_bob)
    print(f"Alice recibe: {decrypted_message_alice.decode('utf-8')}")
except ValueError as e:
    print(f"Error al descifrar el mensaje en Alice: {e}")
