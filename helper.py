from urlextract import URLExtract
extract = URLExtract()
from wordcloud import WordCloud
import pandas as pd
from collections import Counter
import emoji
import re
from pathlib import Path

# ---- Utilities ----
STOP_PATH = Path(__file__).with_name("stop_hinglish.txt")

def _read_stopwords():
    try:
        return STOP_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        # Fallback: empty stoplist if file missing
        return []

STOP_WORDS = set(w.strip() for w in _read_stopwords() if w.strip())

def _is_media_message(s: str) -> bool:
    # Matches "<Media omitted>" (any trailing whitespace/newline)
    return bool(re.fullmatch(r"\s*<Media omitted>\s*", s or ""))

def fetch_stats(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    # Ensure string for safe ops
    msg = df['message'].astype(str)

    # number of messages
    num_messages = df.shape[0]

    # total words
    words = []
    for m in msg:
        words.extend(m.split())

    # number of media messages (robust)
    num_media_messages = sum(_is_media_message(m) for m in msg)

    # number of links
    links = []
    for m in msg:
        links.extend(extract.find_urls(m))

    return num_messages, len(words), num_media_messages, len(links)

def most_busy_users(df):
    x = df['user'].value_counts().head()
    df2 = (df['user'].value_counts(normalize=True) * 100).round(2).reset_index().rename(
        columns={'index': 'name', 'user': 'percent'})
    return x, df2

# wordcloud
def create_wordcloud(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    temp = df[df['user'] != 'group_notification'].copy()

    # Drop media messages & NaN; force to string
    temp['message'] = temp['message'].astype(str)
    temp = temp[~temp['message'].apply(_is_media_message)]
    temp = temp[temp['message'].str.strip() != ""]

    def remove_stop_words(message: str) -> str:
        y = []
        # basic tokenization; you can add better cleaning later
        for word in message.lower().split():
            if word not in STOP_WORDS:
                y.append(word)
        return " ".join(y)

    wc = WordCloud(width=500, height=500, min_font_size=10, background_color='white')

    # Apply cleaning safely
    temp['message'] = temp['message'].apply(remove_stop_words)

    # Join all messages (guard empty)
    corpus = " ".join(temp['message'].dropna().tolist()) or "whatsapp chat"

    df_wc = wc.generate(corpus)
    return df_wc

# most common words
def most_common_words(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    temp = df[df['user'] != 'group_notification'].copy()
    temp['message'] = temp['message'].astype(str)
    temp = temp[~temp['message'].apply(_is_media_message)]

    words = []
    for message in temp['message']:
        for word in message.lower().split():
            if word and word not in STOP_WORDS:
                words.append(word)

    most_common_df = pd.DataFrame(Counter(words).most_common(20))
    return most_common_df

def emoji_helper(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]

    # Ensure string
    msg = df['message'].astype(str)

    # Build a simple emoji list robustly
    final_emoji_list = []
    for m in msg:
        for ch in m:
            if ch in emoji.EMOJI_DATA:
                final_emoji_list.append(ch)

    # Remove empty/skin-tone fragments if any stray through
    emojis_to_be_removed = ['', '🏻']
    final_emoji_list = [e for e in final_emoji_list if e not in emojis_to_be_removed]

    emoji_counts = Counter(final_emoji_list)
    emoji_df = pd.DataFrame(emoji_counts.most_common(), columns=['Emoji', 'Count'])
    return emoji_df

def monthly_timeline(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    timeline = df.groupby(['year', 'month_num', 'month'], as_index=False)['message'].count()
    # Build "time" as "Month-YYYY"
    timeline['time'] = timeline['month'] + "-" + timeline['year'].astype(str)
    return timeline

def daily_timeline(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    daily_timeline = df.groupby('only_date', as_index=False)['message'].count()
    return daily_timeline

def week_activity_map(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    return df['day_name'].value_counts()

def month_activity_map(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    return df['month'].value_counts()

def activity_heatmap(selected_user, df):
    if selected_user != 'Overall':
        df = df[df['user'] == selected_user]
    user_heatmap = df.pivot_table(
        index='day_name',
        columns='period',
        values='message',
        aggfunc='count'
    ).fillna(0)
    return user_heatmap
