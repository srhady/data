import requests
import json
import time
from datetime import datetime, timezone, timedelta
import urllib.parse

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36",
    "Referer": "https://www.sagar-tv.com/",
    "Accept": "application/json"
}

base_url = "https://streamed.pk"

categories = [
    "baseball", "american-football", "hockey", 
    "fight", "tennis", "football", "basketball"
]

bd_timezone = timezone(timedelta(hours=6))

def generate_comprehensive_playlist():
    full_playlist = []

    for category in categories:
        print(f"\n[{category.capitalize()}] ক্যাটাগরির ডাটা আনা হচ্ছে...")
        api_url = f"{base_url}/api/matches/{category}"

        try:
            response = requests.get(api_url, headers=headers)
            if response.status_code != 200:
                continue
            matches_data = response.json()
        except Exception:
            continue

        for match in matches_data:
            try:
                match_title = match.get("title", "Unknown Match")
                
                # --- সময় এবং স্ট্যাটাস লজিক ---
                match_date_ms = match.get("date", 0)
                status = "Upcoming"
                readable_time = ""
                match_date_sec = 0 # সর্টিংয়ের জন্য ডিফল্ট ভ্যালু
                
                if match_date_ms:
                    match_date_sec = match_date_ms / 1000.0
                    dt_object = datetime.fromtimestamp(match_date_sec, tz=timezone.utc).astimezone(bd_timezone)
                    readable_time = dt_object.strftime("%I:%M %p %d-%m-%Y") 
                    
                    current_time_sec = datetime.now(bd_timezone).timestamp()
                    if current_time_sec >= match_date_sec:
                        status = "Live"
                
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

                # --- এমবেড লিংক লজিক ---
                sources = match.get("sources", [])
                stream_urls_list = [] # একাধিক লিংকের জন্য ফাঁকা লিস্ট
                
                print(f"  -> প্রসেসিং: {match_title}")

                for src in sources:
                    source_name = src.get("source")
                    source_id = src.get("id")
                    
                    if not source_name or not source_id:
                        continue

                    stream_api_url = f"{base_url}/api/stream/{source_name}/{source_id}"
                    
                    try:
                        stream_resp = requests.get(stream_api_url, headers=headers)
                        if stream_resp.status_code == 200:
                            stream_data = stream_resp.json()
                            
                            # যতগুলো লিংক পাবে, সব লিস্টে অ্যাড করবে
                            if isinstance(stream_data, list):
                                for stream in stream_data:
                                    if "embedUrl" in stream:
                                        stream_urls_list.append(stream["embedUrl"])
                            elif isinstance(stream_data, dict) and "embedUrl" in stream_data:
                                stream_urls_list.append(stream_data["embedUrl"])
                    except Exception:
                        pass
                    
                    time.sleep(0.5)

                # ডুপ্লিকেট লিংকগুলো বাদ দিয়ে শুধু ইউনিক লিংকগুলো রাখা হচ্ছে
                unique_stream_urls = list(set(stream_urls_list))

                # অন্তত ১টি লিংক থাকলেই জেসনে অ্যাড হবে
                if unique_stream_urls:
                    item = {
                        "Category": category.capitalize(),
                        "League": category.capitalize(),
                        "Team 1 Name": team_1_name,
                        "Team 2 Name": team_2_name,
                        "Team 1 Logo": team_1_logo,
                        "Team 2 Logo": team_2_logo,
                        "Match Title": match_title,
                        "Match Poster": poster_url,
                        "Match Status": status,
                        "Start Time": readable_time,
                        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36",
                        "Referer": "https://www.sagar-tv.com/",
                        "Stream URL": unique_stream_urls, # এখন এটি একটি লিস্ট হবে (একাধিক লিংকের জন্য)
                        "_sort_time": match_date_sec # এটি শুধু সর্ট করার কাজে লাগবে, জেসনে দেখাবে না
                    }
                    full_playlist.append(item)
                    
            except Exception as e:
                 print(f"লুপ এরর: {e}")

    # --- ম্যাজিক সর্টিং: Live গুলো একদম উপরে, তারপর Upcoming গুলো ক্রমানুসারে ---
    full_playlist.sort(key=lambda x: (0 if x["Match Status"] == "Live" else 1, x["_sort_time"]))

    # সর্ট হওয়ার পর অপ্রয়োজনীয় টেম্পোরারি _sort_time রিমুভ করা
    for item in full_playlist:
        del item["_sort_time"]

    # ফাইনাল জেসন সেভ করা
    output_filename = "all_sports_playlist.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(full_playlist, f, ensure_ascii=False, indent=4)
        
    print(f"\n✅ মিশন কমপ্লিট! সব ডাটা '{output_filename}' ফাইলে সেভ হয়েছে!")

if __name__ == "__main__":
    generate_comprehensive_playlist()
