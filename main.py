import json
import logging
import requests
import ssl
import websocket


HOST = "localhost"
PORT = 9443
USERNAME = "admin"
PASSWORD = "Admin11@"

# Enabling this will print all HTTP requests and responses
DEBUG_REQUESTS = False

API_ENDPOINT = "/api/mosaic/"
UI_ENDPOINT = API_ENDPOINT + "ui/"
LOGIN_ENDPOINT = API_ENDPOINT + "login"
LOGOUT_ENDPOINT = API_ENDPOINT + "logout/"
OAUTH_LOGIN_URLS_ENDPOINT = API_ENDPOINT + "oauthloginurls"
LIST_MESSAGES_ENDPOINT = API_ENDPOINT + "listmessages"
LIST_REQUESTS_ENDPOINT = API_ENDPOINT + "listrequests"
REQUEST_SENDER_ENDPOINT = API_ENDPOINT + "requestsender/"


if DEBUG_REQUESTS:
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.DEBUG)
    websocket.enableTrace(True)


class HttpClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.verify = False  # Accept self-signed certificates

    def get(self, endpoint: str, params=None, headers=None) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, params=params, headers=headers)
        return response

    def post(self, endpoint: str, data=None, json=None, headers=None) -> requests.Response:
        url = f"{self.base_url}{endpoint}"
        response = self.session.post(url, data=data, json=json, headers=headers)
        return response

    def close(self):
        self.session.close()


class LiftLayerClient:

    def __init__(self, host: str, port: int, username: str, password: str):
        self.http_url = f"https://{host}:{port}"
        self.ws_url = f"wss://{host}:{port}"
        self.ws_namespace = "lift_layers"
        self.username = username
        self.password = password
        self.http_client = None
        self.lift_layer_session_id = None

    def login(self):
        assert self.http_client is None
        self.http_client = HttpClient(self.http_url)
        response = self.http_client.get(OAUTH_LOGIN_URLS_ENDPOINT)
        response.raise_for_status()
        oauth_path = response.json()["end_points"][0]["path"]
        response = self.http_client.get(oauth_path)
        response.raise_for_status()
        print("Logged in successfully using OAuth link")

    def logout(self):
        assert self.http_client is not None
        response = self.http_client.get(LOGOUT_ENDPOINT)
        response.raise_for_status()
        self.http_client.close()
        self.http_client = None
        print("Logged out successfully")

    def begin_session(self):
        assert self.lift_layer_session_id is None
        message = self._send_request("BeginLiftLayersCreationRequest", "begin_lift_layer_creation_server", {})
        self.lift_layer_session_id = message["topic_identifier"]

    def end_session(self):
        assert self.lift_layer_session_id is not None
        self._send_request("TerminateLiftLayersCreationRequest", self.lift_layer_session_id, {})
        self.lift_layer_session_id = None

    def create_design(self, path: str):
        assert self.lift_layer_session_id is not None
        message = self._send_request("CreateLiftLayersDesignRequest", self.lift_layer_session_id, {"path": path})
        error = message.get("error")
        if error != "eSuccess":
            print(f"ERROR: {error}")

    # surface_type can be "eCritical", "eCut" or "eFill"
    def load_design_surface(self, surface_type: str, design_path: str, surface_name: str):
        pass

    def load_quick_slope_surface(self, surface_type: str, heading: float, mainfall: float, cross_slope: str):
        pass

    def unload_surface(self, surface_type: str):
        pass

    def update_surface(self, surface_type: str, position: str, thickness: float):
        pass

    def preview_surface(self):
        pass

    def _get_sender_endpoint(self, request: str, topic: str) -> str:
        return f"{self.ws_url}{REQUEST_SENDER_ENDPOINT}{self.ws_namespace}/{request}/{topic}"

    def _get_websocket(self, url: str) -> websocket.WebSocket:
        assert self.http_url is not None
        cookies = self.http_client.session.cookies.get_dict()
        cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        ssl_options = {"cert_reqs": ssl.CERT_NONE}
        return websocket.create_connection(url, cookie=cookie_header, sslopt=ssl_options)

    def _send_request(self, request: str, topic: str, message: dict) -> dict:
        assert self.http_client is not None
        url = self._get_sender_endpoint(request, topic)
        ws = self._get_websocket(url)
        payload = json.dumps({
            "uuid": "123e4567-e89b-12d3-a456-426614174003",
            "request_type": "stream",
            "message": message
        })
        print(f"-> [{request}/{topic}] {payload}")
        ws.send(payload)
        payload = json.loads(ws.recv())
        print(f"<- [{request}/{topic}] {payload}")
        return payload["message"]

def main():
    client = LiftLayerClient(HOST, PORT, USERNAME, PASSWORD)
    client.login()
    client.begin_session()
    client.create_design("/path/to/design")
    client.end_session()
    client.logout()

if __name__ == "__main__":
    main()
