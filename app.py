import streamlit as st
import pandas as pd
import os
import random
from google import genai

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Chat with Samu",
    page_icon="icon.png", # <--- MAKE SURE YOU UPLOAD icon.png
    layout="centered"
)

# ---------------------------------------------------------
# 2. CUSTOM CSS
# ---------------------------------------------------------
st.markdown("""
<style>
/* Background */
.stApp {
    background-color: #FDFBF7;
    background-image: linear-gradient(180deg, #FDFBF7 0%, #F5F0E6 100%);
    color: #4A4A4A;
    font-family: 'Helvetica Neue', sans-serif;
}

/* Header */
.header-container {
    text-align: center;
    padding: 20px;
    background: white;
    border-radius: 20px;
    box-shadow: 0 4px 15px rgba(196, 98, 45, 0.08);
    border: 1px solid #EFEFEF;
    margin-bottom: 20px;
}
.samu-title {
    font-family: 'Georgia', serif;
    font-size: 38px;
    font-weight: 800;
    color: #C4622D;
    margin-bottom: 5px;
}
.samu-subtitle {
    font-family: 'Helvetica Neue', sans-serif;
    font-size: 16px;
    color: #8B5E3C;
    font-style: italic;
}

/* Story Cards */
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
    height: 42px; /* Fixed height for alignment */
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
    height: 55px; /* Fixed height for alignment */
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
# 3. DATA LOADING (ROBUST VERSION)
# ---------------------------------------------------------
@st.cache_data
def load_data():
    csv_file = "Chatbot Master file.csv"
    
    # Check if file exists first
    if not os.path.exists(csv_file):
        st.error(f"❌ CRITICAL ERROR: The file '{csv_file}' was not found in the folder.")
        return pd.DataFrame()

    try:
        df = pd.read_csv(csv_file)
    except Exception as e1:
        try:
            # Fallback for encoding issues
            df = pd.read_csv(csv_file, encoding='latin1')
        except Exception as e2:
            st.error(f"❌ ERROR LOADING CSV: {e2}")
            return pd.DataFrame()

    df = df.fillna("")
    # Standardize column names
    df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
    
    # Quick Debug: Check if 'featured_image' exists
    if 'featured_image' not in df.columns and not df.empty:
        st.warning(f"⚠️ Warning: 'Featured Image' column not found. Available columns: {list(df.columns)}")
        
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

def render_story_card(row):
    title = row.get('title', 'Untitled')
    full_summary = str(row.get('summary', ''))
    
    # Truncate summary for "crispy" look
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
            <img src="{img_url}" class="story-img" 
                 onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1519681393798-3828fb4090bb?auto=format&fit=crop&w=400&q=80';">
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
    
    # 1. Try to find matches
    for _, row in df.iterrows():
        # Search everywhere (Title, Category, Tags, Summary)
        txt = f"{row.get('title','')} {row.get('tags','')} {row.get('summary','')} {row.get('category','')} {row.get('content','')}".lower()
        
        score = 0
        for w in q.split():
            if w in txt: score += 1
            
        if score > 0:
            scores.append((score, row))
            
    scores.sort(key=lambda x: x[0], reverse=True)
    results = [row for _, row in scores[:n]]
    
    # 2. FALLBACK LOGIC: If no results found, return random ones!
    if not results:
        return df.sample(n=min(n, len(df))).to_dict('records'), False # False means "Random match"
    
    return results, True # True means "Exact match"

# ---------------------------------------------------------
# 6. HEADER & MAIN UI
# ---------------------------------------------------------

col1, col2, col3 = st.columns([1, 4, 1])
with col2:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    st.markdown("""
    <div class="header-container">
        <div class="samu-title">Chat with Samu</div>
        <div class="samu-subtitle">Your Friendly Guide to the AnecdoteBox</div>
    </div>
    """, unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🏠 Fresh Picks", "💬 Chat with Samu"])

# --- TAB 1: HOME ---
with tab1:
    if not df.empty:
        st.markdown("### ✨ Featured Stories")
        # Ensure we don't crash if df is smaller than 3
        sample_size = min(3, len(df))
        random_stories = df.sample(n=sample_size)
        
        c1, c2, c3 = st.columns(3)
        for i, (_, row) in enumerate(random_stories.iterrows()):
            with [c1, c2, c3][i]:
                st.markdown(render_story_card(row), unsafe_allow_html=True)
    else:
        st.info("⚠️ Data not loaded. Please check CSV file name.")

# --- TAB 2: CHAT ---
with tab2:
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hello! I am Samu your frindly AnecdoteBox chatbot. Tell me, what you prefer to read?"}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if "html" in msg and msg["html"]:
                st.markdown(msg["html"], unsafe_allow_html=True)

    if prompt := st.chat_input("Ex: I want a story about love..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)

        # Run Search
        stories_list = []
        is_exact_match = False
        
        if not df.empty:
            found_data, is_exact_match = find_stories(prompt)
            # Convert back to list of rows if it was a dataframe sample
            if isinstance(found_data, list):
                stories_list = found_data
            else:
                # If it came from sample() fallback (which returns dict)
                stories_list = found_data

        # Prepare Context
        context_text = ""
        cards_html = ""
        
        if stories_list:
            cards_html = "<div style='display:flex; gap:10px; overflow-x:auto; padding-bottom:15px;'>"
            for s in stories_list:
                # Handle dictionary vs Series access
                title = s.get('title') if isinstance(s, dict) else s['title']
                summary = s.get('summary') if isinstance(s, dict) else s['summary']
                
                context_text += f"- {title}: {summary}\n"
                cards_html += f"<div style='min-width:220px; max-width:220px;'>{render_story_card(s)}</div>"
            cards_html += "</div>"
        
        # Decide Prompt based on whether we found exact matches or random ones
        if is_exact_match:
            instructions = "I found these specific stories for you. Recommend them enthusiastically."
        else:
            instructions = f"I couldn't find stories exactly matching '{prompt}', but I selected these random interesting stories. Apologize gently, then recommend these instead."

        full_prompt = f"""
        You are Samu. User asked: "{prompt}"
        Stories to display:
        {context_text}
        
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
