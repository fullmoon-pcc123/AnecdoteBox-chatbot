import streamlit as st
import pandas as pd
import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI  # <--- Switched from Google to OpenAI

# ---------------------------------------------------------
# 1. PAGE CONFIG & CSS
# ---------------------------------------------------------
st.set_page_config(page_title="AnecdoteBox", page_icon="icon.png", layout="centered")

# (Keep your existing CSS here...)
st.markdown("""<style>...</style>""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. DATA LOADING & SEARCH FUNCTIONS
# ---------------------------------------------------------
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

def get_stories_from_website(query):
    try:
        url = f"https://anecdotebox.com/wp-json/wp/v2/posts?search={query}&per_page=3"
        response = requests.get(url, timeout=8)
        data = response.json()
        results = []
        if isinstance(data, list) and len(data) > 0:
            for post in data:
                results.append({
                    "title": post["title"]["rendered"],
                    "summary": clean_html(post["excerpt"]["rendered"])[:150] + "...",
                    "url": post["link"]
                })
            return results
    except:
        pass
    return []

def find_stories_in_excel(query, n=3):
    if df.empty: return []
    q = query.lower()
    scores = []
    for _, row in df.iterrows():
        txt = f"{row.get('title','')} {row.get('tags','')} {row.get('summary','')}".lower()
        score = sum(1 for w in q.split() if w in txt)
        if score > 0: scores.append((score, row.to_dict()))
    scores.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scores[:n]] if scores else df.sample(n=min(n, len(df))).to_dict('records')

def render_story_card(s):
    title = s.get('title', 'Untitled')
    summary = s.get('summary', '')[:80] + "..."
    link = s.get('url', s.get('link', '#'))
    img = s.get('featured_image', "https://images.unsplash.com/photo-1519681393798-3828fb4090bb?w=400")
    return f"""
    <div class="story-card">
        <img src="{img}" class="story-img">
        <div class="card-content">
            <div class="story-title">{title}</div>
            <p style="font-size:12px; color:#666; height:40px;">{summary}</p>
            <a href="{link}" target="_blank" class="read-btn">Read Story ➜</a>
        </div>
    </div>
    """

# ---------------------------------------------------------
# 3. OPENAI API SETUP
# ---------------------------------------------------------
try:
    # Make sure you put OPENAI_API_KEY in your Streamlit Secrets
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    CHAT_MODEL = "gpt-4o-mini" # Fast, cheap, and very smart
except Exception as e:
    client = None
    st.error("OpenAI API Key missing or invalid.")

# ---------------------------------------------------------
# 4. CHAT INTERFACE
# ---------------------------------------------------------
st.markdown('<div class="logo-container"><div class="logo-text">Anecdote<span class="logo-accent">Box</span></div></div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🏠 Fresh Picks", "💬 Chat with Samu"])

with tab1:
    if not df.empty:
        st.markdown("### ✨ Featured Stories")
        random_stories = df.sample(n=min(3, len(df)))
        cols = st.columns(3)
        for i, (_, row) in enumerate(random_stories.iterrows()):
            with cols[i]: st.markdown(render_story_card(row), unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="samu-header"><div class="samu-title">Chat with Samu</div></div>', unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm Samu. How can I help you today?"}]

    # Display History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if "html" in msg: st.markdown(msg["html"], unsafe_allow_html=True)

    # User Input
    if prompt := st.chat_input("I'm looking for a story about..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching..."):
                # 1. Search Website First
                results = get_stories_from_website(prompt)
                source = "website"
                
                # 2. Fallback to Excel
                if not results:
                    results = find_stories_in_excel(prompt)
                    source = "local collection"

                # 3. Build UI & Context
                context_text = ""
                cards_html = "<div style='display:flex; gap:10px; overflow-x:auto; padding-bottom:15px;'>"
                for s in results:
                    context_text += f"Title: {s['title']}\n"
                    cards_html += f"<div style='min-width:200px;'>{render_story_card(s)}</div>"
                cards_html += "</div>"

                # 4. ChatGPT Call
                try:
                    if client:
                        response = client.chat.completions.create(
                            model=CHAT_MODEL,
                            messages=[
                                {"role": "system", "content": "You are Samu, a warm storyteller. Be brief (2 sentences)."},
                                {"role": "user", "content": f"The user asked: {prompt}. I found these stories in my {source}: {context_text}. Give a friendly response."}
                            ]
                        )
                        reply = response.choices[0].message.content
                    else:
                        reply = "I found these stories for you!"
                except Exception as e:
                    reply = "I've searched my collection and found these for you:"
                    st.error(f"ChatGPT Error: {e}")

                st.write(reply)
                st.markdown(cards_html, unsafe_allow_html=True)
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": reply, 
                    "html": cards_html
                })
