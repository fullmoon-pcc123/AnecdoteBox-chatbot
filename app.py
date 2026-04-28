import streamlit as st
import pandas as pd
import os
import random
import requests
from bs4 import BeautifulSoup
from google import genai

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="AnecdoteBox",
    page_icon="icon.png", 
    layout="centered"
)

# ---------------------------------------------------------
# 2. CUSTOM CSS (Kept as per your original)
# ---------------------------------------------------------
st.markdown("""
<style>
.stApp { background-color: #FDFBF7; background-image: linear-gradient(180deg, #FDFBF7 0%, #F5F0E6 100%); color: #4A4A4A; font-family: 'Helvetica Neue', sans-serif; }
.logo-container { text-align: center; margin-top: 20px; margin-bottom: 5px; }
.logo-text { font-family: 'Arial Rounded MT Bold', sans-serif; font-size: 50px; font-weight: 900; color: #1A1F2C; letter-spacing: -1px; line-height: 1.1; }
.logo-accent { color: #E64833; }
.logo-tagline { font-size: 16px; color: #666; margin-bottom: 30px; text-align: center; }
.samu-header { background: white; padding: 20px; border-radius: 15px; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #EFEFEF; margin-bottom: 25px; }
.samu-title { font-family: 'Georgia', serif; font-size: 26px; font-weight: 800; color: #C4622D; margin: 0; }
.samu-subtitle { font-size: 15px; color: #8B5E3C; font-style: italic; margin-top: 5px; }
.story-card { background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid #F0F0F0; margin-bottom: 15px; height: 100%; }
.story-img { width: 100%; height: 160px; object-fit: cover; }
.card-content { padding: 15px; }
.story-title { color: #C4622D; font-weight: bold; font-size: 16px; margin-bottom: 8px; height: 42px; overflow: hidden; }
.story-summary { color: #666; font-size: 13px; line-height: 1.4; margin-bottom: 12px; height: 55px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; }
.read-btn { display: block; width: 100%; text-align: center; background-color: #C4622D; color: white !important; padding: 8px 0; border-radius: 8px; font-size: 13px; font-weight: bold; text-decoration: none; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. DATA LOADING & API HELPERS
# ---------------------------------------------------------
@st.cache_data
def load_data():
    csv_file = "Chatbox Master file.csv"
    if not os.path.exists(csv_file):
        return pd.DataFrame()
    try:
        df = pd.read_csv(csv_file, encoding='utf-8')
    except:
        df = pd.read_csv(csv_file, encoding='latin1')
    df = df.fillna("")
    df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
    return df

df = load_data()

def clean_html(html):
    return BeautifulSoup(html, "html.parser").get_text()

def get_story_from_api(query):
    try:
        url = f"https://anecdotebox.com/wp-json/wp/v2/posts?search={query}&per_page=1"
        response = requests.get(url, timeout=5)
        data = response.json()
        if data and isinstance(data, list):
            post = data[0]
            return {
                "title": post["title"]["rendered"],
                "summary": clean_html(post["excerpt"]["rendered"])[:200],
                "url": post["link"],
                "featured_image": "" # API would need extra call for media, leaving blank for fallback
            }
    except:
        pass
    return None

def render_story_card(row):
    title = row.get('title', 'Untitled')
    full_summary = str(row.get('summary', ''))
    summary = (full_summary[:90] + '...') if len(full_summary) > 90 else full_summary
    link = row.get('url', row.get('link', '#'))
    img_url = row.get('featured_image', '')
    if not img_url or str(img_url).lower() in ['nan', '', 'none']:
        img_url = "https://images.unsplash.com/photo-1519681393798-3828fb4090bb?auto=format&fit=crop&w=400&q=80"
    
    return f"""
    <div class="story-card">
        <img src="{img_url}" class="story-img">
        <div class="card-content">
            <div class="story-title">{title}</div>
            <div class="story-summary">{summary}</div>
            <a href="{link}" target="_blank" class="read-btn">Read Story ➜</a>
        </div>
    </div>
    """

def find_stories(query, n=3):
    if df.empty: return [], False
    q = query.lower()
    scores = []
    for _, row in df.iterrows():
        txt = f"{row.get('title','')} {row.get('tags','')} {row.get('summary','')} {row.get('content','')}".lower()
        score = sum(1 for w in q.split() if w in txt)
        if score > 0: scores.append((score, row))
    
    scores.sort(key=lambda x: x[0], reverse=True)
    if scores:
        return [row for _, row in scores[:n]], True
    return df.sample(n=min(n, len(df))).to_dict('records'), False

# ---------------------------------------------------------
# 4. GEMINI API SETUP
# ---------------------------------------------------------
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=GEMINI_API_KEY)
    MODEL = "gemini-1.5-flash" # Updated model name
except Exception as e:
    client = None
    st.error(f"Gemini API Error: {e}")

# ---------------------------------------------------------
# 5. UI RENDERING
# ---------------------------------------------------------
st.markdown("""
<div class="logo-container">
    <div class="logo-text">Anecdote<span class="logo-accent">Box</span></div>
    <div class="logo-tagline">Stories to make your day</div>
</div>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🏠 Fresh Picks", "💬 Chat with Samu"])

# TAB 1: HOME
with tab1:
    if not df.empty:
        st.markdown("### ✨ Featured Stories")
        random_stories = df.sample(n=min(3, len(df)))
        cols = st.columns(3)
        for i, (_, row) in enumerate(random_stories.iterrows()):
            with cols[i]:
                st.markdown(render_story_card(row), unsafe_allow_html=True)

# TAB 2: CHAT
with tab2:
    st.markdown("""
    <div class="samu-header">
        <div class="samu-title">Chat with Samu</div>
        <div class="samu-subtitle">Your Friendly Guide to the AnecdoteBox</div>
    </div>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hello! I am Samu. How are you feeling today?"}]

    # Display Chat History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if "html" in msg and msg["html"]:
                st.markdown(msg["html"], unsafe_allow_html=True)

    # Chat Input Logic
    if prompt := st.chat_input("Ex: I want a story about hope..."):
        # 1. Add User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # 2. Process Response
        with st.chat_message("assistant"):
            with st.spinner("Samu is thinking..."):
                stories_list = []
                is_exact = False
                
                # Step A: Try Live Website API
                api_result = get_story_from_api(prompt)
                if api_result:
                    stories_list = [api_result]
                    is_exact = True
                
                # Step B: Fallback to Excel
                if not stories_list and not df.empty:
                    stories_list, is_exact = find_stories(prompt)

                # Step C: Build Context and Call Gemini
                context_text = ""
                cards_html = "<div style='display:flex; gap:10px; overflow-x:auto; padding-bottom:15px;'>"
                
                for s in stories_list:
                    context_text += f"- {s.get('title')}: {s.get('summary')}\n"
                    cards_html += f"<div style='min-width:220px; max-width:220px;'>{render_story_card(s)}</div>"
                cards_html += "</div>"

                instructions = "Recommend these specific stories." if is_exact else "I couldn't find an exact match, but here are some stories you might like."
                
                full_prompt = f"""
                You are Samu, a warm and helpful guide for AnecdoteBox.
                User said: "{prompt}"
                Available Stories: {context_text}
                Context: {instructions}
                Respond to the user in a friendly way and mention the stories above if relevant. Keep it under 3 sentences.
                """

                try:
                    if client:
                        resp = client.models.generate_content(model=MODEL, contents=full_prompt)
                        reply = resp.text
                    else:
                        reply = "I'm having trouble connecting to my brain (API Key missing), but here are some stories!"
                    
                    st.write(reply)
                    st.markdown(cards_html, unsafe_allow_html=True)
                    
                    # Save to history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": reply, 
                        "html": cards_html
                    })
                except Exception as e:
                    st.error(f"Chat Error: {e}")
