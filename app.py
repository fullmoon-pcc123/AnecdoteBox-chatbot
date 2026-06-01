import streamlit as st
import pandas as pd
import os
import requests
import time
import base64
from bs4 import BeautifulSoup
from openai import OpenAI

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION & SOCIAL METADATA
# ---------------------------------------------------------
st.set_page_config(
    page_title="AnecdoteBox",
    page_icon="https://anecdotebox.com/wp-content/uploads/2024/09/cropped-favicon-32x32.png", 
    layout="centered"
)

# ---------------------------------------------------------
# 2. CUSTOM CSS (RESTORED TO YOUR ORIGINAL BEAUTIFUL DESIGN)
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

/* --- LOGO TEXT STYLING --- */
.logo-container {
    text-align: center;
    margin-top: 20px;
    margin-bottom: 5px;
}
.logo-text {
    font-family: 'Arial Rounded MT Bold', 'Helvetica Rounded', 'Arial', sans-serif;
    font-size: 50px; 
    font-weight: 900;
    color: #1A1F2C; 
    letter-spacing: -1px;
    line-height: 1.1;
}
.logo-accent { color: #E64833; }
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

/* --- STORY CARDS (FIXED IMAGE SIZE) --- */
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
.story-card:hover { transform: translateY(-3px); }
.story-img {
    width: 100%;
    height: 160px; /* FORCES IMAGE TO BE UNIFORM */
    object-fit: cover;
}
.card-content { padding: 15px; }
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
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. HELPER FUNCTIONS & LOGIC
# ---------------------------------------------------------
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except:
    client = None

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

@st.cache_data
def load_data():
    csv_file = "Chatbox Master file.csv"
    if not os.path.exists(csv_file): return pd.DataFrame()
    try:
        df = pd.read_csv(csv_file)
    except:
        df = pd.read_csv(csv_file, encoding='latin1')
    df = df.fillna("")
    df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
    return df

df = load_data()

def clean_html(html):
    return BeautifulSoup(html, "html.parser").get_text()

def extract_keywords(query):
    """Uses AI to distill search terms for high reliability"""
    if not client: return query
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "Extract 1-2 core keywords from the user prompt. Output ONLY the keywords. Example: 'Show me stories about emojis' -> 'emojis'"},
                      {"role": "user", "content": query}],
            max_tokens=10
        )
        return resp.choices[0].message.content.strip()
    except: return query

def get_stories_from_website(query=None, limit=3):
    """Fetches Live Website Stories. If query is None, gets absolute latest."""
    t = int(time.time()) # Cache buster
    try:
        if not query or any(w in query.lower() for w in ["latest", "new", "recent", "fresh"]):
            url = f"https://anecdotebox.com/wp-json/wp/v2/posts?per_page={limit}&_embed&t={t}"
        else:
            clean_q = extract_keywords(query)
            url = f"https://anecdotebox.com/wp-json/wp/v2/posts?search={clean_q}&per_page={limit}&_embed&t={t}"
            
        response = requests.get(url, timeout=10)
        data = response.json()
        results = []
        if isinstance(data, list) and len(data) > 0:
            for post in data:
                img = ""
                if "_embedded" in post and "wp:featuredmedia" in post["_embedded"]:
                    img = post["_embedded"]["wp:featuredmedia"][0]["source_url"]
                results.append({
                    "title": post["title"]["rendered"],
                    "summary": clean_html(post["content"]["rendered"])[:200],
                    "url": post["link"],
                    "featured_image": img
                })
            return results
    except: pass
    return []

def find_stories_in_excel(query, n=3):
    if df.empty: return []
    clean_q = extract_keywords(query).lower()
    scores = []
    for _, row in df.iterrows():
        txt = f"{row.get('title','')} {row.get('tags','')} {row.get('summary','')}".lower()
        score = sum(1 for w in clean_q.split() if w in txt)
        if score > 0: scores.append((score, row.to_dict()))
    scores.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scores[:n]] if scores else df.sample(n=min(n, len(df))).to_dict('records')

def render_story_card(row):
    title = row.get('title', 'Untitled')
    summary = row.get('summary', '')[:90] + "..."
    link = row.get('url', row.get('link', '#'))
    img_url = row.get('featured_image', "https://images.unsplash.com/photo-1519681393798-3828fb4090bb?w=400")
    
    return f"""
    <div class="story-card">
        <a href="{link}" target="_blank">
            <img src="{img_url}" class="story-img">
        </a>
        <div class="card-content">
            <div class="story-title">{title}</div>
            <div class="story-summary">{summary}</div>
            <a href="{link}" target="_blank" class="read-btn">Read Story ➜</a>
        </div>
    </div>
    """

# ---------------------------------------------------------
# 4. BRANDING SECTION (LOGO)
# ---------------------------------------------------------
logo_file = "logo.png"
if os.path.exists(logo_file):
    logo_base64 = get_base64_of_bin_file(logo_file)
    st.markdown(f"""
        <div class="logo-container">
            <img src="data:image/png;base64,{logo_base64}" width="250">
            <div class="logo-tagline">Stories to make your day</div>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <div class="logo-container">
            <div class="logo-text">Anecdote<span class="logo-accent">Box</span></div>
            <div class="logo-tagline">Stories to make your day</div>
        </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. TABS & INTERFACE
# ---------------------------------------------------------
tab1, tab2 = st.tabs(["🏠 Fresh Picks", "💬 Chat with Samu"])

# --- TAB 1: FRESH PICKS (WEBSITE FIRST) ---
with tab1:
    st.markdown("### ✨ Featured Stories")
    # Priority 1: Website
    featured = get_stories_from_website(limit=3)
    
    # Priority 2: Excel Fallback
    if not featured and not df.empty:
        featured = df.sample(n=min(3, len(df))).to_dict('records')

    if featured:
        cols = st.columns(3)
        for i, row in enumerate(featured):
            with cols[i % 3]: st.markdown(render_story_card(row), unsafe_allow_html=True)
    else:
        st.info("No stories found.")

# --- TAB 2: CHAT WITH SAMU ---
with tab2:
    st.markdown("""
    <div class="samu-header">
        <div class="samu-title">Chat with Samu</div>
        <div class="samu-subtitle">Your Friendly Guide to the AnecdoteBox</div>
    </div>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hello! I am Samu. How can I help you today?"}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if "html" in msg: st.markdown(msg["html"], unsafe_allow_html=True)

    if prompt := st.chat_input("Ex: Show me stories about emojis..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching the box..."):
                # Search Logic
                res = get_stories_from_website(prompt)
                source = "website"
                if not res:
                    res = find_stories_in_excel(prompt)
                    source = "local collection"

                # Build Card Carousel
                cards_html = "<div style='display:flex; gap:10px; overflow-x:auto; padding-bottom:15px;'>"
                context = ""
                for s in res:
                    context += f"Title: {s['title']}\n"
                    cards_html += f"<div style='min-width:220px;'>{render_story_card(s)}</div>"
                cards_html += "</div>"

                # AI Narration
                try:
                    if client:
                        chat = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "system", "content": "You are Samu, a warm storyteller. Be friendly and brief (2 sentences)."},
                                      {"role": "user", "content": f"User asked: {prompt}. Found in {source}: {context}"}]
                        )
                        reply = chat.choices[0].message.content
                    else: reply = "I found these stories for you!"
                except: reply = "I found these in my box for you!"

                st.write(reply)
                st.markdown(cards_html, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": reply, "html": cards_html})
