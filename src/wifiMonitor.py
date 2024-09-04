from rich import print
from rich.logging import RichHandler
import displayClient
import logging
import socket
import time
import icons

logger = logging.getLogger(__name__)


class WifiMonitor:
    def __init__(self):
        self.display = displayClient.DisplayClient()
        self.display.connect()

    def test_internet(self, host="8.8.8.8", port=53, timeout=3):
        """
        Source: https://stackoverflow.com/questions/3764291/how-can-i-see-if-theres-an-available-and-active-network-connection-in-python
        Host: 8.8.8.8 (google-public-dns-a.google.com)
        OpenPort: 53/tcp
        Service: domain (DNS/TCP)
        """
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except socket.error as ex:
            logger.warning(ex)
            return False

    def initial_connection(self):
        while not self.test_internet():
            logger.debug("Waiting for connection...")
            self.display.draw_icon(icons.WIFI_DISCONNECTED)
            time.sleep(1)
            self.display.draw_icon(icons.WIFI_WAIT)
            time.sleep(1)
        logger.debug("Initial connection")

    def run(self):
        self.initial_connection()
        while True:
            if self.test_internet():
                logger.debug("Connected")
                self.display.draw_icon(icons.WIFI_CONNECTED)
                while self.test_internet():
                    time.sleep(60)
            else:
                logger.debug("Disconnected")
                self.display.draw_icon(icons.WIFI_DISCONNECTED)
                time.sleep(10)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    monitor = WifiMonitor()
    monitor.run()
