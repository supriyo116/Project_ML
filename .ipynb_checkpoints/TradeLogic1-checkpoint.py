import pandas as pd


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
    team_signal = SignalTeam(df_5m, df_30m)
    sideways_indicator = SidewaysDefender(df_5m)

    if sideways_indicator == -1:
        return 0  # Override with square-off signal in sideways market
    else:
        return team_signal
