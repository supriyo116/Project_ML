import pandas as pd
import hashlib
import requests
from fyers_apiv3 import fyersModel

# Load credentials from cred.csv
config_df = pd.read_csv("cred.csv")
config = config_df.iloc[0].to_dict()

client_id = config["client_id"]
secret_key = config["secret_key"]
redirect_uri = config["redirect_uri"]
response_type = config["response_type"]
state = config["state"]
pin = config["pin"]


def get_authorization_code():
    """Generates and returns the authorization code"""
    session = fyersModel.SessionModel(
        client_id=client_id,
        secret_key=secret_key,
        redirect_uri=redirect_uri,
        response_type=response_type
    )

    response = session.generate_authcode()
    return response


def get_access_token(auth_code, login_type="authorization_code"):
    """
    Fetches and saves the access token to cred.csv.

    login_type: "authorization_code" (default) or "refresh_token"
    """
    if login_type == "authorization_code":
        session = fyersModel.SessionModel(
            client_id=client_id,
            secret_key=secret_key,


            redirect_uri=redirect_uri,
            response_type=response_type,
            grant_type="authorization_code"
        )
        session.set_token(auth_code)
        response = session.generate_token()

    elif login_type == "refresh_token":
        # Hash app_id + app_secret
        combined = f"{client_id}:{secret_key}"
        sha256_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()

        # Prepare payload
        url = "https://api-t1.fyers.in/api/v3/validate-refresh-token"
        headers = {"Content-Type": "application/json"}
        payload = {
            "grant_type": "refresh_token",
            "appIdHash": sha256_hash,
            "refresh_token": auth_code,
            "pin": pin
        }

        # Send request
        response = requests.post(url, headers=headers, json=payload).json()

    else:
        raise ValueError("Invalid login_type. Use 'authorization_code' or 'refresh_token'.")

    if "access_token" in response:
        access_token = response["access_token"]
        refresh_token = response.get("refresh_token", auth_code)  # Keep the same refresh_token if not provided

        # Update credentials in DataFrame
        config_df.loc[0, "access_token"] = access_token
        config_df.loc[0, "refresh_token"] = refresh_token

        # Save back to CSV
        config_df.to_csv("cred.csv", index=False)

        print("✅ Access Token saved successfully in cred.csv")
        print("🔄 Refresh Token saved (valid for 15 days)")
        return access_token


    else:
        print("⚠️ Refresh token failed. Switching to authorization code method.")
        auth_code = input("🔑 Please enter a new authorization code: ")
        # Call the function again but RETURN its result to the calleD
        return get_access_token(auth_code, login_type="authorization_code")


if __name__ == "__main__":
    mode = input("Select login mode: 1️⃣ Authorization Code | 2️⃣ Refresh Token (1/2): ").strip()

    if mode == "1":
        auth_code = get_authorization_code()
        print(f"🔗 Open this link in your browser and authorize: {auth_code}")
        auth_code_input = input("🔑 Enter the authorization code: ")
        get_access_token(auth_code_input, login_type="authorization_code")

    elif mode == "2":
        refresh_token = config.get("refresh_token")
        if not refresh_token:
            print("⚠️ No refresh token found in cred.csv. Use authorization code login first.")
        else:
            get_access_token(refresh_token, login_type="refresh_token")

    else:
        print("❌ Invalid selection. Please restart and enter 1 or 2.")
