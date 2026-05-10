import requests

def analyze_manga(manga_id, name):
    url = "https://api.mangadex.org/chapter"
    languages = ["es-la", "en"]
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
    
    vol_map = {}
    for ch in all_chapters:
        attrs = ch["attributes"]
        vol = attrs["volume"] or "none"
        ch_num = attrs["chapter"] or "none"
        lang = attrs["translatedLanguage"]
        if vol not in vol_map: vol_map[vol] = {}
        if ch_num not in vol_map[vol]: vol_map[vol][ch_num] = set()
        vol_map[vol][ch_num].add(lang)
    
    print(f"\n=== {name} ===")
    for vol in sorted(vol_map.keys(), key=lambda x: float(x) if x.replace(".","",1).isdigit() else 999):
        if vol == "none": continue
        if float(vol) > 5: break
        
        counts = {"es-la": 0, "en": 0, "both": 0, "total": 0}
        for ch, langs in vol_map[vol].items():
            counts["total"] += 1
            if "es-la" in langs and "en" in langs: counts["both"] += 1
            elif "es-la" in langs: counts["es-la"] += 1
            elif "en" in langs: counts["en"] += 1
        
        status = "Pure ES-LA" if counts["es-la"] + counts["both"] == counts["total"] else "Mixed/EN"
        if counts["es-la"] == 0 and counts["both"] == 0: status = "Pure EN"
        
        print(f"Vol {vol}: {status} (Total: {counts['total']}, ES-LA: {counts['es-la'] + counts['both']}, EN: {counts['en']})")

if __name__ == "__main__":
    # Kaguya-sama
    analyze_manga("37f5cce0-8070-4ada-96e5-fa24b1bd4ff9", "Kaguya-sama")
    # Chainsaw Man
    analyze_manga("a777428a-c3a4-4f14-8ca3-6f8fa406b00b", "Chainsaw Man")
