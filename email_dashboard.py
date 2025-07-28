import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# === CONFIG ===
ARTIST_NAME = "Ghost VnX"
GENRE_KEYWORDS = ['drill', 'hip hop', 'rap', 'trap', 'uk drill']
FOLLOW_UP_MINUTES = 10

# === LOAD FILE ===
st.title("🎧 Music Curator Email System")
uploaded_file = st.file_uploader("Upload Your Curator CSV File", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df = df.rename(columns=lambda x: x.strip())  # Remove leading/trailing spaces

    # === FIND EMAIL COLUMN ===
    email_col = next((col for col in df.columns if 'contact' in col.lower() or 'email' in col.lower()), None)
    if not email_col:
        st.error("❌ Could not find a column with email/contact info. Please make sure your CSV has a 'Contact' or 'Email' column.")
        st.stop()

    df = df.dropna(subset=[email_col])  # Remove rows with empty emails

    # === GENRE FILTERING ===
    def genre_match(row):
        text = ' '.join([str(v).lower() for v in row.values])
        return any(g in text for g in GENRE_KEYWORDS)

    df['matched_genre'] = df.apply(genre_match, axis=1)
    genre_df = df[df['matched_genre'] == True].copy()

    # === PLATFORM DETECTION ===
    def detect_platform(row):
        if pd.notna(row.get('spotify')): return 'Spotify'
        if pd.notna(row.get('soundcloud')): return 'SoundCloud'
        if pd.notna(row.get('youtube')): return 'YouTube'
        if 'blog' in str(row.get('website', '')).lower(): return 'Blogger'
        if pd.notna(row.get('submission page')): return 'Submit Portal'
        return 'Unknown'

    genre_df['platform'] = genre_df.apply(detect_platform, axis=1)

    # === EMAIL DRAFTING ===
    def create_email(row):
        name = row.get('title', 'there')
        platform = row.get('platform', 'your platform')
        submission = row.get('submission page', row.get('website', ''))

        email = f"""Subject: New Hip Hop/Drill Track Submission 🎵

Hi {name},

I’m Ghost VnX, an independent hip hop/drill artist, reaching out because I believe my latest track could resonate well with your curation on {platform}.

Here’s the submission/info link:
{submission}

Thanks in advance — looking forward to hearing your thoughts.

Best,  
Ghost VnX
"""
        return email

    genre_df['email_preview'] = genre_df.apply(create_email, axis=1)
    genre_df['sent_at'] = datetime.now()
    genre_df['follow_up_due'] = datetime.now() + timedelta(minutes=FOLLOW_UP_MINUTES)

    # === DASHBOARD DISPLAY ===
    st.success(f"{len(genre_df)} matched contacts filtered by genre.")
    st.subheader("📊 Platform Breakdown")
    st.bar_chart(genre_df['platform'].value_counts())

    st.subheader("📧 Email Draft Previews")
    sample_count = st.slider("How many samples to view?", 1, 10, 3)
    for i in range(sample_count):
        st.markdown(f"### Draft to: `{genre_df.iloc[i][email_col]}`")
        st.code(genre_df.iloc[i]['email_preview'], language='text')

    # === DOWNLOAD DRAFTS ===
    st.subheader("📁 Download Results")
    csv_download = genre_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Draft Results CSV", csv_download, file_name="email_drafts_preview.csv", mime='text/csv')

else:
    st.warning("👆 Please upload your CSV to begin.")
