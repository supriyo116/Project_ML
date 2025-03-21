import pandas as pd
from fyers_apiv3.FyersWebsocket import data_ws
import threading
import time


class livedata:
    def __init__(self, symbols):
        self.symbols = symbols
        self.is_running = False
        self.fyers = None
        self.thread = None

        # Load credentials from CSV
        config = pd.read_csv("cred.csv").iloc[0]
        self.access_token = config["access_token"]
        self.client_id = config["client_id"]

        # Data storage
        self.columns = ["timestamp", "symbol", "open", "high", "low", "close", "volume"]
        self.live_data = pd.DataFrame(columns=self.columns)

        # Store latest LTP as an instance attribute
        self.ltp = None

    def onmessage(self, message):
        if "ltp" in message:
            symbol = message.get("symbol", "unknown")
            ltp_value = message["ltp"]
            self.ltp = ltp_value
            print(f"Updated LTP for {symbol}: {ltp_value}")

    def onerror(self, message):
        print("Error:", message)

    def onclose(self, message):
        print("Connection closed:", message)

    def onopen(self):
        data_type = "SymbolUpdate"
        self.fyers.subscribe(symbols=self.symbols, data_type=data_type)
        self.fyers.keep_running()

    def start(self):
        if self.is_running:
            print("WebSocket is already running!")
            return

        self.fyers = data_ds = data_ws.FyersDataSocket(
            access_token=self.access_token,
            log_path="",
            litemode=True,
            write_to_file=False,
            reconnect=True,
            on_connect=self.onopen,
            on_close=self.onclose,
            on_error=self.onerror,
            on_message=self.onmessage,
            reconnect_retry=10
        )

        self.thread = threading.Thread(target=self.fyers.connect)
        self.thread.start()
        self.is_running = True
        print("✅ WebSocket started!")

    def stop(self):
        if not self.is_running:
            print("WebSocket is not running!")
            return

        self.fyers.disconnect()
        self.is_running = False
        print("⛔ WebSocket stopped!")
