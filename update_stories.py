import feedparser # You'll need to add this to requirements.txt

# 1. Get your WordPress Feed
feed_url = "https://anecdotebox.com"
feed = feedparser.parse(feed_url)

# 2. Extract top 3 stories
stories_html = ""
for entry in feed.entries[:3]:
    stories_html += f'<li><a href="{entry.link}">{entry.title}</a></li>'

# 3. Read your index.html and replace a placeholder with the stories
with open("index.html", "r") as f:
    content = f.read()

# This replaces a comment <!--STORIES--> in your HTML with the actual list
new_content = content.replace("<!--STORIES-->", stories_html)

with open("index.html", "w") as f:
    f.write(new_content)
