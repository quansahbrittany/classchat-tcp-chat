
import socket
import threading
import json

HOST = "127.0.0.1"
PORT = 5050


def send_json(client_socket, message):
    """Send one JSON message to the server."""
    message.setdefault("status", "")
    message.setdefault("sender", "")
    message.setdefault("receiver", "")
    message.setdefault("text", "")

    data = json.dumps(message) + "\n"
    client_socket.sendall(data.encode("utf-8"))


def receive_registration_response(client_socket):
    """Wait for the server's response after username registration."""
    buffer = b""

    while b"\n" not in buffer:
        data = client_socket.recv(4096)

        if not data:
            raise ConnectionError("Server disconnected.")

        buffer += data

    line, _remaining = buffer.split(b"\n", 1)
    return json.loads(line.decode("utf-8"))


def receive_messages(client_socket, stop_event):
    """Dedicated thread for receiving messages from the server."""
    buffer = b""

    while not stop_event.is_set():
        try:
            data = client_socket.recv(4096)

            if not data:
                print("\nServer disconnected.")
                stop_event.set()
                break

            buffer += data

            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)

                if not line.strip():
                    continue

                message = json.loads(line.decode("utf-8"))
                status = message.get("status", "")
                sender = message.get("sender", "Server")
                text = message.get("text", "")
                receiver = message.get("receiver", "")

                if status == "private":
                    print(f"\n[Private] {sender}: {text}")

                elif status == "group":
                    print(f"\n[Group: {receiver}] {sender}: {text}")

                elif status == "error":
                    print(f"\n[Error] {text}")

                else:
                    print(f"\n{text}")

        except (OSError, json.JSONDecodeError):
            if not stop_event.is_set():
                print("\nConnection closed.")
            stop_event.set()
            break


def send_messages(client_socket, username, stop_event):
    """Dedicated thread for reading commands and sending messages."""
    print("\nCLASSCHAT COMMANDS")
    print("--------------------------------")
    print("/private username message")
    print("/create room_name")
    print("/join room_name")
    print("/group room_name message")
    print("/help")
    print("/quit")
    print("--------------------------------")

    while not stop_event.is_set():
        try:
            command = input(f"{username}> ").strip()

            if not command:
                continue

            if command == "/help":
                print("\nCLASSCHAT COMMANDS")
                print("--------------------------------")
                print("/private username message")
                print("/create room_name")
                print("/join room_name")
                print("/group room_name message")
                print("/help")
                print("/quit")
                print("--------------------------------")
                continue

            elif command.startswith("/private "):
                parts = command.split(maxsplit=2)

                if len(parts) < 3:
                    print("Usage: /private username message")
                    continue

                send_json(client_socket, {
                    "status": "private",
                    "sender": username,
                    "receiver": parts[1],
                    "text": parts[2]
                })

            elif command.startswith("/create "):
                parts = command.split(maxsplit=1)

                if len(parts) < 2:
                    print("Usage: /create room_name")
                    continue

                send_json(client_socket, {
                    "status": "create",
                    "sender": username,
                    "receiver": parts[1],
                    "text": ""
                })

            elif command.startswith("/join "):
                parts = command.split(maxsplit=1)

                if len(parts) < 2:
                    print("Usage: /join room_name")
                    continue

                send_json(client_socket, {
                    "status": "join",
                    "sender": username,
                    "receiver": parts[1],
                    "text": ""
                })

            elif command.startswith("/group "):
                parts = command.split(maxsplit=2)

                if len(parts) < 3:
                    print("Usage: /group room_name message")
                    continue

                send_json(client_socket, {
                    "status": "group",
                    "sender": username,
                    "receiver": parts[1],
                    "text": parts[2]
                })

            elif command == "/quit":
                send_json(client_socket, {
                    "status": "quit",
                    "sender": username,
                    "receiver": "SERVER",
                    "text": ""
                })

                stop_event.set()
                break

            else:
                print("Unknown command. Type /help to see available commands.")

        except (EOFError, OSError):
            stop_event.set()
            break

    try:
        client_socket.shutdown(socket.SHUT_WR)
    except OSError:
        pass


def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((HOST, PORT))
        print("Connected to ClassChat server!")

        username = input("Choose a username: ").strip()

        if not username:
            print("Username cannot be empty.")
            return

        send_json(client_socket, {
            "status": "register",
            "sender": username,
            "receiver": "SERVER",
            "text": ""
        })

        response = receive_registration_response(client_socket)

        if response.get("status") == "error":
            print(f"Registration failed: {response.get('text', '')}")
            return

        print(f"Welcome to ClassChat, {username}!")

        stop_event = threading.Event()

        # Thread 1: receives messages from the server.
        receive_thread = threading.Thread(
            target=receive_messages,
            args=(client_socket, stop_event)
        )

        # Thread 2: reads user input and sends messages.
        send_thread = threading.Thread(
            target=send_messages,
            args=(client_socket, username, stop_event)
        )

        receive_thread.start()
        send_thread.start()

        send_thread.join()
        receive_thread.join()

    except ConnectionRefusedError:
        print("Could not connect. Make sure the server is running.")

    except ConnectionError as error:
        print(error)

    finally:
        client_socket.close()
        print("Client closed.")


if __name__ == "__main__":
    main()
