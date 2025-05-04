from fyers_apiv3 import fyersModel
import pandas as pd
import datetime
import pandas_ta as ta

config = pd.read_csv("cred.csv")
config = config.iloc[0].to_dict()
# Credentials
client_id = config["client_id"]
access_token = config["access_token"]

fyers = fyersModel.FyersModel(client_id=client_id, is_async=False, token=access_token, log_path="")

now = datetime.datetime.now().timestamp()
threedaysago = datetime.datetime.now() - datetime.timedelta(days=3)
threedaysago = threedaysago.timestamp()


def fetch_historical_data(symbol, resolution, ATR, mult):
    requirement = {
        "symbol": symbol,
        "resolution": resolution,
        "date_format": 0,
        "range_from": str(int(threedaysago)),
        "range_to": str(int(now)),
        "cont_flag": 1
    }
    data = fyers.history(data=requirement)

    if data['s'] == 'ok':
        df = pd.DataFrame(data['candles'], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')+pd.DateOffset(hours=5, minutes=30)  # Convert to datetime
        # df.ta.supertrend(length=ATR, multiplier=mult, append=True)
        return df
    else:
        print("Error fetching data:", data)
        return None





