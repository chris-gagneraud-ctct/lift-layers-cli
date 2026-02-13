
HOST="localhost:8888"

def get_auth_token(url, username, password):
    import requests
    # url = f"http://{host}/api/mosaic/login"
    payload = {
        "username": username,
        "password": password
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        token = response.json().get("access_token")
        print(f"Authentication successful. Token: {token}")
        return token
    except requests.exceptions.RequestException as e:
        print(f"Authentication failed: {e} (using {username}/{password})")
        return None

import websocket
def websocket_client():
    # Binary payload: messagesenderbinary and messagehandlerbinary
    # JSON payload: messagesender and messagehandler
    mosaic_url = "ws://localhost:8888/api/mosaic/messagehandlerbinary/"
    extra_url = "Power/SetIgnitionLowTimeout/set_ignition_low_timeout_topic?access_token=D39YO4U7nUC-Ztb_bBybTw=="

    try:
        ws = websocket.create_connection(mosaic_url + extra_url, data={"access_token": "dev_token"})
        print(f"Connected to {mosaic_url}")
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
    auth_token = get_auth_token("http://localhost:8092/oauth/access_token", "", "")
