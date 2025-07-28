import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
import pickle
import pathlib

# === Setup for OAuth ===
CLIENT_ID = "19168390529-vtbs40n42arn6dd19bavb81mk63rlus3.apps.googleusercontent.com"
CLIENT_SECRET = "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"
SCOPES = ['https://www.googleapis.com/auth/gmail.send']
REDIRECT_URI = "https://ghostvnx-email-campaign.streamlit.app"  # Replace with your actual deployed app link if different

TOKEN_FILE = "token.pkl"  # Stores the user's access token

# === Start Gmail Connection Flow ===
def login_to_gmail():
    st.subheader("📧 Connect Your Gmail")

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            credentials = pickle.load(token)

        if credentials and credentials.valid:
            st.success("✅ Gmail connected successfully.")
            return credentials

    if 'auth_url' not in st.session_state:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "redirect_uris": [REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        auth_url, _ = flow.authorization_url(prompt='consent')
        st.session_state.auth_url = auth_url
        st.session_state.flow = flow

    if 'code' not in st.experimental_get_query_params():
        st.markdown(f"[🔐 Click here to connect Gmail]({st.session_state.auth_url})")
        st.stop()
    else:
        query_params = st.experimental_get_query_params()
        code = query_params.get('code')[0]

        flow = st.session_state.flow
        flow.fetch_token(code=code)
        credentials = flow.credentials

        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(credentials, token)

        st.success("✅ Gmail connected successfully.")
        return credentials

# === Send Email ===
def send_email(credentials, to, subject, message):
    service = build('gmail', 'v1', credentials=credentials)

    from email.mime.text import MIMEText
    import base64

    msg = MIMEText(message)
    msg['to'] = to
    msg['from'] = "me"
    msg['subject'] = subject

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    body = {'raw': raw}

    send_result = service.users().messages().send(userId="me", body=body).execute()
    return send_result
