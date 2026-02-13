
















class WebSocketClient:
    def __init__(self, host: str, port: int, access_token: str):
        self.base_url = f"ws://{host}:{port}"
        self.access_token = access_token
        self.ws = None

    def connect(self, endpoint: str):
        headers = [
            f"Authorization: Bearer {self.access_token}",
        ]
        ssl_options = {"cert_reqs": ssl.CERT_NONE}
        self.ws = websocket.create_connection(self.base_url + endpoint, header=headers, sslopt=ssl_options)

    def send(self, message):
        self.ws.send_bytes(message)

    def receive(self):
        return self.ws.recv()

    def close(self):
        self.ws.close()


def create_session(client):
    topic = "begin_lift_layer_creation_server"


# "mows_oauth", "mows_form" or None
login_method = "mows_form"

# allowanyuser, allowyamswebui, allowdevuser, allowplatformapi

def old_stuff():
    http_client = None
    access_token = ""
    if login_method == "mows_oauth":
        print("Using mows_oauth login")
        http_client = HttpClient(MOWS_OAUTH_HOST, MOWS_OAUTH_PORT)
        response = http_client.get(MOWS_OAUTH_ACCESS_TOKEN_ENDPOINT)
        response.raise_for_status()
        access_token = response.json()["access_token"]
        print(response.cookies)
        print(http_client.session.cookies)
        http_client.close()
    elif login_method == "mows_form":
        print("Using mows_form login")
        http_client = HttpClient(MOWS_API_HOST, MOWS_API_PORT)
        response = http_client.post(LOGIN_ENDPOINT, data={"username": "admin", "password": "Admin11@"})
        response.raise_for_status()
        access_token = response.json()["access_token"]
        http_client.close()

    print(f"Using access token='{access_token}'")

    if login_method == "mows_oauth":
        http_client = HttpClient(MOWS_API_HOST, MOWS_API_PORT)
    params = {
        "access_token": access_token
    }
    headers = {
        # To please the server.
        # Search for "YamsAuthenticator: Rejecting authorization request. TLS Connection required." in MosaicOverWS project
        "X-Forwarded-Proto": "https://"
    }
    response = http_client.get("/api/mosaic/listmessages", params=params, headers=headers)
    response.raise_for_status()
    print("Messages:")
    for message in response.json():
        print(" -", message["full_name"])
    response = http_client.get("/api/mosaic/listrequests?access_token=" + access_token)
    for message in response.json():
        print(" -", message["request"]["full_name"], message["response"]["full_name"])


    http_client.close()

    # # BeginLiftLayersCreationRequest
    # ws_client = WebSocketClient(MOWS_API_HOST, MOWS_API_PORT, access_token)
    # ws_client.connect("/api/mosaic/listmessages")
    # ws_client.connect("requestsender/lift_layers/BeginLiftLayersCreationRequest/my_topic")
    # builder = flatbuffers.Builder(1024)
    # BeginLiftLayersCreationRequest.Start(builder)
    # root = BeginLiftLayersCreationRequest.End(builder)
    # builder.Finish(root)
    # payload = builder.Output()
    # print(type(payload), len(payload), payload)
    # ws_client.send(b"{}")
    # print(ws_client.receive())
    # # ws_client.connect("requesthandler/lift_layers/BeginLiftLayersCreationRequest/my_topic")