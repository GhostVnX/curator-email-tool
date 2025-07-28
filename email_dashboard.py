import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# === CONFIG ===
ARTIST_NAME = "Ghost VnX"
GENRE_KEYWORDS = ['drill', 'hip hop', 'rap', 'trap', 'uk drill']
CHRISTIAN_FILTER = ['christian hip hop', 'gospel', 'faith', 'jesus', 'church', 'ministry', 'worship', 'spiritual']
FOLLOW_UP_MINUTES = 10

st.set_page_config(page_title="Ghost VnX Email Dashboard", layout="wide")
st.title("📬 Ghost VnX | Curator Email Dashboard")

uploaded_file = st.file_uploader("Upload Your Curator CSV File", type=['csv'])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df = df.rename(columns=lambda x: x.strip())

    # === Detect Email Column ===
    email_col = next((col for col in df.columns if 'contact' in col.lower() or 'email' in col.lower()), None)
    if not email_col:
        st.error("❌ Could not find an email/contact column.")
        st.stop()

    df = df.dropna(subset=[email_col])  # Drop rows with missing email

    # === Genre Filter ===
    def genre_match(row):
        text = ' '.join([str(v).lower() for v in row.values])
        return any(g in text for g in GENRE_KEYWORDS)

    df['matched_genre'] = df.apply(genre_match, axis=1)
    genre_df = df[df['matched_genre'] == True].copy()

    # === Exclude Christian-only Curators ===
    def is_christian_only(row):
        text = ' '.join([str(v).lower() for v in row.values])
        return any(c in text for c in CHRISTIAN_FILTER)

    genre_df['christian_only'] = genre_df.apply(is_christian_only, axis=1)
    filtered_df = genre_df[genre_df['christian_only'] == False].copy()

    # === Platform Detection ===
    def detect_platform(row):
        if pd.notna(row.get('spotify')): return 'Spotify'
        if pd.notna(row.get('soundcloud')): return 'SoundCloud'
        if pd.notna(row.get('youtube')): return 'YouTube'
        if 'blog' in str(row.get('website', '')).lower(): return 'Blogger'
        if pd.notna(row.get('submission page')): return 'Submit Portal'
        return 'Unknown'

    filtered_df['platform'] = filtered_df.apply(detect_platform, axis=1)

    # === Email Generation ===
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

    filtered_df['email_preview'] = filtered_df.apply(create_email, axis=1)
    filtered_df['sent_at'] = datetime.now()
    filtered_df['follow_up_due'] = datetime.now() + timedelta(minutes=FOLLOW_UP_MINUTES)

    # === METRICS ===
    total_uploaded = len(df)
    genre_matched = len(genre_df)
    excluded_christian = genre_df['christian_only'].sum()
    final_emails = len(filtered_df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📥 Total Uploaded", total_uploaded)
    col2.metric("🎯 Matched by Genre", genre_matched)
    col3.metric("❌ Christian-Only Excluded", excluded_christian)
    col4.metric("✅ Final Emails Prepared", final_emails)

    # === VISUAL CHART ===
    st.subheader("📊 Platform Breakdown")
    st.bar_chart(filtered_df['platform'].value_counts())

    # === EMAIL PREVIEWS ===
    st.subheader("📧 Sample Email Previews")
    sample_count = st.slider("How many to preview?", 1, 10, 3)
    for i in range(min(sample_count, final_emails)):
        st.markdown(f"**To:** `{filtered_df.iloc[i][email_col]}`")
        st.code(filtered_df.iloc[i]['email_preview'], language='text')

    # === FULL TABLE ===
    st.subheader("📋 Final Processed Table")
    st.dataframe(filtered_df[[email_col, 'platform', 'email_preview']], use_container_width=True)

    # === DOWNLOAD FINAL RESULT ===
    st.subheader("⬇️ Download Filtered Results")
    download = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", download, file_name="filtered_email_results.csv", mime='text/csv')

else:
    st.info("📂 Please upload your curator list CSV to begin.")

