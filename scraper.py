import requests
import json
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36",
    "Referer": "https://www.sagar-tv.com/",
    "Accept": "application/json"
}

def generate_custom_playlist():
    print("১. ডাটা ফিন্ডিং শুরু হচ্ছে...")
    matches_api_url = "https://streamed.pk/api/matches/basketball"
    
    try:
        response = requests.get(matches_api_url, headers=headers)
        response.raise_for_status()
        matches_data = response.json()
    except Exception as e:
        print(f"❌ মূল API এরর: {e}")
        return

    personal_playlist = []

    for match in matches_data:
        try:
            match_title = match.get("title", "Unknown Match")
            match_id = match.get("id", "unknown-id")
            sources = match.get("sources", [])
            
            print(f"ম্যাচ প্রসেসিং: {match_title}")
            match_embed_urls = []

            for src in sources:
                source_name = src.get("source")
                source_id = src.get("id")
                
                if not source_name or not source_id:
                    continue

                stream_api_url = f"https://streamed.pk/api/stream/{source_name}/{source_id}"
                
                try:
                    stream_resp = requests.get(stream_api_url, headers=headers)
                    if stream_resp.status_code == 200:
                        stream_data = stream_resp.json()
                        
                        if isinstance(stream_data, list):
                            for stream in stream_data:
                                if "embedUrl" in stream:
                                    match_embed_urls.append(stream["embedUrl"])
                        elif isinstance(stream_data, dict) and "embedUrl" in stream_data:
                            match_embed_urls.append(stream_data["embedUrl"])
                            
                except Exception:
                    pass
                
                time.sleep(1)

            if match_embed_urls:
                unique_embeds = list(set(match_embed_urls))
                personal_playlist.append({
                    "title": match_title,
                    "match_id": match_id,
                    "streams": unique_embeds
                })
        except Exception as e:
             print(f"লুপ এরর: {e}")

    # JSON ফাইল সেভ করা
    output_filename = "basketball_playlist.json"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(personal_playlist, f, ensure_ascii=False, indent=4)
        
    print("✅ সব ডাটা আপডেট করা হয়েছে!")

if __name__ == "__main__":
    generate_custom_playlist()
