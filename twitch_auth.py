from os import getenv

import requests
from dotenv import load_dotenv
from flask import Flask, redirect, request

app = Flask(__name__)

load_dotenv()

CLIENT_ID = getenv("mod_log_id")
CLIENT_SECRET = getenv("mod_log_secret")
REDIRECT_URL = "http://localhost:3000/callback"
SCOPES = "moderation:read moderator:read:banned_users moderator:read:chat_messages"


@app.route("/login")
def login():
    return redirect(
        "https://id.twitch.tv/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URL}"
        "&response_type=code"
        f"&scope={SCOPES}"
    )


@app.route("/callback")
def callback():
    code = request.args.get("code")
    token_r = requests.post(
        "https://id.twitch.tv/oauth2/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URL,
        },
    )

    data = token_r.json()
    print("\n === SEND THESE TO SPIDER ===")
    print(f"TWITCH_ACCESS_TOKEN = {data['access_token']}")
    print(f"TWITCH_REFRESH_TOKEN = {data['refresh_token']}")
    print("=====================================")
    return "Done! You can close this tab and stop the script."


if __name__ == "__main__":
    print("Visit http://localhost:3000/login in your browser!")
    app.run(port=3000)
