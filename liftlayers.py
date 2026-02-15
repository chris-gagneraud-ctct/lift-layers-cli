#!/usr/bin/env python

import argparse
import json
import logging
import random
import requests
import ssl
import sys
import urllib3
import websocket


# Web proxy settings
DEFAULT_HOST = "localhost:9443"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "Admin11@"

API_ENDPOINT = "/api/mosaic/"
LOGIN_ENDPOINT = API_ENDPOINT + "login"
LOGOUT_ENDPOINT = API_ENDPOINT + "logout/"
OAUTH_LOGIN_URLS_ENDPOINT = API_ENDPOINT + "oauthloginurls"
LIST_MESSAGES_ENDPOINT = API_ENDPOINT + "listmessages"
LIST_REQUESTS_ENDPOINT = API_ENDPOINT + "listrequests"
REQUEST_SENDER_ENDPOINT = API_ENDPOINT + "requestsender/"


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

    def __init__(self, host_port: str, username: str, password: str, verbose=False, dry_run=False):
        self.http_url = f"https://{host_port}"
        self.ws_url = f"wss://{host_port}"
        self.ws_namespace = "lift_layers"
        self.username = username
        self.password = password
        self.verbose = verbose or dry_run
        self.dry_run = dry_run
        self.http_client = None
        self.lift_layer_session_id = None

    # TODO: Allow login with username/password
    def login(self):
        if self.dry_run:
            print(f"Would log using OAuth link from {OAUTH_LOGIN_URLS_ENDPOINT}")
            return
        assert self.http_client is None
        self.http_client = HttpClient(self.http_url)
        response = self.http_client.get(OAUTH_LOGIN_URLS_ENDPOINT)
        response.raise_for_status()
        oauth_path = response.json()["end_points"][0]["path"]
        response = self.http_client.get(oauth_path)
        response.raise_for_status()
        if self.verbose:
            print("Logged in successfully using OAuth link")

    def logout(self):
        if self.dry_run:
            print(f"Would log out by calling {LOGOUT_ENDPOINT}")
            return
        assert self.http_client is not None
        response = self.http_client.get(LOGOUT_ENDPOINT)
        response.raise_for_status()
        self.http_client.close()
        self.http_client = None
        if self.verbose:
            print("Logged out successfully")

    def begin_session(self):
        assert self.lift_layer_session_id is None
        message = self._send_request("BeginLiftLayersCreationRequest", "begin_lift_layer_creation_server", {})
        if self.dry_run:
            self.lift_layer_session_id = "dummy-server-uuid"
        else:
            self.lift_layer_session_id = message["topic_identifier"]

    def end_session(self):
        assert self.lift_layer_session_id is not None
        self._send_request("TerminateLiftLayersCreationRequest", self.lift_layer_session_id, {})
        self.lift_layer_session_id = None

    def create_design(self, path: str):
        assert self.lift_layer_session_id is not None
        message = self._send_request("CreateLiftLayersDesignRequest", self.lift_layer_session_id, {"path": path})
        if self.dry_run:
            return
        error = message.get("error")
        if error != "eSuccess":
            raise Exception(f"CreateLiftLayersDesignRequest: error={error}")

    # surface_type can be "eCritical", "eCut" or "eFill"
    def load_design_surface(self, surface_type: str, design_path: str, surface_name: str):
        assert self.lift_layer_session_id is not None
        message = self._send_request("LoadSurfaceRequest", self.lift_layer_session_id, {
            "variant": surface_type,
            "surface_type": "DesignSurface",
            "surface": {
                "design": design_path,
                "surface": surface_name
            }
        })
        if self.dry_run:
            return
        error = message.get("error")
        if error != "eSuccess":
            raise Exception(f"LoadSurfaceRequest: error={error}")

    def load_quick_slope_surface(self, surface_type: str, heading: float, mainfall: float, cross_slope: float):
        assert self.lift_layer_session_id is not None
        message = self._send_request("LoadSurfaceRequest", self.lift_layer_session_id, {
            "variant": surface_type,
            "surface_type": "QuickSlopeSurface",
            "surface": {
                "heading": heading,
                "mainfall": mainfall,
                "cross_slope": cross_slope
            }
        })
        if self.dry_run:
            return
        error = message.get("error")
        if error != "eSuccess":
            raise Exception(f"LoadSurfaceRequest: error={error}")


    def unload_surface(self, surface_type: str):
        assert self.lift_layer_session_id is not None
        message = self._send_request("LoadSurfaceRequest", self.lift_layer_session_id, {
            "variant": surface_type,
            "surface_type": "NoSurfaceSelected",
            "surface": {}
        })
        if self.dry_run:
            return
        error = message.get("error")
        if error != "eSuccess":
            raise Exception(f"LoadSurfaceRequest: error={error}")

    def update_surface(self, surface_type: str, x: float, y: float, z: float, thickness: float):
        assert self.lift_layer_session_id is not None
        message = self._send_request("UpdateSurfaceLayersRequest", self.lift_layer_session_id, {
            "variant": surface_type,
            "reference_position": {
                "x": x,
                "y": y,
                "z": z
            },
            "layer_thickness": thickness
        })
        if self.dry_run:
            return
        success = message.get("success")
        if not success:
            raise Exception(f"UpdateSurfaceLayersRequest: success={success}")

    def preview_surface(self, x: float, y: float, z: float, heading: float):
        assert self.lift_layer_session_id is not None
        message = self._send_request("PreviewSurfacePointsRequest", self.lift_layer_session_id, {
            "preview_origin": {
                "x": x,
                "y": y,
                "z": z
            },
            "preview_heading": heading
        })
        if self.dry_run:
            return
        success = message.get("success")
        if not success:
            raise Exception(f"PreviewSurfacePointsRequest: success={success}")

    def _get_sender_endpoint(self, request: str, topic: str) -> str:
        return f"{self.ws_url}{REQUEST_SENDER_ENDPOINT}{self.ws_namespace}/{request}/{topic}"

    def _get_websocket(self, url: str) -> websocket.WebSocket:
        assert self.http_url is not None
        cookies = self.http_client.session.cookies.get_dict()
        cookie_header = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        ssl_options = {"cert_reqs": ssl.CERT_NONE}
        return websocket.create_connection(url, cookie=cookie_header, sslopt=ssl_options)

    def _send_request(self, request: str, topic: str, message: dict) -> dict:
        payload = json.dumps({
            "uuid": f"lift-layers-cli-{str(random.randint(100000, 999999))}",
            "request_type": "stream",
            "message": message
        })
        if self.verbose:
            print(f"-> [{request}/{topic}] {payload}")
        if self.dry_run:
            return {}
        assert self.http_client is not None
        url = self._get_sender_endpoint(request, topic)
        ws = self._get_websocket(url)
        ws.send(payload)
        payload = json.loads(ws.recv())
        if self.verbose:
            print(f"<- [{request}/{topic}] {payload}")
        return payload["message"]



if __name__ == "__main__":
    commands_help = """
Available commands:
  create_design <design_path>
  load_design_surface <surface_type> <design_path> <surface_name>
  load_quick_slope_surface <surface_type> <heading> <mainfall> <cross_slope>
  unload_surface <surface_type>
  update_surface <surface_type> <x> <y> <z> <thickness>
  preview_surface <x> <y> <z> <heading>
Where surface_type can be "eCritical", "eCut" or "eFill"
    """
    parser = argparse.ArgumentParser(
        description="Lift layer CLI",
        epilog=commands_help,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('-H', '--host', metavar='HOST:PORT',
                        help=f'Host and port (default to {DEFAULT_HOST})',
                        default=f"{DEFAULT_HOST}")
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help='Be verbose. Use -v to show Mosaic messages, -vv to also show WebSocket frames and HTTP requests.')
    parser.add_argument('-d', '--dry-run', action='store_true', default=False,
                        help='Do not execute commands, just print what would be done (implies -v)')
    parser.add_argument('command',
                        help='Command to execute')
    parser.add_argument('args', nargs=argparse.REMAINDER,
                        help='Arguments for the command')
    args = parser.parse_args()

    host = args.host
    function = None
    kwargs = {}
    if args.command == "create_design":
        if len(args.args) != 1:
            print("Usage: create_design <design_path>")
            sys.exit(1)
        function = LiftLayerClient.create_design
        kwargs["path"] = args.args[0]
    elif args.command == "load_design_surface":
        if len(args.args) != 3:
            print("Usage: load_design_surface <surface_type> <design_path> <surface_name>")
            sys.exit(1)
        function = LiftLayerClient.load_design_surface
        kwargs["surface_type"] = args.args[0]
        kwargs["design_path"] = args.args[1]
        kwargs["surface_name"] = args.args[2]
    elif args.command == "load_quick_slope_surface":
        if len(args.args) != 4:
            print("Usage: load_quick_slope_surface <surface_type> <heading> <mainfall> <cross_slope>")
            sys.exit(1)
        function = LiftLayerClient.load_quick_slope_surface
        kwargs["surface_type"] = args.args[0]
        kwargs["heading"] = float(args.args[1])
        kwargs["mainfall"] = float(args.args[2])
        kwargs["cross_slope"] = float(args.args[3])
    elif args.command == "unload_surface":
        if len(args.args) != 1:
            print("Usage: unload_surface <surface_type>")
            sys.exit(1)
        function = LiftLayerClient.unload_surface
        kwargs["surface_type"] = args.args[0]
    elif args.command == "update_surface":
        if len(args.args) != 5:
            print("Usage: update_surface <surface_type> <x> <y> <z> <thickness>")
            sys.exit(1)
        function = LiftLayerClient.update_surface
        kwargs["surface_type"] = args.args[0]
        kwargs["x"] = float(args.args[1])
        kwargs["y"] = float(args.args[2])
        kwargs["z"] = float(args.args[3])
        kwargs["thickness"] = float(args.args[4])
    elif args.command == "preview_surface":
        if len(args.args) != 4:
            print("Usage: preview_surface <x> <y> <z> <heading>")
            sys.exit(1)
        function = LiftLayerClient.preview_surface
        kwargs["x"] = float(args.args[0])
        kwargs["y"] = float(args.args[1])
        kwargs["z"] = float(args.args[2])
        kwargs["heading"] = float(args.args[3])
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    if args.verbose >= 2:
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger("urllib3").setLevel(logging.DEBUG)
        websocket.enableTrace(True)

    client = LiftLayerClient(DEFAULT_HOST, DEFAULT_USERNAME, DEFAULT_PASSWORD, verbose=args.verbose >= 1, dry_run=args.dry_run)
    client.login()
    client.begin_session()
    exit_code = 1
    try:
        function(client, **kwargs)
        exit_code = 0
    except Exception as e:
        print(f"Error executing request: {e}")
    finally:
        client.end_session()
        client.logout()
    sys.exit(exit_code)