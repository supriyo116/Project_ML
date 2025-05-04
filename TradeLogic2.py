import pandas as pd
import pickle
import pandas_ta as ta

with open("model.pkl", "rb") as f:
    azure_model = pickle.load(f)


def signal(df_5m: pd.DataFrame) -> int:
    """Uses the Azure ML model to predict the trade signal."""
    try:
        if df_5m.empty or df_5m.empty:
            return 0  # No data to process

        df_5m.ta.macd(append=True)
        df_5m.ta.rsi(append=True)
        df_5m.ta.stoch(append=True)
        df_5m.ta.bbands(append=True)
        df_5m.ta.supertrend(append=True)
        df_5m.ta.obv(append=True)

        # Combine both timeframes into a single feature set

        # Make prediction
        features = ["timestamp",
                             "open", "high", "low", "close", "volume",
                             "MACD_12_26_9", "RSI_14", "STOCHk_14_3_3",
                             "BBP_5_2.0", "SUPERTd_7_3.0", "OBV", "treasury_yield"
                             ]

        # Extract only the latest row for these features
        latest_features = df_5m[features].iloc[[-1]]

        # Predict using the Azure ML model
        prediction = azure_model.predict(latest_features)
        print(prediction)
        return int(prediction[0])



    except Exception as e:
        print("PredictTradeSignal Failure:", e)
        return 0  # Default to "hold" if an error occurs

