import requests
import json

manga_id = "37f5cce0-8070-4ada-96e5-fa24b1bd4ff9"
languages = ["es-la", "en", "es"]

def get_aggregate(manga_id):
    url = f"https://api.mangadex.org/manga/{manga_id}/aggregate"
    params = {"translatedLanguage[]": languages}
    resp = requests.get(url, params=params)
    return resp.json()["volumes"]

def check_volumes(volumes):
    for vol_num, vol_data in volumes.items():
        if vol_num in ["none"] or (vol_num.isdigit() and int(vol_num) > 7):
            continue
        
        print(f"\n--- Volumen {vol_num} ---")
        chapters = vol_data["chapters"]
        
        # We need to check language availability per chapter.
        # The aggregate API doesn't tell us which chapter has which language easily
        # if we pass multiple languages. It just aggregates them.
        # Better: Check each language individually or fetch chapter list.
        pass

# Since aggregate is limited, let's fetch all chapters for these languages
def fetch_all_chapters(manga_id):
    url = "https://api.mangadex.org/chapter"
    all_chapters = []
    offset = 0
    while True:
        params = {
            "manga": manga_id,
            "translatedLanguage[]": languages,
            "limit": 100,
            "offset": offset,
            "order[chapter]": "asc"
        }
        resp = requests.get(url, params=params).json()
        all_chapters.extend(resp["data"])
        if offset + 100 >= resp["total"]:
            break
        offset += 100
    return all_chapters

def analyze_chapters(chapters):
    # vol -> chapter -> set of languages
    vol_map = {}
    for ch in chapters:
        attrs = ch["attributes"]
        vol = attrs["volume"] or "none"
        ch_num = attrs["chapter"] or "none"
        lang = attrs["translatedLanguage"]
        
        if vol not in vol_map: vol_map[vol] = {}
        if ch_num not in vol_map[vol]: vol_map[vol][ch_num] = set()
        vol_map[vol][ch_num].add(lang)
    
    for vol in sorted(vol_map.keys(), key=lambda x: float(x) if x.replace(".","",1).isdigit() else 999):
        if vol != "none" and float(vol) > 7: continue
        
        print(f"Volumen {vol}:")
        is_mixed = False
        ch_list = sorted(vol_map[vol].keys(), key=lambda x: float(x) if x.replace(".","",1).isdigit() else 999)
        for ch in ch_list:
            langs = vol_map[vol][ch]
            print(f"  Ch {ch}: {langs}")
            if "es-la" not in langs:
                is_mixed = True
        
        if is_mixed:
            print(f"  >>> ESTE VOLUMEN ES MIXTO (faltan capítulos en es-la) <<<")

if __name__ == "__main__":
    print("Fetching chapters for Kaguya-sama...")
    chaps = fetch_all_chapters(manga_id)
    analyze_chapters(chaps)
