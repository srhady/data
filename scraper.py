import requests
import json
import time
from datetime import datetime, timezone, timedelta

# ফেক ব্রাউজার হেডার
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.sagar-tv.com/",
    "Accept": "application/json"
}

base_url = "https://streamed.pk"

# আপনার স্পোর্টস ক্যাটাগরির লিস্ট
categories = [
    "baseball", "american-football", "hockey", 
    "fight", "tennis", "football", "basketball"
]

# বাংলাদেশ সময় (UTC +6) সেট করা (যাতে গিটহাবে রান করলেও সঠিক সময় দেখায়)
bd_timezone = timezone(timedelta(hours=6))

def generate_comprehensive_playlist():
    full_playlist = {}

    for category in categories:
        print(f"\n[{category.upper()}] ক্যাটাগরির ডাটা আনা হচ্ছে...")
        api_url = f"{base_url}/api/matches/{category}"
        full_playlist[category] = []

        try:
            response = requests.get(api_url, headers=headers)
            if response.status_code != 200:
                print(f"❌ {category} এর ডাটা পাওয়া যায়নি।")
                continue
            matches_data = response.json()
        except Exception as e:
            print(f"❌ {category} API কল এরর: {e}")
            continue

        for match in matches_data:
            try:
                match_title = match.get("title", "Unknown Match")
                match_id = match.get("id", "")
                
                # --- সময় ও স্ট্যাটাস লজিক শুরু ---
                match_date_ms = match.get("date", 0)
                status = "Unknown"
                readable_time = ""
                
                if match_date_ms:
                    # মিলি-সেকেন্ডকে সেকেন্ডে রূপান্তর
                    match_date_sec = match_date_ms / 1000.0
                    
                    # API-এর টাইমস্ট্যাম্প থেকে বাংলাদেশ সময়ে রূপান্তর
                    dt_object = datetime.fromtimestamp(match_date_sec, tz=timezone.utc).astimezone(bd_timezone)
                    readable_time = dt_object.strftime("%d-%b-%Y %I:%M %p") # ফরম্যাট: 24-Mar-2026 08:30 PM
                    
                    # বর্তমান বাংলাদেশ সময়ের সাথে তুলনা করে Live নাকি Upcoming নির্ধারণ
                    current_time_sec = datetime.now(bd_timezone).timestamp()
                    
                    if current_time_sec >= match_date_sec:
                        status = "🔴 Live"
                    else:
                        status = "⏳ Upcoming"
                # --- সময় ও স্ট্যাটাস লজিক শেষ ---
                
                # পোস্টারের ফুল লিংক তৈরি
                poster_url = match.get("poster", "")
                if poster_url and poster_url.startswith("/"):
                    poster_url = f"{base_url}{poster_url}"

                teams = match.get("teams", {})
                sources = match.get("sources", [])
                
                print(f"  -> ম্যাচ প্রসেসিং: {match_title} ({status})")
                match_streams = []

                # এমবেড লিংক বের করার লুপ
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
                            
                            embed_urls = []
                            if isinstance(stream_data, list):
                                for stream in stream_data:
                                    if "embedUrl" in stream:
                                        embed_urls.append(stream["embedUrl"])
                            elif isinstance(stream_data, dict) and "embedUrl" in stream_data:
                                embed_urls.append(stream_data["embedUrl"])
                            
                            if embed_urls:
                                unique_embeds = list(set(embed_urls))
                                match_streams.append({
                                    "source": source_name,
                                    "links": unique_embeds
                                })
                    except Exception:
                        pass
                    
                    time.sleep(0.5)

                # শুধু এমবেড লিংক থাকলেই ডাটা সেভ হবে
                if match_streams:
                    clean_match_data = {
                        "id": match_id,
                        "title": match_title,
                        "status": status,
                        "start_time": readable_time,
                        "poster": poster_url,
                        "teams": teams,
                        "streams": match_streams
                    }
                    full_playlist[category].append(clean_match_data)
                    
            except Exception as e:
                 print(f"লুপ এরর: {e}")

    # ফাইনাল জেসন সেভ করা
    output_filename = "all_sports_playlist.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(full_playlist, f, ensure_ascii=False, indent=4)
        
    print(f"\n✅ মিশন কমপ্লিট! সব ডাটা '{output_filename}' ফাইলে সেভ হয়েছে!")

if __name__ == "__main__":
    generate_comprehensive_playlist()
