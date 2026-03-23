import requests
import json
import urllib.parse
from datetime import datetime, timezone, timedelta

# বাংলাদেশ সময় (UTC +6)
bd_timezone = timezone(timedelta(hours=6))

def fetch_matches():
    # আপনার দেওয়া JS কোডের মতো fetch('https://streamed.pk/api/matches/all-today')
    # all-today দিলাম যাতে লাইভ এবং আপকামিং দুটোই আসে
    url = 'https://streamed.pk/api/matches/all-today' 
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status() # JS এর if (!response.ok) throw new Error(...) এর মতো
        matches = response.json()
        
        full_playlist = []
        
        # matches.forEach(match => { ... })
        for match in matches:
            process_match(match, full_playlist)
            
        # ম্যাজিক সর্টিং: Live গুলো একদম উপরে, তারপর Upcoming
        full_playlist.sort(key=lambda x: (0 if x["Match Status"] == "Live" else 1, x["_sort_time"]))

        for item in full_playlist:
            del item["_sort_time"]

        # JSON সেভ করা
        with open("all_sports_playlist.json", "w", encoding="utf-8") as f:
            json.dump(full_playlist, f, ensure_ascii=False, indent=4)
            
        print("✅ সব ডাটা পারফেক্টলি সেভ হয়েছে!")

    except Exception as error:
        print('Error fetching matches:', error)

def process_match(match, playlist):
    # বেসিক ইনফো
    title = match.get("title", "Unknown Match")
    category = match.get("category", "Sports")
    
    # সময় এবং স্ট্যাটাস (JS এর new Date(match.date).toLocaleString() এর মতো)
    match_date_ms = match.get("date", 0)
    status = "Upcoming"
    readable_time = ""
    match_date_sec = 0
    
    if match_date_ms:
        match_date_sec = match_date_ms / 1000.0
        dt_object = datetime.fromtimestamp(match_date_sec, tz=timezone.utc).astimezone(bd_timezone)
        readable_time = dt_object.strftime("%I:%M %p %d-%m-%Y") 
        
        if datetime.now(bd_timezone).timestamp() >= match_date_sec:
            status = "Live"

    # টিম ইনফো (JS এর if (match.teams) {...} লজিক)
    teams = match.get("teams", {})
    team_1_name = teams.get("home", {}).get("name", "") if teams.get("home") else ""
    team_2_name = teams.get("away", {}).get("name", "") if teams.get("away") else ""
    
    t1_badge = teams.get("home", {}).get("badge", "") if teams.get("home") else ""
    team_1_logo = f"https://streamed.pk/api/images/proxy/{t1_badge}" if t1_badge else ""
    
    t2_badge = teams.get("away", {}).get("badge", "") if teams.get("away") else ""
    team_2_logo = f"https://streamed.pk/api/images/proxy/{t2_badge}" if t2_badge else ""

    # পোস্টার
    poster_url = match.get("poster", "")
    if poster_url and poster_url.startswith("/"):
        poster_url = f"https://streamed.pk{poster_url}"
    if not poster_url:
        poster_url = f"https://placehold.co/800x450/ffffff/000000.png?text={urllib.parse.quote(title)}&font=Oswald"

    # স্ট্রিম সোর্স বের করা (JS এর match.sources.map(...) এর অংশটুকু)
    sources = match.get("sources", [])
    stream_urls = []
    
    print(f"Match: {title}, Status: {status}")

    for src in sources:
        source_name = src.get("source")
        source_id = src.get("id")
        
        if source_name and source_id:
            # আসল এমবেড লিংক আনার জন্য এই রিকোয়েস্টটি করতেই হবে
            stream_api = f"https://streamed.pk/api/stream/{source_name}/{source_id}"
            try:
                res = requests.get(stream_api, timeout=5)
                if res.status_code == 200:
                    stream_data = res.json()
                    if isinstance(stream_data, list):
                        for s in stream_data:
                            if "embedUrl" in s: stream_urls.append(s["embedUrl"])
                    elif isinstance(stream_data, dict) and "embedUrl" in stream_data:
                        stream_urls.append(stream_data["embedUrl"])
            except:
                pass

    unique_streams = list(dict.fromkeys(stream_urls))

    if unique_streams:
        playlist.append({
            "Category": category.capitalize(),
            "League": category.capitalize(),
            "Team 1 Name": team_1_name,
            "Team 2 Name": team_2_name,
            "Team 1 Logo": team_1_logo,
            "Team 2 Logo": team_2_logo,
            "Match Title": title,
            "Match Poster": poster_url,
            "Match Status": status,
            "Start Time": readable_time,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Stream URL": unique_streams,
            "_sort_time": match_date_sec
        })

# কোড রান করা
if __name__ == "__main__":
    fetch_matches()
