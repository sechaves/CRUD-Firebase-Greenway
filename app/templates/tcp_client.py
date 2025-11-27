import socket
import json

def start_client(user_id):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("TU_IP_O_DOMINIO", 9000))

    # Registrarse
    s.send(json.dumps({
        "type": "register",
        "user_id": user_id
    }).encode())

    print("Conectado como:", user_id)

    while True:
        msg = input("Mensaje: ")

        data = {
            "type": "send_message",
            "chat_id": "demo_chat",
            "from": user_id,
            "to": "otro_usuario",
            "text": msg
        }

        s.send((json.dumps(data) + "\n").encode())

if __name__ == "__main__":
    start_client("user_1")
