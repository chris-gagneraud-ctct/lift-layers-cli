import json
import logging
import requests
import ssl
import websocket


WEB_PROXY_HTTP_URL = "https://localhost:9443"
DUPLO_URL = "http://localhost:8888"
# Pick a server
SERVER_URL = WEB_PROXY_HTTP_URL
# If False, the script will use the form login.
# If True, it will use the "Login with MosaicOverWSDevAuthenticator" link.
LOGIN_WITH_OAUTH_LINK = True
# Enabling this will print all HTTP requests and responses
DEBUG_REQUESTS = True

API_ENDPOINT = "/api/mosaic/"
UI_ENDPOINT = API_ENDPOINT + "ui/"
LOGIN_ENDPOINT = API_ENDPOINT + "login"
LOGOUT_ENDPOINT = API_ENDPOINT + "logout/"
OAUTH_LOGIN_URLS_ENDPOINT = API_ENDPOINT + "oauthloginurls"
LIST_MESSAGES_ENDPOINT = API_ENDPOINT + "listmessages"
LIST_REQUESTS_ENDPOINT = API_ENDPOINT + "listrequests"
REQUEST_SENDER_ENDPOINT = API_ENDPOINT + "requestsender/"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin11@"


if DEBUG_REQUESTS:
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.DEBUG)
    websocket.enableTrace(True)


class HttpClient:
    def __init__(self, base_url: str):
        print("Using base URL:", base_url)
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

def get_dev_oauth_path(http_client: HttpClient) -> str:
    response = http_client.get(OAUTH_LOGIN_URLS_ENDPOINT)
    response.raise_for_status()
    print("Available OAuth login endpoints:")
    for endpoint in response.json()["end_points"]:
        path = endpoint["path"]
        description = endpoint["description"]
        print(f" - {description}:\n   {path}")
    return response.json()["end_points"][0]["path"]  # Just return the first one for now

def login_with_form(http_client: HttpClient, username: str, password: str) -> str:
    response = http_client.post(LOGIN_ENDPOINT, data={"username": username, "password": password})
    response.raise_for_status()
    print("Logged in successfully using form login")
    return response.json()["access_token"]

def login_with_oauth_link(http_client: HttpClient, oauth_path: str) -> None:
    response = http_client.get(oauth_path)
    response.raise_for_status()
    print("Logged in successfully using OAuth link")
    return None

def logout(http_client: HttpClient):
    response = http_client.get(LOGOUT_ENDPOINT)
    response.raise_for_status()
    print("Logged out successfully")

def list_messages(http_client: HttpClient, access_token: str):
    params = {}
    headers = {}
    if access_token:
        params["access_token"] = access_token
    response = http_client.get(LIST_MESSAGES_ENDPOINT, params=params, headers=headers)
    response.raise_for_status()
    print("Messages:")
    for message in response.json():
        print(" -", message["full_name"])

def list_requests(http_client: HttpClient, access_token: str):
    params = {}
    headers = {}
    if access_token:
        params["access_token"] = access_token
    response = http_client.get(LIST_REQUESTS_ENDPOINT, params=params, headers=headers)
    response.raise_for_status()
    for message in response.json():
        print(" -", message["request"]["full_name"], message["response"]["full_name"])

def get_cookie_header(session):
    cookies = session.cookies.get_dict()
    cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
    return {"Cookie": cookie_header}

def lift_layer_begin_session(http_client: HttpClient):
    url = (WEB_PROXY_HTTP_URL.replace("http", "ws") +
           REQUEST_SENDER_ENDPOINT +
           "lift_layers/BeginLiftLayersCreationRequest/begin_lift_layer_creation_server")
    cookies = http_client.session.cookies.get_dict()
    cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
    ssl_options = {"cert_reqs": ssl.CERT_NONE}
    ws = websocket.create_connection(url, cookie=cookie_header, sslopt=ssl_options)
    payload = json.dumps({
        "uuid": "123e4567-e89b-12d3-a456-426614174002",
        "request_type": "stream",
        "message": {}
    })
    print(f"Sending lift layer begin session request: {payload}")
    ws.send(payload)
    payload = json.loads(ws.recv())
    print(f"Received lift layer begin session response: {payload}")
    return payload["message"]["topic_identifier"]

def lift_layer_end_session(http_client: HttpClient, session_id: str):
    url = (WEB_PROXY_HTTP_URL.replace("http", "ws") +
           REQUEST_SENDER_ENDPOINT +
           f"lift_layers/TerminateLiftLayersCreationRequest/{session_id}")
    cookies = http_client.session.cookies.get_dict()
    cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
    ssl_options = {"cert_reqs": ssl.CERT_NONE}
    ws = websocket.create_connection(url, cookie=cookie_header, sslopt=ssl_options)
    payload = json.dumps({
        "uuid": "123e4567-e89b-12d3-a456-426614174003",
        "request_type": "stream",
        "message": {}
    })
    print(f"Sending lift layer end session request: {payload}")
    ws.send(payload)
    payload = json.loads(ws.recv())
    print(f"Received lift layer end session response: {payload}")



def main():
    client = HttpClient(SERVER_URL)
    if LOGIN_WITH_OAUTH_LINK:
        oauth_path = get_dev_oauth_path(client)
        login_with_oauth_link(client, oauth_path)
        token = None # Session cookie will be used for authentication
    else:
        token = login_with_form(client, ADMIN_USERNAME, ADMIN_PASSWORD)
    # list_messages(client, token)
    # list_requests(client, token)
    session_id = lift_layer_begin_session(client)
    print("Lift layer session ID:", session_id)
    lift_layer_end_session(client, session_id)
    logout(client)


if __name__ == "__main__":
    main()
