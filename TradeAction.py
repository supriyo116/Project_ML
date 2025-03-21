from fyers_apiv3 import fyersModel
import pandas as pd
from web_socket import livedata


class TradeManager:
    def __init__(self,symbol="MCX:CRUDEOILM25MARFUT", qty=1, mode="Manual", MaxLoss=-500, cred_file="cred.csv"):
        # Load credentials from CSV and initialize the API client
        config = pd.read_csv(cred_file)
        config = config.iloc[0].to_dict()
        self.client_id = config["client_id"]
        self.access_token = config["access_token"]
        self.api = fyersModel.FyersModel(client_id=self.client_id, token=self.access_token, is_async=False, log_path="")
        self.symbol = symbol
        self.qty = qty
        self.mode = mode
        self.MaxLoss = MaxLoss
        def display_trade(self):
            print(f"Symbol: {self.symbol}, Quantity: {self.qty}, Mode: {self.mode}, Max Loss: {self.MaxLoss}")

        # Initialize live data using the websocket
        self.ws = livedata(symbols=[symbol])
        self.ws.start()



        self.position = [0]
        self.SL_order = [0]

        # Initialize state: position and SL order.
        # Format: [position_status, order_id]
        # For example, [0] indicates no position, [1, order_id] for a long, [-1, order_id] for a short.

    def update_TSL(self, order_no, order_type, entry_price, LTP, step, initial_sl_long=20, initial_sl_short=15,
                   symbol='MCX:CRUDEOILM19AUG24'):
        try:
            if order_type == 1:  # Buy or long position
                if LTP > entry_price + step:
                    factor = int((LTP - entry_price) / step)
                    if factor != 0:
                        new_trigger_price = entry_price + factor * step - initial_sl_long
                        data = {
                            "id": order_no,
                            "type": 4,  # Stop-limit order
                            "stopPrice": new_trigger_price,  # New stop loss trigger price
                            "limitPrice": new_trigger_price - 0.5,  # New limit price
                            "symbol": symbol
                        }
                        ret = self.api.modify_order(data=data)
                        return ret['message']  # Return the status message from the response
            else:  # Sell or short position
                if LTP < entry_price - step:
                    factor = int((entry_price - LTP) / step)
                    if factor != 0:
                        new_trigger_price = entry_price - factor * step + initial_sl_short
                        data = {
                            "id": order_no,
                            "type": 4,  # Stop-limit order
                            "stopPrice": new_trigger_price,  # New stop loss trigger price
                            "limitPrice": new_trigger_price + 0.5,  # New limit price
                            "symbol": symbol
                        }
                        ret = self.api.modify_order(data=data)
                        return ret['message']  # Return the status message from the response
            return 'No update needed'
        except Exception as e:
            print("Update TSL Failure:", e)
            return 'Update TSL Failure'

    def buy(self, LTP, symbol, qty=10):
        try:
            # Place market buy order
            buy_order_data = {
                "symbol": symbol,
                "qty": qty,
                "type": 2,  # Market Order
                "side": 1,  # Buy
                "productType": "INTRADAY",
                "limitPrice": 0,
                "stopPrice": 0,
                "validity": "DAY",
                "disclosedQty": 0,
                "offlineOrder": False,
                "orderTag": "BuyOrder"
            }
            ret = self.api.place_order(data=buy_order_data)

            # Place SL-LMT sell order
            sl_order_data = {
                "symbol": symbol,
                "qty": qty,
                "type": 4,  # SL-LMT Order
                "side": -1,  # Sell
                "productType": "INTRADAY",
                "limitPrice": LTP - 20.5,
                "stopPrice": LTP - 20,
                "validity": "DAY",
                "disclosedQty": 0,
                "offlineOrder": False,
                "orderTag": "SLOrder"
            }
            ret1 = self.api.place_order(data=sl_order_data)

            if ret['s'] == 'ok' and ret1['s'] == 'ok':
                self.position = [1, ret["id"]]
                self.SL_order = [-1, ret1["id"]]
            else:
                print("Buy order failed:", ret, ret1)
                return "Buy order failed"
            return "Buy order placed"
        except Exception as e:
            print("Buy Failure:", e)
            return "Buy order failed"

    def sell(self, LTP, symbol, qty=10):
        try:
            # Place market sell order
            sell_order_data = {
                "symbol": symbol,
                "qty": qty,
                "type": 2,  # Market Order
                "side": -1,  # Sell
                "productType": "INTRADAY",
                "limitPrice": 0,
                "stopPrice": 0,
                "validity": "DAY",
                "disclosedQty": 0,
                "offlineOrder": False,
                "orderTag": "SellOrder"
            }
            ret = self.api.place_order(data=sell_order_data)

            # Place SL-LMT buy order
            sl_order_data = {
                "symbol": symbol,
                "qty": qty,
                "type": 4,  # SL-LMT Order
                "side": 1,  # Buy
                "productType": "INTRADAY",
                "limitPrice": LTP + 15.5,
                "stopPrice": LTP + 15,
                "validity": "DAY",
                "disclosedQty": 0,
                "offlineOrder": False,
                "orderTag": "SLOrder"
            }
            ret1 = self.api.place_order(data=sl_order_data)

            if ret['s'] == 'ok' and ret1['s'] == 'ok':
                self.position = [1, ret["id"]]
                self.SL_order = [-1, ret1["id"]]
            else:
                print("Sell order failed:", ret, ret1)
                return "Sell order failed"
            return "Sell order placed"
        except Exception as e:
            print("Sell Failure:", e)
            return "Sell order failed"

    def squareoff(self, symbol, qty=10):
        try:
            # Check if there is no position to square off
            if self.position[0] == 0:
                self.SL_order = [0]
                self.position = [0]
                return "Nothing to square off"
            cancel_data = {"id": self.SL_order[1]} if self.SL_order[1] != 0 else None
            if cancel_data:
                cancel_response = self.api.cancel_order(data=cancel_data)
                if cancel_response['s'] == "ok":
                    exit_data = {"id": self.position[1]} if self.position[1] != 0 else None
                    if exit_data:
                        exit_response = self.api.exit_positions(data=exit_data)
                        if exit_response['s'] == "ok":
                            self.position = [0]
                            self.SL_order = [0]
                            return "Position squared off"
                        else:
                            return "Failed to exit position"
                else:
                    return "Failed to cancel stop-loss order"
        except Exception as e:
            print("Squareoff Failure:", e)
            return "Squareoff failed"

    def fetchltp(self):
        """Fetch the latest price from the live data websocket."""
        return self.ws.ltp

    def longentry(self, decision_variable, MaxLoss, symbol=None):
        if symbol is None:
            symbol = self.symbol
        try:
            if self.position[0] == 0:  # No open position
                current_ltp = self.fetchltp()
                self.buy(current_ltp, symbol)  # Execute the buy order

                while True:
                    try:
                        # Continuously get updated LTP
                        current_ltp = self.fetchltp()

                        # Check SL order status and update TSL continuously if pending
                        sl_status = self.get_order_status(self.SL_order[1])
                        if sl_status == "6":  # Pending
                            position_status = self.get_order_status(self.position[1])
                            self.update_TSL(self.position[1], 1, position_status["avgprc"], current_ltp, step=4, symbol=symbol)
                        elif sl_status == "2":  # Filled: Stop Loss hit
                            self.position = [0]
                            self.SL_order = [0]
                            break

                        # Check the MTM loss limit continuously
                        if self.mtm() < MaxLoss:
                            self.squareoff(symbol)
                            print("MTM Loss limit reached. Exiting trade.")
                            break

                        # Check if the decision is still favorable for a long trade
                        if decision_variable != 1:
                            self.squareoff(symbol)
                            break

                    except Exception as e:
                        print("Error inside longentry loop:", e)
                        break
        except Exception as e:
            print("Error in longentry function:", e)


    def shortentry(self, decision_variable, MaxLoss, symbol=None):
        if symbol is None:
            symbol = self.symbol
        try:
            if self.position[0] == 0:  # No open position
                current_ltp = self.fetchltp()
                self.sell(current_ltp, symbol)  # Execute the sell order

                while True:
                    try:
                        # Continuously get updated LTP
                        current_ltp = self.fetchltp()

                        # Continuously check and update the SL order
                        sl_status = self.get_order_status(self.SL_order[1])
                        if sl_status == "6":  # Pending
                            position_status = self.get_order_status(self.position[1])
                            self.update_TSL(self.position[1], -1, position_status["avgprc"], current_ltp, step=4, symbol=symbol)
                        elif sl_status == "2":  # Filled: Stop Loss hit
                            self.position = [0]
                            self.SL_order = [0]
                            break

                        # Check the MTM loss limit continuously
                        if self.mtm() < MaxLoss:
                            self.squareoff(symbol)
                            print("MTM Loss limit reached. Exiting trade.")
                            break

                        # Check if the decision is still favorable for a short trade
                        if decision_variable != -1:
                            self.squareoff(symbol)
                            break

                    except Exception as e:
                        print("Error inside shortentry loop:", e)
                        break
        except Exception as e:
            print("Error in shortentry function:", e)

    def mtm(self):
        try:
            response = self.api.positions()
            if response.get('s') != 'ok' or 'overall' not in response:
                print("Invalid response or 'overall' field missing")
                return 0
            overall = response['overall']
            total_mtm = float(overall.get('pl_total', 0))
            return total_mtm
        except Exception as e:
            print(f"Unexpected error in MTM calculation: {e}")
            return 0

    def get_order_status(self, order_id):
        response = self.api.orderbook()
        for order in response.get('orderBook', []):
            if order['id'] == order_id:
                return order['status']
        return None

    def emergency_exit(self):
        print("🚨 Emergency Exit Triggered! Closing all positions...")

        data = {}  # Empty data to close all positions
        exit_response = self.api.exit_positions(data=data)

        if exit_response.get('s') == "ok":
            print("✅ Emergency exit successful. All positions are closed.")

        elif exit_response.get('message') == "Looks like you have no open positions." :
            print("✅ No open positions, hence closing session")

        else:
            print("❌ Failed to close all positions. Response:", exit_response)






# # Example: Place a buy order
# result = tm.buy(LTP=5858.0, symbol='MCX:CRUDEOILM19AUG24', qty=10)
# print(result)

# # Example: Check order status (if you have an order_id)
# status = tm.get_order_status(tm.position[1])
# print("Order Status:", status)

# # Example: Square off your position
# squareoff_result = tm.squareoff(symbol='MCX:CRUDEOILM19AUG24', qty=10)
# print(squareoff_result)

# # Example: Get MTM value
# current_mtm = tm.mtm()
# print("MTM:", current_mtm)

