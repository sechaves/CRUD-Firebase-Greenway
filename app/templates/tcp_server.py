import socket
import threading
import json
import firebase_admin
from firebase_admin import credentials, firestore

# --- Inicializar Firebase ---
cred = credentials.Certificate("serviceAccount.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# --- Diccionario de conexiones activas ---
connected_users = {}  # user_id -> socket

def save_message(chat_id, msg):
    """Guarda mensajes en Firebase si el destinatario no está conectado."""
    db.collection("chats").document(chat_id).collection("messages").add(msg)

def send_to_user(user_id, msg_json):
    """Envía mensaje al usuario si está conectado."""
    if user_id in connected_users:
        try:
            connected_users[user_id].send((msg_json + "\n").encode())
        except:
            pass

def handle_client(client_socket):
    user_id = None

    try:
        while True:
            data = client_socket.recv(4096).decode().strip()
            if not data:
                break

            msg = json.loads(data)

            if msg["type"] == "register":
                # Registrar conexión
                user_id = msg["user_id"]
                connected_users[user_id] = client_socket
                print(f"[+] {user_id} conectado.")
                continue

            if msg["type"] == "send_message":
                chat_id = msg["chat_id"]
                to_user = msg["to"]
                msg_json = json.dumps(msg)

                # Enviar al destinatario si está conectado
                send_to_user(to_user, msg_json)

                # Guardar SIEMPRE en Firebase
                save_message(chat_id, msg)

    except Exception as e:
        print("Error:", e)

    finally:
        if user_id in connected_users:
            del connected_users[user_id]
        client_socket.close()
        print(f"[-] {user_id} desconectado.")

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 9000))
    server_socket.listen(10)

    print("🔥 Servidor TCP corriendo en puerto 9000...")

    while True:
        client_socket, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    start_server()
