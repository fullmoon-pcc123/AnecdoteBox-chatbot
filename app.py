import streamlit as st
import pandas as pd
from google import genai

# PAGE CONFIG
st.set_page_config(
    page_title="AnecdoteBox Chatbot",
    page_icon="📖",
    layout="centered"
)

# CUSTOM CSS
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #F5E6D0 0%, #FDF6EC 100%);
    font-family: 'Segoe UI', sans-serif;
}
.main-header {
    background: linear-gradient(135deg, #C4622D, #8B5E3C);
    padding: 20px;
    border-radius: 15px;
    color: white;
    text-align: center;
    margin-bottom: 20px;
}
.bot-message {
    background: #FEF3E2;
    border: 1px solid #E0C9A6;
    border-radius: 4px 16px 16px 16px;
    padding: 12px 16px;
    margin: 8px 0;
    font-family: Georgia, serif;
    color: #2C2C2C;
    font-size: 15px;
    line-height: 1.6;
}
.user-message {
    background: #C4622D;
    border-radius: 16px 4px 16px 16px;
    padding: 12px 16px;
    margin: 8px 0;
    color: white;
    text-align: right;
    font-size: 15px;
}
.story-card {
    background: white;
    border: 1px solid #E0C9A6;
    border-radius: 12px;
    padding: 14px;
    margin: 8px 0;
    box-shadow: 0 2px 8px rgba(196,98,45,0.08);
}
</style>
""", unsafe_allow_html=True)


# LOAD DATA
@st.cache_data
def load_data():
    df = pd.read_csv("anecdotebox_final.csv")
    df = df.fillna("")
    return df

df = load_data()


# SETUP GEMINI
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL = "gemini-2.0-flash"


# FIND RELEVANT STORIES
def find_stories(query, n=3):
    query_lower = query.lower()
    scores = []

    for _, row in df.iterrows():
        score = 0
        tags = str(row.get("tags", "")).lower()
        title = str(row.get("title", "")).lower()
        summary = str(row.get("summary", "")).lower()
        category = str(row.get("category", "")).lower()

        for word in query_lower.split():
            if word in tags:
                score += 3
            if word in title:
                score += 2
            if word in summary:
                score += 1
            if "stories" in category:
                score += 1

        scores.append((score, row))

    scores.sort(key=lambda x: x[0], reverse=True)
    return [row for score, row in scores[:n] if score > 0]


# GENERATE AI RESPONSE
def get_response(user_input, stories):

    story_context = ""
    for i, s in enumerate(stories):
        story_context += f"""
Story {i+1}:
Title: {s['title']}
Category: {s['category']}
Summary: {s['summary']}
Tags: {s['tags']}
URL: {s['url']}
"""

    prompt = f"""
You are the AnecdoteBox storyteller, warm and friendly.

User asked: {user_input}

Available stories:
{story_context}

Respond warmly and recommend relevant stories.
End with a gentle question.
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
        return response.text.strip()

    except Exception:
        return "I am having a little trouble finding stories right now. Please try again."


# HEADER
st.markdown("""
<div class="main-header">
<h2>📖 AnecdoteBox</h2>
<p>Your Personal Storyteller</p>
</div>
""", unsafe_allow_html=True)


# CHAT HISTORY
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "bot",
            "text": "Hello! I am the AnecdoteBox storyteller. What kind of story speaks to you today?"
        }
    ]


# DISPLAY MESSAGES
for msg in st.session_state.messages:

    if msg["role"] == "bot":
        st.markdown(
            f'<div class="bot-message">{msg["text"]}</div>',
            unsafe_allow_html=True
        )

    else:
        st.markdown(
            f'<div class="user-message">{msg["text"]}</div>',
            unsafe_allow_html=True
        )


# HANDLE INPUT
def process_input(user_input):

    if not user_input.strip():
        return

    st.session_state.messages.append({
        "role": "user",
        "text": user_input
    })

    stories = find_stories(user_input)
    response = get_response(user_input, stories)

    st.session_state.messages.append({
        "role": "bot",
        "text": response
    })

    st.rerun()


user_input = st.chat_input("Ask for a story or mood...")
if user_input:
    process_input(user_input)


# FOOTER
st.markdown("""
<div style='text-align:center;color:#bbb;font-size:12px;margin-top:20px'>
Powered by AnecdoteBox
</div>
""", unsafe_allow_html=True)

