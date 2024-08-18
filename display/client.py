from rich import print
import os
import sys
import zmq


class Client:
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def connect(self):
        self.socket.connect("tcp://localhost:5555")

    def draw_file(self, path):
        self.socket.send(str.encode(path))
        return self.socket.recv().decode("utf-8")


if __name__ == "__main__":
    path = sys.argv[1]
    client = Client()
    client.connect()
    client.draw_file(path)
