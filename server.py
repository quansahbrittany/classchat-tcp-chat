
# ClassChat - Multi-Client TCP Server

import socket
import threading
import json

# Server configuration
HOST = "127.0.0.1"
PORT = 5050

# Store connected clients and chat rooms
clients = {}
rooms = {}

# Protect shared data when multiple threads access it
server_lock = threading.RLock()


class ClientConnection:
    def __init__(self, sock, address):
        self.sock = sock
        self.address = address
        self.username = None
        self.send_lock = threading.Lock()


def send_json(client, message):
    """Send a JSON message to one client."""
    try:
        data = json.dumps(message) + "\n"

        with client.send_lock:
            client.sock.sendall(data.encode("utf-8"))

    except OSError:
        pass


def send_status(client, text, status="ok"):
    """Send a status or error message."""
    send_json(client, {
        "status": status,
        "sender": "SERVER",
        "receiver": client.username,
        "text": text
    })


def register_client(client, message):
    """Register a client with a unique username."""
    username = message.get("username", "").strip()

    if not username:
        send_status(client, "Username cannot be empty.", "error")
        return False

    with server_lock:
        if username in clients:
            send_status(client, "That username is already taken.", "error")
            return False

        client.username = username
        clients[username] = client

    send_status(client, f"Welcome to ClassChat, {username}!")
    print(f"{username} connected from {client.address}")

    return True


def handle_private_message(client, message):
    """Send a private message to another connected user."""
    receiver = message.get("receiver", "").strip()
    text = message.get("text", "").strip()

    if not receiver or not text:
        send_status(client, "Usage: /private username message", "error")
        return

    with server_lock:
        recipient = clients.get(receiver)

    if recipient is None:
        send_status(client, f"{receiver} is not online.", "error")
        return

    send_json(recipient, {
        "status": "message",
        "sender": client.username,
        "receiver": receiver,
        "text": text
    })

    send_status(client, f"Private message sent to {receiver}.")


def create_room(client, message):
    """Create a room and add its creator."""
    room_name = message.get("room", "").strip()

    if not room_name:
        send_status(client, "Enter a room name.", "error")
        return

    with server_lock:
        if room_name in rooms:
            send_status(client, "That room already exists.", "error")
            return

        rooms[room_name] = {client.username}

    send_status(client, f"Room '{room_name}' created. You joined it.")
    print(f"{client.username} created room {room_name}")


def join_room(client, message):
    """Add a client to an existing room."""
    room_name = message.get("room", "").strip()

    with server_lock:
        if room_name not in rooms:
            send_status(client, f"Room '{room_name}' does not exist.", "error")
            return

        rooms[room_name].add(client.username)
        members = list(rooms[room_name])

    send_status(client, f"You joined room '{room_name}'.")

    for username in members:
        if username != client.username:
            with server_lock:
                member = clients.get(username)

            if member:
                send_status(member, f"{client.username} joined {room_name}.")


def send_group_message(client, message):
    """Send a message to everyone in a room."""
    room_name = message.get("room", "").strip()
    text = message.get("text", "").strip()

    if not text:
        send_status(client, "Group message cannot be empty.", "error")
        return

    with server_lock:
        if room_name not in rooms:
            send_status(client, f"Room '{room_name}' does not exist.", "error")
            return

        if client.username not in rooms[room_name]:
            send_status(client, f"You have not joined '{room_name}'.", "error")
            return

        recipients = [
            clients[username]
            for username in rooms[room_name]
            if username in clients
        ]

    for recipient in recipients:
        send_json(recipient, {
            "status": "message",
            "sender": client.username,
            "receiver": f"room:{room_name}",
            "text": text
        })


def process_message(client, message):
    """Process commands received from a registered client."""
    command = message.get("command")

    if command == "private":
        handle_private_message(client, message)

    elif command == "create":
        create_room(client, message)

    elif command == "join":
        join_room(client, message)

    elif command == "group":
        send_group_message(client, message)

    elif command == "quit":
        send_status(client, "You have disconnected from ClassChat.")
        return False

    else:
        send_status(client, "Unknown command.", "error")

    return True


def remove_client(client):
    """Remove a disconnected client from the server."""
    username = client.username

    if username is None:
        return

    with server_lock:
        clients.pop(username, None)

        for room_name in list(rooms):
            rooms[room_name].discard(username)

            if not rooms[room_name]:
                del rooms[room_name]

    print(f"{username} disconnected.")


def handle_client(sock, address):
    """Handle one client connection in its own thread."""
    client = ClientConnection(sock, address)
    buffer = ""

    try:
        while True:
            data = sock.recv(4096)

            if not data:
                break

            buffer += data.decode("utf-8")

            # Process complete newline-delimited JSON messages
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)

                if not line.strip():
                    continue

                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    send_status(client, "Invalid JSON message.", "error")
                    continue

                if not isinstance(message, dict):
                    send_status(client, "Message must be a JSON object.", "error")
                    continue

                if client.username is None:
                    if message.get("command") != "register":
                        send_status(client, "Register a username first.", "error")
                    else:
                        register_client(client, message)
                else:
                    if not process_message(client, message):
                        return

    except (ConnectionResetError, OSError):
        pass

    finally:
        remove_client(client)
        try:
            sock.close()
        except OSError:
            pass


def main():
    """Start the ClassChat server."""
    server_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print("ClassChat server is running...")
    print(f"Listening on {HOST}:{PORT}")
    print("Waiting for clients...")

    try:
        while True:
            client_socket, client_address = server_socket.accept()

            print(f"New connection from {client_address}")

            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address),
                daemon=True
            )

            client_thread.start()

    except KeyboardInterrupt:
        print("\nShutting down ClassChat server...")

    finally:
        server_socket.close()


if __name__ == "__main__":
    main()
