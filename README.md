
# ClassChat - TCP Chat Application

## Project Overview

ClassChat is a multi-client chat application developed in Python using TCP sockets and multithreading.

The application allows multiple users to connect to a central server, register unique usernames, exchange private messages, and communicate through group chat rooms.

This project was developed for CS 350 as a semester project focused on network programming, socket communication, and concurrent client handling.

## Features

- TCP client-server communication
- Multiple simultaneous client connections
- Unique username registration
- Duplicate username prevention
- Private one-to-one messaging
- Group chat room creation
- Joining existing chat rooms
- Group messaging
- Simultaneous message sending and receiving
- JSON-based message formatting
- Client disconnection and cleanup

## Technologies Used

- Python
- TCP/IP sockets
- Socket programming
- Multithreading
- JSON
- Git and GitHub

## Project Structure

```text
classchat-tcp-chat/
│
├── server.py       # Handles client connections and message routing
├── client.py       # Client application
├── README.md       # Project documentation
├── .gitignore      # Excludes unnecessary files
└── .venv/          # Local Python virtual environment
```

## Requirements

- Python 3.9 or later
- Terminal or command-line interface
- Git (optional, for version control)

## Installation

Clone the repository:

```bash
git clone https://github.com/quansahbrittany/classchat-tcp-chat.git
```

Navigate into the project directory:

```bash
cd classchat-tcp-chat
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate the virtual environment on macOS:

```bash
source .venv/bin/activate
```

## Running the Application

### 1. Start the server

Open a Terminal window and run:

```bash
python server.py
```

The server listens on:

```text
127.0.0.1:5050
```

### 2. Start a client

Open another Terminal window and run:

```bash
python client.py
```

Choose a unique username when prompted.

### 3. Connect additional clients

Open additional Terminal windows and run the client again.

Each connected user must register with a unique username.

## Available Commands

| Command | Description |
|---|---|
| `/private username message` | Send a private message |
| `/create room_name` | Create a group chat room |
| `/join room_name` | Join an existing room |
| `/group room_name message` | Send a group message |
| `/help` | Display available commands |
| `/quit` | Disconnect from ClassChat |

## Testing

The following features have been manually tested using multiple client Terminal sessions:

- Client-server connection
- Multiple client connections
- Username registration
- Duplicate username prevention
- Private messaging
- Group room creation
- Joining group rooms
- Group messaging
- Client disconnection
- Username reuse after disconnection

## System Architecture

ClassChat follows a centralized client-server architecture.

Clients establish TCP connections with the server. The server manages connected users, maintains group room membership, and routes messages to the appropriate recipients.

Separate threads allow the server to handle multiple clients and allow clients to receive incoming messages while users are typing.

## Limitations

- The current implementation is designed for local testing.
- Messages are not stored permanently.
- Communication is not encrypted.
- The application currently uses a command-line interface.

## Author

Brittany Quansah

Cybersecurity & Computer Science  
Radford University

## Course

CS 350 - Fall 2026

Semester Project: ClassChat
