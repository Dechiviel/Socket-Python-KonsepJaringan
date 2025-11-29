**Project Overview**

This repository contains basic socket examples in Python demonstrating network communication using TCP protocols. The project aims to show how to build a server-client connection, multi-user ready, and send-recieve message.

**Included Files**
- `Server.py`: Server implementation. The server accepts connections and responds.
- `Client.py`: Client implementation that connects to the server.
- And some random experiment files

**Prerequisites**
- **Python**: Version 3.7+ recommended.

**Guide to Use**
- Copy this repository to your local.

- Start the server:
```
python Server.py <ip> <port>
```
- Start the client:
```
python Client.py <server_ip> <server_port>
```

**Usage Notes & Tips**
- Use `127.0.0.1` (localhost) for testing on the same machine.