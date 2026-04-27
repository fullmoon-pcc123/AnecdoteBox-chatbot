import streamlit as st
import pandas as pd
import os
import random
from google import genai

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="AnecdoteBox",
    page_icon="icon.png", # Your baby girl icon
    layout="centered"
)

# ---------------------------------------------------------
# 2. CUSTOM CSS
# ---------------------------------------------------------
st.markdown("""
<style>
/* --- MAIN BACKGROUND --- */
.stApp {
    background-color: #FDFBF7;
    background-image: linear-gradient(180deg, #FDFBF7 0%, #F5F0E6 100%);
    color: #4A4A4A;
    font-family: 'Helvetica Neue', sans-serif;
}

/* --- LOGO TEXT STYLING (Mimics your image) --- */
.logo-container {
    text-align: center;
    margin-top: 20px;
    margin-bottom: 5px;
}
.logo-text {
    font-family: 'Arial Rounded MT Bold', 'Helvetica Rounded', 'Arial', sans-serif;
    font-size: 50px; /* Big and bold */
    font-weight: 900;
    color: #1A1F2C; /* Dark Navy/Black from your logo */
    letter-spacing: -1px;
    line-height: 1.1;
}
.logo-accent {
    color: #E64833; /* The Red/Orange color for 'Box' */
}
.logo-tagline {
    font-family: 'Helvetica Neue', sans-serif;
    font-size: 16px;
    color: #666;
    margin-top: 0px;
    margin-bottom: 30px;
    font-weight: 500;
    text-align: center;
}

/* --- CHAT WITH SAMU HEADER --- */
.samu-header {
    background: white;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    border: 1px solid #EFEFEF;
    margin-bottom: 25px;
}
.samu-title {
    font-family: 'Georgia', serif;
    font-size: 26px; 
    font-weight: 800;
    color: #C4622D;
    margin: 0;
}
.samu-subtitle {
    font-size: 15px;
    color: #8B5E3C;
    font-style: italic;
    margin-top: 5px;
}

/* --- STORY CARDS --- */
.story-card {
    background: white;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    transition: transform 0.2s;
    border: 1px solid #F0F0F0;
    margin-bottom: 15px;
    height: 100%;
}
.story-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 16px rgba(196,98,45,0.15);
}
.story-img {
    width: 100%;
    height: 160px;
    object-fit: cover;
}
.card-content {
    padding: 15px;
}
.story-title {
    color: #C4622D;
    font-weight: bold;
    font-size: 16px;
    margin-bottom: 8px;
    line-height: 1.3;
    height: 42px; 
    overflow: hidden;
}
.story-summary {
    color: #666;
    font-size: 13px;
    line-height: 1.4;
    margin-bottom: 12px;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    height: 55px;
}
.read-btn {
    display: block;
    width: 100%;
    text-align: center;
    text-decoration: none;
    background-color: #C4622D;
    color: white !important;
    padding: 8px 0;
    border-radius: 8px;
    font-size: 13px;
    font-weight: bold;
}
.read-btn:hover {
    background-color: #A04D22;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. DATA LOADING
# ---------------------------------------------------------
@st.cache_data
def load_data():
    csv_file = "Chatbox Master file.csv"
    
    if not os.path.exists(csv_file):
        st.error(f"❌ File not found: {csv_file}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(csv_file)
    except Exception:
        try:
            df = pd.read_csv(csv_file, encoding='latin1')
        except:
            return pd.DataFrame()

    df = df.fillna("")
    df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
    return df

df = load_data()

# ---------------------------------------------------------
# 4. GEMINI API SETUP
# ---------------------------------------------------------
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=GEMINI_API_KEY)
except:
    client = None

MODEL = "gemini-flash-latest"

# ---------------------------------------------------------
# 5. HELPER FUNCTIONS
# ---------------------------------------------------------
import requests
from bs4 import BeautifulSoup

def clean_html(html):
    return BeautifulSoup(html, "html.parser").get_text()

def get_story_from_api(query):
    url = f"https://anecdotebox.com/wp-json/wp/v2/posts?search={query}"
    response = requests.get(url)
    data = response.json()

    if data:
        title = data[0]["title"]["rendered"]
        content = clean_html(data[0]["content"]["rendered"])
        link = data[0]["link"]

        return f"{title}\n\n{content[:1200]}\n\nRead more: {link}"
    
    return None
def render_story_card(row):
    title = row.get('title', 'Untitled')
    full_summary = str(row.get('summary', ''))
    
    # Crisp summary (90 chars)
    if len(full_summary) > 90:
        summary = full_summary[:90].rsplit(' ', 1)[0] + "..."
    else:
        summary = full_summary

    link = row.get('url', '#')
    img_url = row.get('featured_image', '')
    
    # Fallback Image
    if not img_url or str(img_url).lower() in ['nan', '', 'none']:
        img_url = "https://images.unsplash.com/photo-1519681393798-3828fb4090bb?auto=format&fit=crop&w=400&q=80"
    
    html = f"""
    <div class="story-card">
        <a href="{link}" target="_blank">
            <img src="{img_url}" class="story-img" onerror="this.src='https://images.unsplash.com/photo-1519681393798-3828fb4090bb?auto=format&fit=crop&w=400&q=80'">
        </a>
        <div class="card-content">
            <div class="story-title">{title}</div>
            <div class="story-summary">{summary}</div>
            <a href="{link}" target="_blank" class="read-btn">Read Story ➜</a>
        </div>
    </div>
    """
    return html

def find_stories(query, n=3):
    if df.empty: return []
    q = query.lower()
    scores = []
    
    for _, row in df.iterrows():
        txt = f"{row.get('title','')} {row.get('tags','')} {row.get('summary','')} {row.get('content','')}".lower()
        score = 0
        for w in q.split():
            if w in txt: score += 1
        if score > 0: scores.append((score, row))
            
    scores.sort(key=lambda x: x[0], reverse=True)
    results = [row for _, row in scores[:n]]
    
    if not results:
        return df.sample(n=min(n, len(df))).to_dict('records'), False
    
    return results, True

# ---------------------------------------------------------
# 6. HEADER & MAIN UI
# ---------------------------------------------------------

# --- A. THE LOGO & TAGLINE (Text Based) ---
st.markdown("""
<div class="logo-container">
    <div class="logo-text">
        Anecdote<span class="logo-accent">Box</span>
    </div>
    <div class="logo-tagline">
        Stories to make your day
    </div>
</div>
""", unsafe_allow_html=True)

# --- B. THE SAMU HEADER ---
st.markdown("""
<div class="samu-header">
    <div class="samu-title">Chat with Samu</div>
    <div class="samu-subtitle">Your Friendly Guide to the AnecdoteBox</div>
</div>
""", unsafe_allow_html=True)


# --- C. TABS & LOGIC ---
tab1, tab2 = st.tabs(["🏠 Fresh Picks", "💬 Chat with Samu"])

# TAB 1: HOME
with tab1:
    if not df.empty:
        st.markdown("### ✨ Featured Stories")
        sample_size = min(3, len(df))
        random_stories = df.sample(n=sample_size)
        c1, c2, c3 = st.columns(3)
        for i, (_, row) in enumerate(random_stories.iterrows()):
            with [c1, c2, c3][i]:
                st.markdown(render_story_card(row), unsafe_allow_html=True)
    else:
        st.info("No stories found.")

# TAB 2: CHAT
with tab2:
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hello! I am Samu. How are you feeling today?"}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if "html" in msg and msg["html"]:
                st.markdown(msg["html"], unsafe_allow_html=True)

    if prompt := st.chat_input("Ex: I want a story about hope..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)

        stories_list = []
        is_exact = False

# 🔌 Step 1: Try API first
api_story = get_story_from_api(prompt)

if api_story:
    stories_list = [{
        "title": "From AnecdoteBox",
        "summary": api_story
    }]
    is_exact = True

# 🔁 Step 2: fallback to Excel
elif not df.empty:
    found_data, is_exact = find_stories(prompt)
    if isinstance(found_data, list): 
        stories_list = found_data
    else: 
        stories_list = found_data


# ✅ UI BLOCK (must be OUTSIDE)
context_text = ""
cards_html = ""

if stories_list:
    cards_html = "<div style='display:flex; gap:10px; overflow-x:auto; padding-bottom:15px;'>"
    for s in stories_list:
        title = s.get('title') if isinstance(s, dict) else s['title']
        summary = s.get('summary') if isinstance(s, dict) else s['summary']
        context_text += f"- {title}: {summary}\n"
        cards_html += f"<div style='min-width:220px; max-width:220px;'>{render_story_card(s)}</div>"
    cards_html += "</div>"
    instructions = "Recommend these specific stories." if is_exact else "I couldn't find an exact match, but here are some nice random stories."

        full_prompt = f"""
        You are Samu. User: "{prompt}"
        Stories: {context_text}
        Instruction: {instructions}
        Keep it short.
        """

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    if client:
                        resp = client.models.generate_content(model=MODEL, contents=full_prompt)
                        reply = resp.text
                    else:
                        reply = "API Key error."
                    
                    st.write(reply)
                    if cards_html: st.markdown(cards_html, unsafe_allow_html=True)
                    st.session_state.messages.append({"role": "assistant", "content": reply, "html": cards_html})
                except Exception as e:
                    st.error(str(e))
