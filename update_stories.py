import feedparser

# 1. Get your WordPress Feed (Added /feed)
feed_url = "https://anecdotebox.com"
feed = feedparser.parse(feed_url)

# 2. Extract top 3 stories
stories_html = ""
for entry in feed.entries[:3]:
    stories_html += f'<li><a href="{entry.link}">{entry.title}</a></li>'

# 3. Read index.html and update
with open("index.html", "r") as f:
    content = f.read()

# This replaces the tag and puts it back for the next run (Fixed spaces)
new_content = content.replace("<!--STORIES-->", stories_html + "\n<!--STORIES-->")

with open("index.html", "w") as f:
    f.write(new_content)

