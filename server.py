
# ClassChat - Multi-Client TCP Chat Server
# CS 350 Semester Project - Fall 2026

import socket
import threading
import json

# Server configuration
HOST = "127.0.0.1"
PORT = 5050

# Connected clients and chat rooms
clients = {}
rooms = {}

# Protect shared data between client threads
server_lock = threading.RLock()


class ClientConnection:
    """Stores information about a connected client."""

    def __init__(self, sock, address):
        self.sock = sock
        self.address = address
        self.username = None
        self.send_lock = threading.Lock()


def send_json(client, message):
    """Send a JSON message containing the required four fields."""

    data = {
        "status": message.get("status", "notice"),
        "sender": message.get("sender", "SERVER"),
        "receiver": message.get("receiver", ""),
        "text": message.get("text", "")
    }

    try:
        encoded_message = json.dumps(data) + "\n"

        with client.send_lock:
            client.sock.sendall(encoded_message.encode("utf-8"))

    except OSError:
        pass


def send_status(client, text, status="notice"):
    """Send a notification or error to one client."""

    send_json(client, {
        "status": status,
        "sender": "SERVER",
        "receiver": client.username or "",
        "text": text
    })


def register_client(client, message):
    """Register a client using a unique username."""

    username = message.get("sender", "").strip()

    if not username:
        send_status(client, "Username cannot be empty.", "error")
        return False

    with server_lock:
        if username in clients:
            send_status(
                client,
                "That username is already taken.",
                "error"
            )
            return False

        client.username = username
        clients[username] = client

    send_status(
        client,
        f"Welcome to ClassChat, {username}!"
    )

    print(f"{username} connected from {client.address}")

    return True


def handle_private_message(client, message):
    """Route a private message to one connected user."""

    receiver = message.get("receiver", "").strip()
    text = message.get("text", "").strip()

    if not receiver or not text:
        send_status(
            client,
            "Usage: /private username message",
            "error"
        )
        return

    with server_lock:
        recipient = clients.get(receiver)

    if recipient is None:
        send_status(
            client,
            f"{receiver} is not online.",
            "error"
        )
        return

    if recipient is client:
        send_status(
            client,
            "You cannot send a private message to yourself.",
            "error"
        )
        return

    send_json(recipient, {
        "status": "private",
        "sender": client.username,
        "receiver": receiver,
        "text": text
    })

    send_status(
        client,
        f"Private message sent to {receiver}."
    )


def create_room(client, message):
    """Create a new group and add its creator."""

    room_name = message.get("receiver", "").strip()

    if not room_name:
        send_status(client, "Enter a room name.", "error")
        return

    with server_lock:
        if room_name in rooms:
            send_status(
                client,
                "That room already exists.",
                "error"
            )
            return

        rooms[room_name] = {client.username}

    send_status(
        client,
        f"Room '{room_name}' created. You joined it."
    )

    print(f"{client.username} created room {room_name}")


def join_room(client, message):
    """Allow a client to join an existing group."""

    room_name = message.get("receiver", "").strip()

    if not room_name:
        send_status(client, "Enter a room name.", "error")
        return

    with server_lock:
        if room_name not in rooms:
            send_status(
                client,
                f"Room '{room_name}' does not exist.",
                "error"
            )
            return

        if client.username in rooms[room_name]:
            send_status(
                client,
                f"You are already in room '{room_name}'."
            )
            return

        rooms[room_name].add(client.username)

        members = [
            clients[name]
            for name in rooms[room_name]
            if name in clients
        ]

    send_status(client, f"You joined room '{room_name}'.")

    for member in members:
        if member is not client:
            send_status(
                member,
                f"{client.username} joined room '{room_name}'."
            )


def send_group_message(client, message):
    """Broadcast a message to members of a group."""

    room_name = message.get("receiver", "").strip()
    text = message.get("text", "").strip()

    if not text:
        send_status(
            client,
            "Group message cannot be empty.",
            "error"
        )
        return

    with server_lock:
        if room_name not in rooms:
            send_status(
                client,
                f"Room '{room_name}' does not exist.",
                "error"
            )
            return

        if client.username not in rooms[room_name]:
            send_status(
                client,
                f"You have not joined '{room_name}'.",
                "error"
            )
            return

        recipients = [
            clients[name]
            for name in rooms[room_name]
            if name in clients
        ]

    for recipient in recipients:
        send_json(recipient, {
            "status": "group",
            "sender": client.username,
            "receiver": room_name,
            "text": text
        })


def process_message(client, message):
    """Determine which action a client is requesting."""

    status = message.get("status")

    if status == "private":
        handle_private_message(client, message)

    elif status == "create":
        create_room(client, message)

    elif status == "join":
        join_room(client, message)

    elif status == "group":
        send_group_message(client, message)

    elif status == "quit":
        send_status(
            client,
            "You have disconnected from ClassChat."
        )
        return False

    else:
        send_status(
            client,
            "Unknown command. Type /help for available commands.",
            "error"
        )

    return True


def remove_client(client):
    """Remove a disconnected user and notify remaining room members."""

    username = client.username

    if username is None:
        return

    notifications = []

    with server_lock:
        # Remove the client from the active user list
        if clients.get(username) is client:
            del clients[username]

        # Remove the user from every room
        for room_name in list(rooms.keys()):

            if username in rooms[room_name]:
                rooms[room_name].remove(username)

                for member_name in rooms[room_name]:
                    member = clients.get(member_name)

                    if member:
                        notifications.append(
                            (member, room_name)
                        )

            # Delete rooms with no remaining members
            if not rooms[room_name]:
                del rooms[room_name]

    # Notify remaining members outside the lock
    for member, room_name in notifications:
        send_status(
            member,
            f"{username} has left room '{room_name}'."
        )

    print(f"{username} disconnected.")


def handle_client(sock, address):
    """Handle communication with one client in its own thread."""

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
                    send_status(
                        client,
                        "Invalid JSON message.",
                        "error"
                    )
                    continue

                if not isinstance(message, dict):
                    send_status(
                        client,
                        "Message must be a JSON object.",
                        "error"
                    )
                    continue

                if client.username is None:

                    if message.get("status") != "register":
                        send_status(
                            client,
                            "Register a username first.",
                            "error"
                        )
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
    """Start the ClassChat TCP server."""

    server_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    server_socket.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print("ClassChat server is running...")
    print(f"Listening on {HOST}:{PORT}")
    print("Waiting for clients...")

    try:
        while True:
            client_socket, client_address = server_socket.accept()

            print(f"New connection from {client_address}")

            # Create a separate thread for each client
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
