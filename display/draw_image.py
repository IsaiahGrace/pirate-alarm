from rich import print
import os
import sys
import zmq


def main(args):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:5555")

    path = os.path.abspath(args[1])
    assert os.path.exists(path)
    socket.send(str.encode(path))
    print(socket.recv().decode("utf-8"))


if __name__ == "__main__":
    main(sys.argv)
