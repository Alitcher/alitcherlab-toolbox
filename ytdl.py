from yt_dlp import YoutubeDL
from pathlib import Path

def normalize_url(url: str) -> str:
    # Convert Shorts to standard watch URL (avoids some edge cases)
    if "youtube.com/shorts/" in url and "?v=" not in url:
        vid = url.split("shorts/")[1].split("?")[0].split("/")[0]
        return f"https://www.youtube.com/watch?v={vid}"
    return url

def list_available_subs(url: str, cookiefile: str | None):
    opts = {
        "quiet": True,
        "skip_download": True,
    }
    if cookiefile:
        opts["cookiefile"] = cookiefile
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    # Collect manual + auto subs
    sub_map = {}
    if info.get("subtitles"):
        for lang, tracks in info["subtitles"].items():
            sub_map.setdefault(lang, set())
            for t in tracks:
                sub_map[lang].add(t.get("ext"))
    if info.get("automatic_captions"):
        for lang, tracks in info["automatic_captions"].items():
            sub_map.setdefault(lang, set())
            for t in tracks:
                sub_map[lang].add(t.get("ext"))
    return {k: sorted(v) for k, v in sorted(sub_map.items())}

def main():
    url = input("Paste YouTube URL: ").strip()
    out = input("Output folder (Enter for current): ").strip() or "."
    url = normalize_url(url)
    out_path = Path(out)
    out_path.mkdir(parents=True, exist_ok=True)

    print("\nWhat do you want to download?")
    print("1. Video + Subtitles")
    print("2. Video only")
    print("3. Subtitles only")
    choice = input("Enter choice (1/2/3): ").strip()

    # If you exported cookies (e.g., with 'Get cookies.txt LOCALLY'), place cookies.txt next to this script.
    cookiefile = "cookies.txt" if Path("cookies.txt").exists() else None

    # Show available subtitle languages first (helps avoid 429 on missing language)
    try:
        subs = list_available_subs(url, cookiefile)
        if subs:
            print("\nAvailable subtitle languages (manual/auto):")
            for lang, exts in subs.items():
                print(f"  {lang}  ({', '.join(exts)})")
        else:
            print("\nNo subtitles listed by YouTube for this video (manual or auto).")
    except Exception as e:
        print(f"\n(Info) Could not list subs first: {e}")

    # Ask for desired subtitle languages (comma separated). Tip: try 'fi' for Finnish videos.
    sub_langs = input("\nSubtitle languages (e.g., 'en' or 'en,fi'; Enter for 'en'): ").strip() or "en"
    # yt-dlp accepts patterns too, like 'en.*,fi'
    langs = [s.strip() for s in sub_langs.split(",") if s.strip()]

    # Base yt-dlp options
    opts = {
        "outtmpl": f"{out}/%(title)s.%(ext)s",
        "noprogress": False,
        "quiet": False,
        # Be gentle to avoid 429
        "retries": 5,
        "fragment_retries": 5,
        "sleep_requests": 2,            # short pause between requests
        "concurrent_fragment_downloads": 5,
        # Prefer MP4 container for merged outputs
        "merge_output_format": "mp4",
        # Try browser impersonation if available (optional; comment out if noisy)
        # "impersonate": "chrome",   # requires extra deps; safe to leave commented
    }
    if cookiefile:
        opts["cookiefile"] = cookiefile

    if choice == "1":  # video + subs
        opts.update({
            "format": "bv*+ba/b",
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": langs,
            "subtitlesformat": "srt",  # srt or vtt
        })
    elif choice == "2":  # video only
        opts.update({
            "format": "bv*+ba/b",
        })
    elif choice == "3":  # subtitles only
        opts.update({
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": langs,
            "subtitlesformat": "srt",
        })
    else:
        print(":( Invalid choice. Exiting.")
        return

    # Download
    try:
        with YoutubeDL(opts) as ydl:
            ydl.download([url])
        print(":) Done.")
    except Exception as e:
        print(f":( Download error: {e}")
        if "429" in str(e):
            print("Tip: 429 = rate limited. Try adding cookies.txt, using fewer languages, or rerun later.")

if __name__ == "__main__":
    main()
