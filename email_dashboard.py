import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import re

# === CONFIG ===
ARTIST_NAME = "Ghost VnX"
GENRE_KEYWORDS = ['drill', 'hip hop', 'rap', 'trap', 'uk drill']
CHRISTIAN_FILTER = ['christian hip hop', 'gospel', 'faith', 'jesus', 'church', 'ministry', 'worship', 'spiritual']
FOLLOW_UP_MINUTES = 10
DASHBOARD_PASSWORD = "GhostAccess123"

# === LOGIN ===
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    password = st.text_input("Enter Dashboard Password", type="password")
    if password == DASHBOARD_PASSWORD:
        st.session_state.authenticated = True
        st.experimental_rerun()
    else:
        st.stop()

# === APP HEADER ===
st.set_page_config(page_title="Ghost VnX Email Dashboard", layout="wide")
st.title("📬 Ghost VnX | Email Campaign Manager")

# === PROMPT + CUSTOM MESSAGE ===
st.subheader("🧠 Campaign Prompt + Email Template")
prompt = st.text_area("Enter prompt to guide how emails should sound (tone, length, keywords)", value="Make it professional but relaxed. Mention UK rap. Max 80 words.")

st.markdown("**Quick Prompts:**")
cols = st.columns(4)
preset_prompts = [
    "Make it formal and respectful",
    "Keep it short and hype (Gen Z tone)",
    "Be friendly, max 50 words",
    "Ask for feedback without pressure"
]
for i, p in enumerate(preset_prompts):
    if cols[i].button(p):
        prompt = p
        st.experimental_rerun()

custom_template = st.text_area("✍️ Base Email Message (use [Name], [Platform], [SubmissionLink])", height=200, value=
"""Hi [Name],

I'm Ghost VnX, an independent hip hop artist. I’d love for you to check out my new track — I believe it fits your curation on [Platform].

Here’s the link: [SubmissionLink]

Best,  
Ghost VnX
""")

uploaded_file = st.file_uploader("📂 Upload Your Curator or Contact CSV", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df = df.rename(columns=lambda x: x.strip())
    email_col = next((col for col in df.columns if 'email' in col.lower() or 'contact' in col.lower()), None)
    if not email_col:
        st.error("Could not find email/contact column.")
        st.stop()

    df = df.dropna(subset=[email_col])

    # === Filter Genre ===
    def genre_match(row):
        text = ' '.join([str(v).lower() for v in row.values])
        return any(g in text for g in GENRE_KEYWORDS)

    df['matched_genre'] = df.apply(genre_match, axis=1)
    genre_df = df[df['matched_genre'] == True].copy()

    def is_christian_only(row):
        text = ' '.join([str(v).lower() for v in row.values])
        return any(c in text for c in CHRISTIAN_FILTER)

    genre_df['christian_only'] = genre_df.apply(is_christian_only, axis=1)
    filtered_df = genre_df[genre_df['christian_only'] == False].copy()

    # === Detect Platform ===
    def detect_platform(row):
        if pd.notna(row.get('spotify')): return 'Spotify'
        if pd.notna(row.get('soundcloud')): return 'SoundCloud'
        if pd.notna(row.get('youtube')): return 'YouTube'
        if 'blog' in str(row.get('website', '')).lower(): return 'Blogger'
        if pd.notna(row.get('submission page')): return 'Submit Portal'
        return 'Unknown'

    filtered_df['platform'] = filtered_df.apply(detect_platform, axis=1)

    # === Personalize Emails ===
    def fill_template(row):
        name = row.get('title', 'there')
        platform = row.get('platform', 'your platform')
        submission = row.get('submission page', row.get('website', ''))

        message = custom_template
        message = re.sub(r'\[Name\]', str(name), message)
        message = re.sub(r'\[Platform\]', str(platform), message)
        message = re.sub(r'\[SubmissionLink\]', str(submission), message)
        return message

    filtered_df['email_preview'] = filtered_df.apply(fill_template, axis=1)
    filtered_df['sent_at'] = datetime.now()
    filtered_df['follow_up_due'] = datetime.now() + timedelta(minutes=FOLLOW_UP_MINUTES)
    filtered_df['status'] = 'Sent'

    # === Simulate Follow-Up Due ===
    now = datetime.now()
    filtered_df.loc[filtered_df['follow_up_due'] < now, 'status'] = 'Follow-up Due'

    # === METRICS ===
    total_uploaded = len(df)
    genre_matched = len(genre_df)
    excluded_christian = genre_df['christian_only'].sum()
    final_emails = len(filtered_df)
    follow_ups = (filtered_df['status'] == 'Follow-up Due').sum()

    st.subheader("📊 Campaign Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Uploaded", total_uploaded)
    c2.metric("Genre Matched", genre_matched)
    c3.metric("Christian Skipped", excluded_christian)
    c4.metric("Follow-ups Due", follow_ups)

    st.bar_chart(filtered_df['platform'].value_counts())

    st.subheader("📧 Email Previews (Personalized)")
    sample_count = st.slider("Preview how many?", 1, 10, 3)
    for i in range(min(sample_count, final_emails)):
        st.markdown(f"**To:** `{filtered_df.iloc[i][email_col]}`")
        st.code(filtered_df.iloc[i]['email_preview'], language='text')

    st.subheader("📋 Campaign Table")
    st.dataframe(filtered_df[[email_col, 'platform', 'status', 'email_preview']], use_container_width=True)

    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download Campaign Log CSV", csv, file_name="campaign_results.csv", mime='text/csv')
else:
    st.info("Upload your CSV above to begin.")
