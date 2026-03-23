import requests
import json
import time
from datetime import datetime, timezone, timedelta
import urllib.parse

# আগের রেফারার (Referer) পুরোপুরি বাদ দেওয়া হয়েছে
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

base_url = "https://streamed.pk"
bd_timezone = timezone(timedelta(hours=6))

def generate_todays_playlist():
    full_playlist = []

    print("\nনতুন API থেকে আজকের সব খেলার ডাটা আনা হচ্ছে...")
    api_url = f"{base_url}/api/matches/all-today"

    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        matches_data = response.json()
    except Exception as e:
        print(f"API থেকে ডাটা আনতে এরর: {e}")
        return

    for match in matches_data:
        try:
            match_title = match.get("title", "Unknown Match")
            category = match.get("category", "Sports")
            
            match_date_ms = match.get("date", 0)
            status = "Upcoming"
            readable_time = ""
            match_date_sec = 0
            
            if match_date_ms:
                match_date_sec = match_date_ms / 1000.0
                dt_object = datetime.fromtimestamp(match_date_sec, tz=timezone.utc).astimezone(bd_timezone)
                readable_time = dt_object.strftime("%I:%M %p %d-%m-%Y") 
                
                current_time_sec = datetime.now(bd_timezone).timestamp()
                if current_time_sec >= match_date_sec:
                    status = "Live"
            
            teams = match.get("teams", {})
            team_1_name = teams.get("home", {}).get("name", "")
            team_2_name = teams.get("away", {}).get("name", "")
            
            t1_badge = teams.get("home", {}).get("badge", "")
            team_1_logo = f"{base_url}/api/images/proxy/{t1_badge}" if t1_badge else ""
            
            t2_badge = teams.get("away", {}).get("badge", "")
            team_2_logo = f"{base_url}/api/images/proxy/{t2_badge}" if t2_badge else ""

            poster_url = match.get("poster", "")
            if poster_url and poster_url.startswith("/"):
                poster_url = f"{base_url}{poster_url}"
            
            if not poster_url:
                encoded_title = urllib.parse.quote(match_title)
                poster_url = f"https://placehold.co/800x450/ffffff/000000.png?text={encoded_title}&font=Oswald"

            sources = match.get("sources", [])
            stream_urls_list = []
            
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
                        
                        if isinstance(stream_data, list):
                            for stream in stream_data:
                                if "embedUrl" in stream:
                                    stream_urls_list.append(stream["embedUrl"])
                        elif isinstance(stream_data, dict) and "embedUrl" in stream_data:
                            stream_urls_list.append(stream_data["embedUrl"])
                except Exception:
                    pass
                
                time.sleep(0.5) 

            unique_stream_urls = list(dict.fromkeys(stream_urls_list))

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
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Stream URL": unique_stream_urls,
                    "_sort_time": match_date_sec
                }
                full_playlist.append(item)
                
        except Exception as e:
             pass

    full_playlist.sort(key=lambda x: (0 if x["Match Status"] == "Live" else 1, x["_sort_time"]))

    for item in full_playlist:
        del item["_sort_time"]

    output_filename = "all_sports_playlist.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(full_playlist, f, ensure_ascii=False, indent=4)
        
    print("\nডাটা সেভ সম্পন্ন হয়েছে!")

if __name__ == "__main__":
    generate_todays_playlist()
