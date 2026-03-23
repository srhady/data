import requests
import json
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.sagar-tv.com/",
    "Accept": "application/json"
}

base_url = "https://streamed.pk"
# আপনার দেওয়া সব স্পোর্টস ক্যাটাগরির লিস্ট
categories = [
    "baseball", "american-football", "hockey", 
    "fight", "tennis", "football", "basketball"
]

def generate_comprehensive_playlist():
    full_playlist = {} # সব ডাটা ক্যাটাগরি অনুযায়ী রাখার জন্য মেইন ডিকশনারি

    for category in categories:
        print(f"\n[{category.upper()}] ক্যাটাগরির ডাটা আনা হচ্ছে...")
        api_url = f"{base_url}/api/matches/{category}"
        
        full_playlist[category] = [] # এই ক্যাটাগরির জন্য একটি ফাঁকা লিস্ট তৈরি করা হলো

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
                match_date = match.get("date", "")
                
                # পোস্টার ও ব্যাজের লিংকগুলো অনেক সময় অর্ধেক দেওয়া থাকে (/api/images...), 
                # সেগুলোকে ফুল লিংক বানানোর লজিক
                poster_url = match.get("poster", "")
                if poster_url and poster_url.startswith("/"):
                    poster_url = f"{base_url}{poster_url}"

                teams = match.get("teams", {})
                sources = match.get("sources", [])
                
                print(f"  -> ম্যাচ প্রসেসিং: {match_title}")
                match_streams = []

                # এমবেড লিংক খোঁজার লুপ
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
                                # সোর্স অনুযায়ী লিংক সাজানো হলো
                                match_streams.append({
                                    "source": source_name,
                                    "links": unique_embeds
                                })
                    except Exception:
                        pass
                    
                    time.sleep(0.5) # সার্ভার যাতে ব্লক না করে তাই হাফ সেকেন্ড ব্রেক

                # যদি এমবেড লিংক পাওয়া যায়, তবেই মূল লিস্টে সুন্দর করে ডাটা অ্যাড হবে
                if match_streams:
                    clean_match_data = {
                        "id": match_id,
                        "title": match_title,
                        "date": match_date,
                        "poster": poster_url,
                        "teams": teams,
                        "streams": match_streams
                    }
                    full_playlist[category].append(clean_match_data)
                    
            except Exception as e:
                 print(f"লুপ এরর: {e}")

    # পুরো ডাটা একটি কমপ্লিট জেসন ফাইলে সেভ করা
    output_filename = "all_sports_playlist.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(full_playlist, f, ensure_ascii=False, indent=4)
        
    print(f"\n✅ মিশন কমপ্লিট! সব ক্যাটাগরির ডাটা '{output_filename}' ফাইলে সেভ হয়েছে!")

if __name__ == "__main__":
    generate_comprehensive_playlist()
