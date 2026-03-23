import requests
import json
import base64
import urllib.parse
from datetime import datetime, timezone, timedelta

# আপনার নতুন Vercel অ্যাপের ডোমেইন লিংক!
VERCEL_PLAYER_URL = "https://data-2.vercel.app/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

# বাংলাদেশ সময় (UTC +6)
bd_timezone = timezone(timedelta(hours=6))

def encrypt_url(url):
    # লিংকটাকে Base64 এ এনকোড করা হচ্ছে
    encoded_bytes = base64.b64encode(url.encode('utf-8'))
    encoded_str = encoded_bytes.decode('utf-8')
    # এবার স্ট্রিংটাকে উল্টে (Reverse) দেওয়া হচ্ছে যাতে কেউ না বোঝে!
    reversed_str = encoded_str[::-1]
    return reversed_str

def generate_secure_playlist():
    full_playlist = []
    print("\n🕵️ নতুন সোর্স (embedhd) থেকে ডাটা শিকার শুরু হচ্ছে...")
    
    api_url = "https://embedhd.org/api-event.php"

    try:
        response = requests.get(api_url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"❌ API থেকে ডাটা আনতে এরর: {e}")
        return

    # API-তে ডাটাগুলো 'days' এর ভেতর 'items' এ থাকে
    days = data.get("days", [])
    
    for day in days:
        items = day.get("items", [])
        for match in items:
            try:
                title = match.get("title", "Unknown Match")
                league = match.get("league", "Sports").upper()
                status = match.get("status", "Upcoming").capitalize()
                
                # --- টিম নাম আলাদা করা ("Team A - Team B" থেকে) ---
                team_1_name = ""
                team_2_name = ""
                if " - " in title:
                    teams = title.split(" - ")
                    team_1_name = teams[0].strip()
                    team_2_name = teams[1].strip()
                    formatted_title = f"{team_1_name} VS {team_2_name}"
                else:
                    formatted_title = title

                # --- সময় কনভার্ট করা ---
                ts_et = match.get("ts_et", 0)
                readable_time = ""
                match_date_sec = 0
                
                if ts_et:
                    match_date_sec = float(ts_et)
                    dt_object = datetime.fromtimestamp(match_date_sec, tz=timezone.utc).astimezone(bd_timezone)
                    readable_time = dt_object.strftime("%I:%M %p %d-%m-%Y")

                # --- পোস্টার তৈরি ---
                encoded_title = urllib.parse.quote(formatted_title)
                poster_url = f"https://placehold.co/800x450/ffffff/000000.png?text={encoded_title}&font=Oswald"

                # --- লিংক এনক্রিপ্ট করা ---
                streams = match.get("streams", [])
                secure_stream_urls = []
                
                print(f"প্রসেসিং: {formatted_title} ({status})")

                for stream in streams:
                    original_link = stream.get("link")
                    if original_link:
                        # ম্যাজিক: অরিজিনাল লিংক লুকিয়ে Vercel লিংক বানানো হচ্ছে
                        encrypted_id = encrypt_url(original_link)
                        safe_url = f"{VERCEL_PLAYER_URL}?id={encrypted_id}"
                        secure_stream_urls.append(safe_url)

                # শুধু লিংক থাকলেই জেসনে অ্যাড হবে
                if secure_stream_urls:
                    item = {
                        "Category": league,
                        "League": league,
                        "Team 1 Name": team_1_name,
                        "Team 2 Name": team_2_name,
                        "Team 1 Logo": "", 
                        "Team 2 Logo": "",
                        "Match Title": formatted_title,
                        "Match Poster": poster_url,
                        "Match Status": status,
                        "Start Time": readable_time,
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                        "Stream URL": secure_stream_urls, # এখানে এখন আপনার Vercel লিংক বসবে!
                        "_sort_time": match_date_sec
                    }
                    full_playlist.append(item)
                    
            except Exception as e:
                pass

    # সর্টিং: Live গুলো উপরে
    full_playlist.sort(key=lambda x: (0 if x["Match Status"].upper() == "LIVE" else 1, x["_sort_time"]))

    for item in full_playlist:
        del item["_sort_time"]

    output_filename = "playlist.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(full_playlist, f, ensure_ascii=False, indent=4)
        
    print(f"\n🎉 বুম! ডাটা সিকিউরড এবং '{output_filename}' ফাইলে সেভ হয়েছে!")

if __name__ == "__main__":
    generate_secure_playlist()
