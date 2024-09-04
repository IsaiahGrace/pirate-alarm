from rich import print
import json
import os
import sys
import zmq
import zmqNet


class DisplayClient:
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def connect(self):
        self.socket.connect(zmqNet.DISPLAY_SERVER_ADDR)

    def send_command(self, command):
        self.socket.send(str.encode(json.dumps(command)))
        response = json.loads(self.socket.recv().decode("utf-8"))
        if response["response"] == "exception":
            raise RuntimeError(response["name"], response["text"])

    def draw_icon(self, icon):
        return self.send_command({"command": "draw_icon", "icon": icon})

    def draw_image(self, relative_path):
        return self.send_command({"command": "draw_image", "relative_path": relative_path})

    def icon_bar_color(self, red, green, blue, alpha):
        return self.send_command({"command": "icon_bar_color", "r": red, "g": green, "b": blue, "a": alpha})

    def backlight(self):
        return self.send_command({"command": "backlight"})


if __name__ == "__main__":
    path = sys.argv[1]
    client = DisplayClient()
    client.connect()
    client.draw_image(path)
