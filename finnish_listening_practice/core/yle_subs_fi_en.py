import subprocess
import sys
from pathlib import Path
import re

# ================= CONFIG =================
DESTDIR = Path.home() / "Downloads" / "Yle"
WHISPER_MODEL = "small"   # base | small | medium
LANG_FI = "fi"
LANG_EN = "en"
# =========================================

DESTDIR.mkdir(parents=True, exist_ok=True)


def run(cmd):
    print("RUN:", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True)


def clean_srt_to_txt(srt_path: Path, txt_path: Path):
    lines = []
    for line in srt_path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^\d+$", line):
            continue
        if re.match(r"\d{2}:\d{2}:\d{2},\d{3}\s-->\s", line):
            continue
        if line.strip():
            lines.append(line.strip())
    txt_path.write_text("\n".join(lines), encoding="utf-8")


def extract_finnish_subs(video: Path) -> Path | None:
    fi_srt = video.with_suffix(".fi.srt")

    try:
        run([
            "ffmpeg", "-y",
            "-i", video,
            "-map", "0:s:m:language:fin",
            fi_srt
        ])
        if fi_srt.exists():
            return fi_srt
    except subprocess.CalledProcessError:
        pass

    # Fallback: first subtitle track
    fallback = video.with_suffix(".srt")
    try:
        run([
            "ffmpeg", "-y",
            "-i", video,
            "-map", "0:s:0",
            fallback
        ])
        if fallback.exists():
            fallback.rename(fi_srt)
            return fi_srt
    except subprocess.CalledProcessError:
        return None

    return None


def whisper_translate(fi_srt: Path):
    run([
        "whisper",
        str(fi_srt),
        "--model", WHISPER_MODEL,
        "--language", LANG_FI,
        "--task", "translate",
        "--output_format", "srt",
        "--output_dir", str(fi_srt.parent)
    ])


def process_video(video: Path):
    print("\nProcessing video:", video.name)

    fi_srt = extract_finnish_subs(video)
    if not fi_srt:
        print("No subtitle stream found")
        return

    print("Finnish subtitles extracted")

    fi_txt = video.with_suffix(".fi.txt")
    clean_srt_to_txt(fi_srt, fi_txt)

    print("Finnish transcript created")

    whisper_translate(fi_srt)

    en_srt = video.with_suffix(".en.srt")
    whisper_out = video.with_suffix(".srt")
    if whisper_out.exists():
        whisper_out.rename(en_srt)

        en_txt = video.with_suffix(".en.txt")
        clean_srt_to_txt(en_srt, en_txt)

        print("English subtitles and transcript created")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python yle_subs_fi_en.py <areena-url>")
        print("  python yle_subs_fi_en.py urls.txt")
        sys.exit(1)

    arg = Path(sys.argv[1])

    if arg.exists():
        urls = [u.strip() for u in arg.read_text(encoding="utf-8").splitlines() if u.strip()]
    else:
        urls = [sys.argv[1]]

    for url in urls:
        print("\nDownloading from Yle:", url)
        run([
            "yle-dl",
            "--destdir", str(DESTDIR),
            "--resolution", "1080",
            url
        ])

    for video in DESTDIR.glob("*.mkv"):
        process_video(video)


if __name__ == "__main__":
    main()
