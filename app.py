import streamlit as st
import pandas as pd
import os
from google import genai

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="AnecdoteBox - Samu",
    page_icon="🧞‍♂️",
    layout="centered"
)

# ---------------------------------------------------------
# 2. CUSTOM CSS (Styling)
# ---------------------------------------------------------
st.markdown("""
<style>
/* --- SOOTHING BACKGROUND --- */
.stApp {
    /* Creamy Latte / Soft Paper Background */
    background-color: #F9F7F2;
    background-image: linear-gradient(180deg, #F9F7F2 0%, #F2EFE9 100%);
    color: #4A4A4A;
    font-family: 'Helvetica Neue', sans-serif;
}

/* --- HEADER STYLING --- */
.custom-header {
    text-align: center;
    padding: 20px;
    background: white;
    border-radius: 15px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    margin-bottom: 25px;
    border: 1px solid #EAEAEA;
}
.guide-title {
    font-size: 32px;
    font-weight: 800;
    color: #C4622D; /* Your Brand Orange */
    margin-bottom: 5px;
    font-family: 'Georgia', serif;
}
.guide-subtitle {
    font-size: 18px;
    color: #8B5E3C;
    font-style: italic;
}

/* --- STORY CARD STYLING --- */
.story-card {
    background: white;
    border: 1px solid #E0C9A6;
    border-radius: 12px;
    padding: 0; /* Removed padding for full-width image */
    margin-bottom: 20px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.05);
    overflow: hidden; /* Keeps image inside rounded corners */
    transition: transform 0.2s;
}
.story-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 16px rgba(196,98,45,0.15);
}
.story-img {
    width: 100%;
    height: 180px; /* Fixed height for consistency */
    object-fit: cover; /* Crops image nicely */
    border-bottom: 1px solid #eee;
}
.card-content {
    padding: 15px;
}
.story-title {
    color: #C4622D;
    font-weight: bold;
    font-size: 18px;
    margin-bottom: 5px;
    line-height: 1.3;
}
.story-summary {
    color: #666;
    font-size: 13px;       /* Made slightly smaller for crisp look */
    line-height: 1.4;
    margin-bottom: 12px;
    display: -webkit-box;
    -webkit-line-clamp: 2; /* CUTS TEXT AFTER 2 LINES */
    -webkit-box-orient: vertical;
    overflow: hidden;
    height: 38px;          /* Forces a fixed height for uniformity */
}
.read-more {
    text-decoration: none;
    color: white;
    background-color: #C4622D;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
    display: inline-block;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. DATA LOADING
# ---------------------------------------------------------
@st.cache_data
def load_data():
    csv_file = "Chatbot Master file.csv"
    try:
        df = pd.read_csv(csv_file)
    except Exception:
        try:
            df = pd.read_csv(csv_file, encoding='latin1')
        except:
            return pd.DataFrame()

    df = df.fillna("")
    # Normalize headers: 'Featured Image' -> 'featured_image'
    df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
    return df

df = load_data()

# ---------------------------------------------------------
# 4. GEMINI SETUP
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
    """
    Creates the HTML for a single story card.
    TRUNCATED VERSION: Cuts text by ~25% for a crispy look.
    """
    title = row.get('title', 'Untitled')
    
    # --- NEW TRUNCATION LOGIC ---
    # Get the full summary
    full_summary = str(row.get('summary', ''))
    
    # Cut it off at 90 characters (approx 15-20 words)
    # .rsplit ensures we don't cut a word in half
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
            <a href="{link}" target="_blank" class="read-btn">Read ➜</a>
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
        score = sum(1 for w in q.split() if w in txt)
        if score > 0: scores.append((score, row))
    scores.sort(key=lambda x: x[0], reverse=True)
    return [row for _, row in scores[:n]]

# ---------------------------------------------------------
# 6. HEADER LAYOUT (LOGO + SAMU)
# ---------------------------------------------------------

# Create columns to center the logo and text
col1, col2, col3 = st.columns([1, 6, 1])

with col2:
    # 1. DISPLAY LOGO (If logo.png exists)
    if os.path.exists("logo.png"):
        st.image("logo.png", width=120) 
    else:
        # Fallback emoji if no logo file found
        st.markdown("<div style='text-align:center; font-size:60px;'>🧞‍♂️</div>", unsafe_allow_html=True)

    # 2. DISPLAY CATCHY TITLE
    st.markdown("""
    <div class='custom-header'>
        <div class='guide-title'>Chat with Samu</div>
        <div class='guide-subtitle'>Your Personal Guide to the AnecdoteBox</div>
    </div>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------
# 7. MAIN INTERFACE
# ---------------------------------------------------------
tab1, tab2 = st.tabs(["🏠 Featured Stories", "💬 Chat with Samu"])

with tab1:
    st.markdown("### ✨ Fresh Picks for You")
    if not df.empty:
        # Show 3 random stories
        sample = df.sample(n=min(3, len(df)))
        c1, c2, c3 = st.columns(3)
        for i, (_, row) in enumerate(sample.iterrows()):
            with [c1,c2,c3][i]:
                st.markdown(render_story_card(row), unsafe_allow_html=True)

with tab2:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Greetings! I am Samu. I know thousands of stories. How are you feeling today?"}
        ]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if "html" in msg: st.markdown(msg["html"], unsafe_allow_html=True)

    if prompt := st.chat_input("Tell Samu your mood..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)

        stories = find_stories(prompt)
        
        # Build context
        context = ""
        cards_html = ""
        if stories:
            context = "Found stories:\n"
            # Flex container for chat cards
            cards_html = "<div style='display:flex; gap:10px; overflow-x:auto; padding-bottom:10px;'>"
            for s in stories:
                context += f"- {s.get('title')}: {s.get('summary')}\n"
                # Render card with fixed width for chat
                cards_html += f"<div style='min-width:220px; max-width:220px;'>{render_story_card(s)}</div>"
            cards_html += "</div>"
        
        # AI Prompt
        full_prompt = f"""
        You are Samu, a wise and friendly guide.
        User: "{prompt}"
        Database Stories: {context}
        
        If stories found: "I found these gems for you..." (briefly say why they fit).
        If none: Be warm, suggest a topic like 'Courage' or 'Love'.
        Keep it short.
        """

        with st.chat_message("assistant"):
            with st.spinner("Samu is thinking..."):
                try:
                    if client:
                        resp = client.models.generate_content(model=MODEL, contents=full_prompt)
                        reply = resp.text
                    else:
                        reply = "My API key is taking a nap."
                    
                    st.write(reply)
                    if cards_html: st.markdown(cards_html, unsafe_allow_html=True)
                    
                    st.session_state.messages.append({"role": "assistant", "content": reply, "html": cards_html})
                except Exception as e:
                    st.error(str(e))
