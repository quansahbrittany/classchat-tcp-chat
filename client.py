
# ClassChat - TCP Client

import socket
import threading
import json

# Server configuration
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5050


def send_json(client_socket, message):
    """Convert a Python dictionary into JSON and send it."""
    data = json.dumps(message) + "\n"
    client_socket.sendall(data.encode("utf-8"))


def receive_messages(client_socket):
    """Continuously receive messages from the server."""
    buffer = ""

    while True:
        try:
            data = client_socket.recv(4096)

            if not data:
                print("\nServer disconnected.")
                break

            buffer += data.decode("utf-8")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)

                if not line.strip():
                    continue

                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    print("\nReceived an invalid message.")
                    continue

                status = message.get("status")
                sender = message.get("sender", "SERVER")
                text = message.get("text", "")
                receiver = message.get("receiver", "")

                if status == "message":
                    print(f"\n[{receiver}] {sender}: {text}")

                elif status == "error":
                    print(f"\nERROR: {text}")

                else:
                    print(f"\n{text}")

        except OSError:
            break


def show_help():
    """Display available ClassChat commands."""
    print("\nCLASSCHAT COMMANDS")
    print("------------------------------")
    print("/private username message")
    print("/create room_name")
    print("/join room_name")
    print("/group room_name message")
    print("/help")
    print("/quit")
    print("------------------------------\n")


def main():
    """Connect to the server and start the chat client."""
    client_socket = socket.socket(
        socket.AF_INET,
        socket.SOCK_STREAM
    )

    try:
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        print("Connected to ClassChat server!")

    except ConnectionRefusedError:
        print("Unable to connect. Make sure the server is running.")
        client_socket.close()
        return

    username = input("Choose a username: ").strip()

    if not username:
        print("Username cannot be empty.")
        client_socket.close()
        return

    # Start a separate thread to receive messages
    receive_thread = threading.Thread(
        target=receive_messages,
        args=(client_socket,),
        daemon=True
    )

    receive_thread.start()

    # Register username with the server
    send_json(client_socket, {
        "command": "register",
        "username": username
    })

    show_help()

    try:
        while True:
            user_input = input(f"{username}> ").strip()

            if not user_input:
                continue

            if user_input == "/help":
                show_help()

            elif user_input.startswith("/private "):
                parts = user_input.split(" ", 2)

                if len(parts) < 3:
                    print("Usage: /private username message")
                    continue

                send_json(client_socket, {
                    "command": "private",
                    "receiver": parts[1],
                    "text": parts[2]
                })

            elif user_input.startswith("/create "):
                parts = user_input.split(maxsplit=1)

                if len(parts) < 2:
                    print("Usage: /create room_name")
                    continue

                send_json(client_socket, {
                    "command": "create",
                    "room": parts[1]
                })

            elif user_input.startswith("/join "):
                parts = user_input.split(maxsplit=1)

                if len(parts) < 2:
                    print("Usage: /join room_name")
                    continue

                send_json(client_socket, {
                    "command": "join",
                    "room": parts[1]
                })

            elif user_input.startswith("/group "):
                parts = user_input.split(" ", 2)

                if len(parts) < 3:
                    print("Usage: /group room_name message")
                    continue

                send_json(client_socket, {
                    "command": "group",
                    "room": parts[1],
                    "text": parts[2]
                })

            elif user_input == "/quit":
                send_json(client_socket, {
                    "command": "quit"
                })
                break

            else:
                print("Unknown command. Type /help to see available commands.")

    except (KeyboardInterrupt, OSError):
        print("\nClosing ClassChat...")

    finally:
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        client_socket.close()


if __name__ == "__main__":
    main()
