import requests
import json
import time
import base64
from datetime import datetime, timezone, timedelta
import urllib.parse

# আপনার ইউনিভার্সাল Vercel প্লেয়ারের লিংক
VERCEL_PLAYER_URL = "https://data-2.vercel.app/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

base_url = "https://streamed.pk"
bd_timezone = timezone(timedelta(hours=6))

# --- লিংক এনক্রিপ্ট করার ম্যাজিক ---
def encrypt_url(url):
    encoded_bytes = base64.b64encode(url.encode('utf-8'))
    encoded_str = encoded_bytes.decode('utf-8')
    reversed_str = encoded_str[::-1]
    return reversed_str

def generate_full_playlist():
    full_playlist = []
    seen_matches = set() # একই ম্যাচ যেন ডাবল না হয়, সেটা চেক করার জন্য

    # লাইভ এবং আপকামিং দুইটা API তেই আমরা হানা দেব!
    endpoints = [
        {"url": "/api/matches/live", "status": "Live 🔴"},
        {"url": "/api/matches/schedule", "status": "Upcoming ⏳"}
    ]

    print("\n🔍 লাইভ এবং আপকামিং ম্যাচ খোঁজা শুরু হচ্ছে...")

    for ep in endpoints:
        api_url = f"{base_url}{ep['url']}"
        status_label = ep['status']
        
        try:
            response = requests.get(api_url, headers=headers, timeout=10)
            if response.status_code != 200:
                continue
            matches_data = response.json()
            print(f"✅ {status_label} থেকে {len(matches_data)} টি ম্যাচ পাওয়া গেছে।")
        except Exception as e:
            print(f"❌ {status_label} ডাটা আনতে এরর: {e}")
            continue

        for match in matches_data:
            try:
                match_id = match.get("id", "")
                match_title = match.get("title", "Unknown Match")
                
                # যদি ম্যাচটি আগেই 'Live' লিস্টে অ্যাড হয়ে থাকে, তবে 'Upcoming' থেকে আর নেব না
                if match_id in seen_matches or match_title in seen_matches:
                    continue
                seen_matches.add(match_id)
                seen_matches.add(match_title)

                category = match.get("category", "Sports")
                
                # --- সময় লজিক ---
                match_date_ms = match.get("date", 0)
                readable_time = ""
                sort_time = 0
                
                if match_date_ms:
                    sort_time = match_date_ms / 1000.0
                    dt_object = datetime.fromtimestamp(sort_time, tz=timezone.utc).astimezone(bd_timezone)
                    readable_time = dt_object.strftime("%I:%M %p | %d-%b") 
                
                # --- টিম লজিক ---
                teams = match.get("teams", {})
                team_1_name = teams.get("home", {}).get("name", "")
                team_2_name = teams.get("away", {}).get("name", "")
                
                t1_badge = teams.get("home", {}).get("badge", "")
                team_1_logo = f"{base_url}/api/images/proxy/{t1_badge}" if t1_badge else ""
                
                t2_badge = teams.get("away", {}).get("badge", "")
                team_2_logo = f"{base_url}/api/images/proxy/{t2_badge}" if t2_badge else ""

                # --- পোস্টার ---
                poster_url = match.get("poster", "")
                if poster_url and poster_url.startswith("/"):
                    poster_url = f"{base_url}{poster_url}"
                if not poster_url:
                    encoded_title = urllib.parse.quote(match_title)
                    poster_url = f"https://placehold.co/800x450/1a1a1a/ffffff.png?text={encoded_title}&font=Oswald"

                # --- স্ট্রিমিং লিংক ---
                sources = match.get("sources", [])
                detailed_streams = []

                for src in sources:
                    source_name = src.get("source")
                    source_id = src.get("id")
                    
                    if not source_name or not source_id:
                        continue

                    stream_api_url = f"{base_url}/api/stream/{source_name}/{source_id}"
                    
                    try:
                        stream_resp = requests.get(stream_api_url, headers=headers, timeout=10)
                        if stream_resp.status_code == 200:
                            stream_data = stream_resp.json()
                            
                            stream_list = stream_data if isinstance(stream_data, list) else [stream_data]
                            
                            for s in stream_list:
                                if isinstance(s, dict) and "embedUrl" in s:
                                    quality = "HD" if s.get("hd") else "SD"
                                    
                                    # --- আসল লিংক লুকিয়ে Vercel লিংক বানানো ---
                                    original_url = s["embedUrl"]
                                    encrypted_id = encrypt_url(original_url)
                                    safe_url = f"{VERCEL_PLAYER_URL}?id={encrypted_id}"
                                    
                                    detailed_streams.append({
                                        "Source": source_name,
                                        "Stream_No": s.get("streamNo", 1),
                                        "Language": s.get("language", "English"),
                                        "Quality": quality,
                                        "Embed_URL": safe_url
                                    })
                    except Exception:
                        pass
                    
                    time.sleep(0.3)

                # আপকামিং ম্যাচগুলোতে অনেক সময় আগে থেকে লিংক থাকে না। 
                # তবুও আমরা জেসনে অ্যাড করব, যাতে ইউজাররা শিডিউল দেখতে পারে।
                item = {
                    "Category": category.capitalize(),
                    "League": category.capitalize(),
                    "Team 1 Name": team_1_name,
                    "Team 2 Name": team_2_name,
                    "Team 1 Logo": team_1_logo,
                    "Team 2 Logo": team_2_logo,
                    "Match Title": match_title,
                    "Match Poster": poster_url,
                    "Match Status": status_label,
                    "Start Time": readable_time,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Streams": detailed_streams,
                    "_sort_time": sort_time # সর্টিং এর জন্য লুকানো ডাটা
                }
                full_playlist.append(item)
                    
            except Exception as e:
                 pass

    # সর্টিং: Live গুলো একদম উপরে থাকবে, এরপর Upcoming গুলো সময়ের ক্রমানুসারে থাকবে
    full_playlist.sort(key=lambda x: (0 if "Live" in x["Match Status"] else 1, x["_sort_time"]))

    # সর্টিং শেষে _sort_time রিমুভ করে দেওয়া
    for item in full_playlist:
        del item["_sort_time"]

    output_filename = "live_sports_playlist.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(full_playlist, f, ensure_ascii=False, indent=4)
        
    print(f"\n🎉 বুম! মোট {len(full_playlist)} টি (Live + Upcoming) ম্যাচ '{output_filename}' ফাইলে সেভ হয়েছে!")

if __name__ == "__main__":
    generate_full_playlist()
