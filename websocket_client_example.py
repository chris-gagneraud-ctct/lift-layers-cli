import websocket

# You may need to install the websocket-client package:
# pip install websocket-client

def websocket_client():
    ws_url = "wss://echo.websocket.events"
    try:
        ws = websocket.create_connection(ws_url)
        print(f"Connected to {ws_url}")
        message = "Hello WebSocket!"
        ws.send(message)
        print(f"Sent: {message}")
        response = ws.recv()
        print(f"Received: {response}")
        ws.close()
        print("Connection closed.")
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    websocket_client()
