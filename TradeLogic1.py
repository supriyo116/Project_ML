import pandas as pd
import pickle
import pandas_ta as ta

with open("model.pkl", "rb") as f:
    azure_model = pickle.load(f)


def PredictTradeSignal(df_30m: pd.DataFrame) -> int:
    """Uses the Azure ML model to predict the trade signal."""
    try:
        if df_30m.empty or df_30m.empty:
            return 0  # No data to process

        # Add MACD columns (default: fast=12, slow=26, signal=9)
        df_30m.ta.macd(append=True)

        # Add CCI column (default period=20)
        df_30m.ta.cci(append=True)

        # Add CMF column (default period=20)
        df_30m.ta.cmf(append=True)

        # Combine both timeframes into a single feature set

        # Make prediction
        features = ["timestamp",
            "open", "high", "low", "close", "volume",
            "MACD_12_26_9", "MACDh_12_26_9", "MACDs_12_26_9",
            "CCI_14_0.015", "CMF_20"
        ]

        # Extract only the latest row for these features
        latest_features = df_30m[features].iloc[[-1]]

        # Predict using the Azure ML model
        prediction = azure_model.predict(latest_features)
        return int(prediction[0])



    except Exception as e:
        print("PredictTradeSignal Failure:", e)
        return 0  # Default to "hold" if an error occurs


def SignalTeam(three_df: pd.DataFrame, thirty_df: pd.DataFrame) -> int:
    try:
        if three_df.empty or thirty_df.empty:
            return 0  # No data to check

        latest_three_signal = three_df['SUPERTd_12_2.0'].iloc[-1]
        latest_thirty_signal = thirty_df['SUPERTd_7_3.0'].iloc[-1]

        if latest_three_signal == 1 and latest_thirty_signal == 1:
            return 1  # Buy signal
        elif latest_three_signal == -1 and latest_thirty_signal == -1:
            return -1  # Sell signal
        else:
            return 0  # Exit or no clear signal
    except Exception as e:
        print("SignalTeam Failure:", e)
        return 0  # Return 0 to indicate failure or no signal


def SidewaysDefender(three_df: pd.DataFrame) -> int:
    try:
        if three_df.empty or len(three_df) < 5:
            return 1  # Not enough data to check sideways condition

        latest_five_values = three_df['SUPERT_12_2.0'].iloc[-5:]
        if all(val == latest_five_values.iloc[0] for val in latest_five_values):
            return -1  # Sideways: all values are the same
        else:
            return 1  # Not sideways
    except Exception as e:
        print("SidewaysDefender Failure:", e)
        return 1  # Default to not sideways if an error occurs


def signal(df_5m: pd.DataFrame, df_30m: pd.DataFrame) -> int:

    # Obtain predictions
    ml_signal = PredictTradeSignal(df_30m)  # ML-based prediction (using latest row of df_30m)
    team_signal = SignalTeam(df_5m, df_30m)  # Rule-based signal
    sideways_indicator = SidewaysDefender(df_5m)  # Sideways market indicator

    print("ml_signal:", ml_signal,"team_signal:", team_signal,"sideways_indicator:", sideways_indicator)

    # If market is sideways, override any signal with a square-off (0)
    if sideways_indicator == -1:
        return 0

    # Assign weights to each component (adjust based on further market conditions)
    ml_weight = 0.4
    team_weight = 0.6

    # Compute the combined signal. For example, if ml_signal is 1 and team_signal is -1,
    # the weighted sum is 0.6*1 + 0.4*(-1) = 0.2, which would yield a hold (0).
    combined_signal = ml_weight * ml_signal + team_weight * team_signal

    # Apply thresholds to determine final decision.
    if combined_signal > 0.33:
        return 1  # Buy signal
    elif combined_signal < -0.33:
        return -1  # Sell signal
    else:
        return 0  # Hold/Exit signal

