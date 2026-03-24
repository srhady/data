import requests
import json
import time
import base64
from datetime import datetime, timezone, timedelta
import urllib.parse

# আপনার ইউনিভার্সাল Vercel প্লেয়ারের লিংক
VERCEL_PLAYER_URL = "https://data-2.vercel.app/"

# API রিকোয়েস্টের হেডার
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

base_url = "https://streamed.pk"
# বাংলাদেশ সময় (UTC +6)
bd_timezone = timezone(timedelta(hours=6))

# --- ম্যাজিক: লিংক এনক্রিপ্ট করার ফাংশন ---
def encrypt_url(url):
    encoded_bytes = base64.b64encode(url.encode('utf-8'))
    encoded_str = encoded_bytes.decode('utf-8')
    # স্ট্রিংটাকে উল্টে (Reverse) দেওয়া
    reversed_str = encoded_str[::-1]
    return reversed_str

def generate_live_playlist():
    full_playlist = []

    print("\n🔴 লাইভ ম্যাচ খোঁজা শুরু হচ্ছে...")
    api_url = f"{base_url}/api/matches/live"

    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        matches_data = response.json()
        print(f"✅ মোট {len(matches_data)} টি লাইভ ম্যাচ পাওয়া গেছে।\n")
    except Exception as e:
        print(f"❌ লাইভ ডাটা আনতে এরর: {e}")
        return

    for match in matches_data:
        try:
            match_title = match.get("title", "Unknown Match")
            category = match.get("category", "Sports")
            
            # --- সময় লজিক ---
            match_date_ms = match.get("date", 0)
            readable_time = ""
            
            if match_date_ms:
                match_date_sec = match_date_ms / 1000.0
                dt_object = datetime.fromtimestamp(match_date_sec, tz=timezone.utc).astimezone(bd_timezone)
                readable_time = dt_object.strftime("%I:%M %p %d-%m-%Y") 
            
            # --- টিম এবং লোগো লজিক ---
            teams = match.get("teams", {})
            team_1_name = teams.get("home", {}).get("name", "")
            team_2_name = teams.get("away", {}).get("name", "")
            
            t1_badge = teams.get("home", {}).get("badge", "")
            team_1_logo = f"{base_url}/api/images/proxy/{t1_badge}" if t1_badge else ""
            
            t2_badge = teams.get("away", {}).get("badge", "")
            team_2_logo = f"{base_url}/api/images/proxy/{t2_badge}" if t2_badge else ""

            # --- পোস্টার লজিক ---
            poster_url = match.get("poster", "")
            if poster_url and poster_url.startswith("/"):
                poster_url = f"{base_url}{poster_url}"
            
            if not poster_url:
                encoded_title = urllib.parse.quote(match_title)
                poster_url = f"https://placehold.co/800x450/ffffff/000000.png?text={encoded_title}&font=Oswald"

            # --- স্ট্রিমিং লিংক, ভাষা এবং কোয়ালিটি বের করার লজিক ---
            sources = match.get("sources", [])
            detailed_streams = []
            
            print(f"প্রসেসিং: {match_title}")

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
                        
                        # API লিস্ট বা ডিকশনারি যাই রিটার্ন করুক, আমরা ডাটা বের করে আনব
                        if isinstance(stream_data, list):
                            for s in stream_data:
                                if "embedUrl" in s:
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
                                        "Embed_URL": safe_url # এখানে এখন আপনার Vercel লিংক সেভ হবে!
                                    })
                        elif isinstance(stream_data, dict) and "embedUrl" in stream_data:
                            quality = "HD" if stream_data.get("hd") else "SD"
                            
                            # --- আসল লিংক লুকিয়ে Vercel লিংক বানানো ---
                            original_url = stream_data["embedUrl"]
                            encrypted_id = encrypt_url(original_url)
                            safe_url = f"{VERCEL_PLAYER_URL}?id={encrypted_id}"
                            
                            detailed_streams.append({
                                "Source": source_name,
                                "Stream_No": stream_data.get("streamNo", 1),
                                "Language": stream_data.get("language", "English"),
                                "Quality": quality,
                                "Embed_URL": safe_url # এখানে এখন আপনার Vercel লিংক সেভ হবে!
                            })
                except Exception:
                    pass
                
                time.sleep(0.5) # সার্ভার ব্লকিং এড়াতে ছোট্ট ব্রেক

            # শুধু স্ট্রিমিং লিংক থাকলেই জেসনে অ্যাড হবে
            if detailed_streams:
                item = {
                    "Category": category.capitalize(),
                    "League": category.capitalize(),
                    "Team 1 Name": team_1_name,
                    "Team 2 Name": team_2_name,
                    "Team 1 Logo": team_1_logo,
                    "Team 2 Logo": team_2_logo,
                    "Match Title": match_title,
                    "Match Poster": poster_url,
                    "Match Status": "Live",
                    "Start Time": readable_time,
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Streams": detailed_streams
                }
                full_playlist.append(item)
                
        except Exception as e:
             pass

    output_filename = "live_sports_playlist.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(full_playlist, f, ensure_ascii=False, indent=4)
        
    print(f"\n🎉 চমৎকার! লাইভ ডাটাগুলো এনক্রিপ্ট হয়ে '{output_filename}' ফাইলে সেভ হয়েছে!")

if __name__ == "__main__":
    generate_live_playlist()
