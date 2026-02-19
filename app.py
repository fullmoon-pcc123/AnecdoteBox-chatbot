import streamlit as st
import pandas as pd
import random
from google import genai
from google.genai import types

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="AnecdoteBox",
    page_icon="📖",
    layout="centered"
)

# ---------------------------------------------------------
# 2. CUSTOM CSS (Styling)
# ---------------------------------------------------------
st.markdown("""
<style>
/* Main Background */
.stApp {
    background: linear-gradient(135deg, #FDFBF7 0%, #F5E6D0 100%);
    font-family: 'Helvetica Neue', sans-serif;
}

/* Header Style */
.main-header {
    background: linear-gradient(135deg, #C4622D, #8B5E3C);
    padding: 25px;
    border-radius: 12px;
    color: white;
    text-align: center;
    margin-bottom: 30px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

/* Story Card Style */
.story-card {
    background: white;
    border: 1px solid #E0C9A6;
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    transition: transform 0.2s;
}
.story-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 15px rgba(196,98,45,0.15);
}
.story-img {
    width: 100%;
    height: 150px;
    object-fit: cover;
    border-radius: 8px;
    margin-bottom: 10px;
}
.story-title {
    color: #C4622D;
    font-weight: bold;
    font-size: 18px;
    margin-bottom: 5px;
}
.story-summary {
    color: #555;
    font-size: 14px;
    line-height: 1.5;
}

/* Chat Messages */
.bot-msg {
    background-color: #FEF3E2;
    padding: 15px;
    border-radius: 10px;
    border-left: 4px solid #C4622D;
    margin-bottom: 10px;
}
.user-msg {
    background-color: #E3E3E3;
    padding: 15px;
    border-radius: 10px;
    text-align: right;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. DATA LOADING
# ---------------------------------------------------------
@st.cache_data
def load_data():
    csv_file = "anecdotebox1withimage.csv"
    try:
        # Try reading as standard CSV
        df = pd.read_csv(csv_file)
    except Exception:
        try:
            # Fallback: Try reading with encoding (common for Excel-saved CSVs)
            df = pd.read_csv(csv_file, encoding='latin1')
        except Exception as e:
            st.error(f"Could not load '{csv_file}'. Error: {e}")
            return pd.DataFrame() # Return empty if fails
            
    # Clean up data (fill empty cells)
    df = df.fillna("")
    
    # standardize column names to lower case to avoid errors
    df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]
    
    return df

df = load_data()

# ---------------------------------------------------------
# 4. GEMINI API SETUP
# ---------------------------------------------------------
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception:
    st.warning("⚠️ GEMINI_API_KEY missing in .streamlit/secrets.toml")
    client = None

# Using the FREE, Stable 1.5 Model
MODEL = "gemini-1.5-flash"

# ---------------------------------------------------------
# 5. HELPER FUNCTIONS
# ---------------------------------------------------------

def render_story_card(row):
    """HTML Helper to display a story card nicely"""
    # Adjust these column names if yours are different in the CSV!
    title = row.get('title', 'Untitled')
    summary = row.get('summary', 'No summary available.')
    # Assuming your CSV column is named 'post_image_url' or similar (normalized to image_url)
    # Check your CSV column headers!
    img_url = row.get('post_image_url', row.get('image_url', 'https://via.placeholder.com/400x200?text=No+Image'))
    link = row.get('url', '#')
    
    html = f"""
    <div class="story-card">
        <img src="{img_url}" class="story-img" onerror="this.src='https://via.placeholder.com/400x200?text=Story'">
        <div class="story-title">{title}</div>
        <div class="story-summary">{summary}</div>
        <br>
        <a href="{link}" target="_blank" style="text-decoration:none; color:#C4622D; font-weight:bold;">👉 Read Full Story</a>
    </div>
    """
    return html

def find_relevant_stories(query, n=3):
    """Simple keyword search"""
    if df.empty: return []
    
    query_lower = query.lower()
    scores = []

    for _, row in df.iterrows():
        score = 0
        # Combine text fields for searching
        # Adjust column names based on your CSV
        search_text = f"{row.get('title','')} {row.get('tags','')} {row.get('summary','')}".lower()
        
        for word in query_lower.split():
            if word in search_text:
                score += 1
        
        if score > 0:
            scores.append((score, row))

    scores.sort(key=lambda x: x[0], reverse=True)
    # Return just the row data
    return [row for score, row in scores[:n]]

# ---------------------------------------------------------
# 6. UI LAYOUT
# ---------------------------------------------------------

# HEADER
st.markdown("""
<div class="main-header">
    <h1>📖 AnecdoteBox</h1>
    <p>Discover stories that matter.</p>
</div>
""", unsafe_allow_html=True)

# TABS: Home Screen vs Chat
tab1, tab2 = st.tabs(["🏠 Featured Stories", "💬 Chat with Storyteller"])

# --- TAB 1: HOME SCREEN (FEATURED) ---
with tab1:
    st.subheader("Fresh Picks for You")
    if not df.empty:
        # Pick 3 random stories
        sample_size = min(3, len(df))
        random_stories = df.sample(n=sample_size)
        
        cols = st.columns(3)
        for i, (index, row) in enumerate(random_stories.iterrows()):
            with cols[i]:
                st.markdown(render_story_card(row), unsafe_allow_html=True)
    else:
        st.info("Please upload data to see stories.")

# --- TAB 2: CHATBOT ---
with tab2:
    # Initialize Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I can help you find the perfect story. Tell me what mood you are in?"}
        ]

    # Display History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            # If we stored raw HTML for cards, render it
            if "card_html" in msg:
                st.markdown(msg["content"]) # The text
                st.markdown(msg["card_html"], unsafe_allow_html=True) # The cards
            else:
                st.markdown(msg["content"])

    # Input
    user_input = st.chat_input("Ex: I want a story about courage...")

    if user_input:
        # 1. Show User Message
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # 2. Logic to get response
        found_rows = find_relevant_stories(user_input)
        
        # Prepare context for Gemini
        context_text = ""
        cards_html = ""
        
        if found_rows:
            context_text = "Here are the stories found in our database:\n"
            cols_html = "<div style='display:flex; gap:10px; flex-wrap:wrap;'>"
            for row in found_rows:
                context_text += f"- Title: {row.get('title')}, Summary: {row.get('summary')}\n"
                # Generate visual card for the chat
                cols_html += f"<div style='flex:1; min-width:200px;'>{render_story_card(row)}</div>"
            cols_html += "</div>"
            cards_html = cols_html
        else:
            context_text = "No specific stories matched exactly in the database."

        # Prompt
        prompt = f"""
        You are a friendly librarian at AnecdoteBox.
        User said: "{user_input}"
        
        Context from database:
        {context_text}
        
        If stories were found, introduce them briefly and enthusiastically.
        If no stories were found, apologize kindly and suggest a general topic (like Love, Success, History).
        Keep it short (under 50 words).
        """

        # 3. Call Gemini
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    if client:
                        response = client.models.generate_content(
                            model=MODEL,
                            contents=prompt
                        )
                        reply_text = response.text
                    else:
                        reply_text = "API Key not configured."
                    
                    st.markdown(reply_text)
                    if cards_html:
                        st.markdown(cards_html, unsafe_allow_html=True)
                    
                    # Save to history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": reply_text,
                        "card_html": cards_html if cards_html else None
                    })

                except Exception as e:
                    st.error(f"Error connecting to AI: {e}")
