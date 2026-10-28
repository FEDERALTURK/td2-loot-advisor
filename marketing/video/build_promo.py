"""Render the TD2 Loot Advisor narrated promo from local project files."""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
WORK = OUT / ".work"
W, H, FPS = 1920, 1080, 24
VOICE_PYTHON = Path.home() / "AppData/Local/Programs/Python/Python313/python.exe"
VOICE = "tr-TR-EmelNeural"
VOICE_RATE = "+0%"
VOICE_PITCH = "+0Hz"
VOICE_SUFFIX = VOICE.rsplit("-", 1)[-1].lower()
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
ORANGE = (255, 122, 26)
GOLD = (255, 195, 74)
GREEN = (152, 194, 117)
WHITE = (240, 238, 232)
MUTED = (169, 166, 156)
FONT_HEAD = r"C:\Windows\Fonts\bahnschrift.ttf"
FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_BODY = r"C:\Windows\Fonts\segoeui.ttf"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def wrap(draw: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines: list[str] = []
    line = ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if line and draw.textbbox((0, 0), candidate, font=f)[2] > max_width:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


def text_block(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str,
               f: ImageFont.FreeTypeFont, fill: tuple[int, int, int], width: int,
               spacing: int = 10) -> int:
    x, y = xy
    for line in wrap(draw, text, f, width):
        draw.text((x, y), line, font=f, fill=fill)
        y += f.size + spacing
    return y


def make_background() -> Image.Image:
    im = Image.new("RGB", (W, H), (14, 15, 14))
    pixels = im.load()
    for y in range(H):
        for x in range(W):
            radial = max(0, 1 - (((x - 1420) / 1050) ** 2 + ((y - 400) / 850) ** 2) ** 0.5)
            glow = int(radial * 17)
            pixels[x, y] = (14 + glow, 15 + int(glow * .5), 14)
    d = ImageDraw.Draw(im, "RGBA")
    for x in range(0, W, 64):
        d.line((x, 0, x, H), fill=(226, 220, 200, 9), width=1)
    for y in range(0, H, 64):
        d.line((0, y, W, y), fill=(226, 220, 200, 9), width=1)
    d.polygon([(0, 0), (610, 0), (0, 280)], fill=(255, 122, 26, 9))
    return im


def corner_marks(d: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color=ORANGE) -> None:
    x1, y1, x2, y2 = box
    n, w = 20, 3
    for x, y, sx, sy in ((x1, y1, 1, 1), (x2, y1, -1, 1), (x1, y2, 1, -1), (x2, y2, -1, -1)):
        d.line((x, y, x + sx * n, y), fill=color, width=w)
        d.line((x, y, x, y + sy * n), fill=color, width=w)


def right_panel(im: Image.Image, d: ImageDraw.ImageDraw, visual: str, t: float) -> None:
    box = (1040, 180, 1775, 770)
    d.rounded_rectangle(box, radius=4, fill=(20, 21, 19), outline=(107, 89, 63), width=2)
    corner_marks(d, box)
    d.text((1080, 205), "TD2 // FIELD DATA", font=font(FONT_BOLD, 18), fill=(153, 149, 137))
    d.text((1695, 205), "LIVE", font=font(FONT_BOLD, 16), fill=GREEN)
    d.line((1080, 245, 1735, 245), fill=(69, 66, 58), width=2)

    if visual in ("intro", "outro"):
        cx, cy = 1407, 485
        for radius, alpha in ((228, 100), (177, 65), (122, 100)):
            d.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), outline=(255, 122, 26, alpha), width=2)
        for a in range(0, 360, 45):
            import math
            rad = math.radians(a + t * 22)
            x1, y1 = cx + int(190 * math.cos(rad)), cy + int(190 * math.sin(rad))
            x2, y2 = cx + int(224 * math.cos(rad)), cy + int(224 * math.sin(rad))
            d.line((x1, y1, x2, y2), fill=ORANGE, width=5)
        icon = Image.open(ROOT / "mobile/store-assets/play-icon-512.png").convert("RGBA")
        icon.thumbnail((245, 245))
        im.paste(icon, (cx-122, cy-122), icon)
        d.text((1245, 690), "ANALİZ  ·  BUILD  ·  KARAR", font=font(FONT_BOLD, 18), fill=WHITE)
    elif visual == "scan":
        d.text((1080, 270), "HIGH-END   /   KNEEPADS", font=font(FONT_BOLD, 16), fill=GOLD)
        d.text((1080, 305), "Fox’s Prayer", font=font(FONT_HEAD, 50), fill=WHITE)
        rows = [("Weapon Damage", "15.0%", 0.96), ("Critical Hit Damage", "8.0%", .73), ("Critical Hit Chance", "6.0%", .58)]
        for i, (name, value, pct) in enumerate(rows):
            y = 400 + i * 79
            d.text((1080, y), name, font=font(FONT_BODY, 21), fill=MUTED)
            d.text((1645, y), value, font=font(FONT_BOLD, 21), fill=WHITE)
            d.rounded_rectangle((1080, y+37, 1710, y+44), radius=3, fill=(57, 55, 49))
            d.rounded_rectangle((1080, y+37, 1080+int(630*pct), y+44), radius=3, fill=ORANGE)
        d.rounded_rectangle((1535, 666, 1715, 726), radius=4, fill=(42, 28, 17), outline=ORANGE, width=2)
        d.text((1579, 674), "F8", font=font(FONT_BOLD, 32), fill=ORANGE)
        d.text((1080, 680), "EKRAN OKUMA TAMAMLANDI", font=font(FONT_BOLD, 15), fill=GREEN)
    elif visual == "build":
        d.text((1080, 274), "STRIKER / DPS BUILD", font=font(FONT_BOLD, 17), fill=GOLD)
        d.text((1080, 318), "Build uyumu", font=font(FONT_HEAD, 35), fill=WHITE)
        d.text((1592, 307), "82%", font=font(FONT_HEAD, 56), fill=GREEN)
        for i, (label, okay) in enumerate((("Set / marka", True), ("Çekirdek özellik", True), ("Kritik hasar", True), ("Göğüs yeteneği", False), ("Sırt çantası yeteneği", True))):
            y = 400 + i * 55
            d.ellipse((1083, y+4, 1109, y+30), fill=(36, 53, 31) if okay else (67, 44, 29), outline=GREEN if okay else ORANGE, width=2)
            if okay:
                d.line((1090, y+17, 1097, y+23, 1103, y+11), fill=GREEN, width=3)
            else:
                d.line((1090, y+17, 1102, y+17), fill=ORANGE, width=3)
            d.text((1130, y), label, font=font(FONT_BODY, 20), fill=WHITE if okay else MUTED)
        d.text((1080, 700), "SON KARAR: SENİN", font=font(FONT_BOLD, 16), fill=ORANGE)
    elif visual == "stash":
        d.text((1080, 270), "AKTİF BUILD  /  ENVANTER", font=font(FONT_BOLD, 16), fill=GOLD)
        slots = ["MASKE", "SIRT", "GÖĞÜSLÜK", "ELDİVEN", "KILIF", "DİZLİK"]
        for i, slot in enumerate(slots):
            x, y = 1080 + (i % 3) * 213, 325 + (i // 3) * 158
            d.rounded_rectangle((x, y, x+190, y+126), radius=3, fill=(28, 29, 26), outline=(77, 74, 65), width=2)
            d.text((x+14, y+14), f"0{i+1}", font=font(FONT_HEAD, 27), fill=ORANGE)
            d.text((x+14, y+59), slot, font=font(FONT_BOLD, 14), fill=WHITE)
            d.text((x+14, y+87), "EŞLEŞME  ✓" if i not in (2, 4) else "EKSİK PARÇA", font=font(FONT_BOLD, 11), fill=GREEN if i not in (2, 4) else GOLD)
        d.text((1080, 665), "SONRAKİ HEDEF", font=font(FONT_BOLD, 13), fill=MUTED)
        d.text((1080, 690), "Göğüslük · chest talent kontrol et", font=font(FONT_BODY, 18), fill=WHITE)
    elif visual == "tasks":
        d.text((1080, 272), "GÖREV TAKİBİ", font=font(FONT_BOLD, 16), fill=GOLD)
        d.text((1080, 316), "Bu haftanın hedefleri", font=font(FONT_HEAD, 38), fill=WHITE)
        items = [("Günlük proje", True), ("Haftalık SHD hedefi", True), ("Manhunt scout", True), ("Sezon görevi", False)]
        for i, (label, done) in enumerate(items):
            y = 393 + i * 66
            d.line((1080, y+51, 1730, y+51), fill=(52, 51, 45), width=1)
            d.ellipse((1084, y+5, 1112, y+33), outline=GREEN if done else ORANGE, width=2)
            if done: d.line((1090, y+19, 1097, y+25, 1107, y+12), fill=GREEN, width=3)
            d.text((1132, y+3), label, font=font(FONT_BODY, 20), fill=WHITE)
            d.text((1650, y+7), "TAMAM" if done else "DEVAM", font=font(FONT_BOLD, 11), fill=GREEN if done else GOLD)
        d.text((1080, 690), "ADIMLAR  ·  İLERLEME  ·  KAYNAKLAR", font=font(FONT_BOLD, 14), fill=MUTED)
    elif visual == "phone":
        d.rounded_rectangle((1280, 268, 1535, 730), radius=29, fill=(9, 10, 9), outline=(136, 127, 108), width=3)
        d.rounded_rectangle((1290, 283, 1525, 715), radius=20, fill=(24, 25, 22))
        d.rounded_rectangle((1365, 289, 1450, 301), radius=6, fill=(71, 68, 60))
        d.text((1315, 326), "TD2 COMPANION", font=font(FONT_BOLD, 15), fill=WHITE)
        d.text((1315, 355), "● DESKTOP BAĞLI", font=font(FONT_BOLD, 10), fill=GREEN)
        d.rounded_rectangle((1310, 397, 1505, 545), radius=4, fill=(34, 35, 31), outline=(67, 66, 58), width=1)
        d.text((1324, 414), "SON TARAMA", font=font(FONT_BOLD, 10), fill=ORANGE)
        d.text((1324, 442), "Ceska Vyroba", font=font(FONT_HEAD, 24), fill=WHITE)
        d.text((1324, 481), "GÖĞÜSLÜK · HIGH-END", font=font(FONT_BOLD, 9), fill=MUTED)
        d.rounded_rectangle((1310, 565, 1505, 624), radius=4, fill=(31, 46, 26), outline=GREEN, width=1)
        d.text((1324, 584), "BUILD’DE KULLAN", font=font(FONT_BOLD, 12), fill=GREEN)
        d.text((1315, 658), "YEREL AĞ  /  SALT OKUNUR", font=font(FONT_BOLD, 9), fill=MUTED)
        d.text((1080, 500), "QR ile eşleştir", font=font(FONT_HEAD, 28), fill=WHITE)
        d.text((1080, 543), "Aynı özel Wi-Fi ağı", font=font(FONT_BODY, 17), fill=MUTED)
        d.text((1550, 500), "TARAMA", font=font(FONT_BOLD, 11), fill=MUTED)
        d.text((1550, 529), "KOMUTU YOK", font=font(FONT_BOLD, 15), fill=GREEN)
    else:  # safety
        cx, cy = 1408, 450
        for r in (210, 160, 105): d.ellipse((cx-r, cy-r, cx+r, cy+r), outline=(255,122,26,60), width=2)
        d.ellipse((cx-62, cy-62, cx+62, cy+62), fill=(42, 32, 21), outline=ORANGE, width=3)
        d.ellipse((cx-34, cy-22, cx+34, cy+22), outline=ORANGE, width=4)
        d.ellipse((cx-9, cy-9, cx+9, cy+9), fill=ORANGE)
        for x, y, label in ((1170, 325, "EKRAN GÖRÜNTÜSÜ"), (1555, 352, "OCR ANALİZİ"), (1180, 580, "BUILD EŞLEŞMESİ"), (1525, 603, "KARAR SENDE")):
            d.rounded_rectangle((x, y, x+185, y+39), radius=3, fill=(28,29,26), outline=(87,75,57), width=1)
            d.text((x+10, y+11), label, font=font(FONT_BOLD, 10), fill=WHITE)
        d.text((1252, 700), "OYUN BELLEĞİNE ERİŞİM YOK", font=font(FONT_BOLD, 15), fill=GREEN)


def render_frame(background: Image.Image, seg: dict, index: int, total: int,
                 t: float, duration: float) -> np.ndarray:
    im = background.copy()
    d = ImageDraw.Draw(im, "RGBA")
    phase = t / max(duration, .1)
    sweep_y = int((phase * 820 + 275) % 820)
    d.line((1010, sweep_y, 1810, sweep_y), fill=(255, 122, 26, 18), width=2)
    # Header and progress markers.
    d.text((84, 55), "TD2", font=font(FONT_HEAD, 30), fill=ORANGE)
    d.text((145, 65), "LOOT ADVISOR", font=font(FONT_BOLD, 15), fill=WHITE)
    d.text((1610, 65), "SAHA BİLGİ SİSTEMİ   /   TANITIM", font=font(FONT_BOLD, 11), fill=(149,146,137))
    d.line((84, 104, 1836, 104), fill=(90,86,75,150), width=1)
    d.text((84, 160), seg["chapter"], font=font(FONT_BOLD, 15), fill=ORANGE)
    d.text((84, 225), f"{index+1:02d}", font=font(FONT_HEAD, 28), fill=(102,99,89))
    d.text((153, 220), "/", font=font(FONT_BODY, 18), fill=(102,99,89))
    d.text((176, 225), f"{total:02d}", font=font(FONT_HEAD, 28), fill=(102,99,89))
    # Emphasized two-line title.
    title_font = font(FONT_HEAD, 67 if len(seg["title"]) < 32 else 56)
    ty = 300
    for line in wrap(d, seg["title"], title_font, 820)[:2]:
        d.text((84, ty), line, font=title_font, fill=WHITE)
        ty += title_font.size + 5
    d.line((84, 495, 154, 495), fill=ORANGE, width=4)
    # Voice-matched narration captions sit in a restrained lower panel.
    d.rounded_rectangle((84, 822, 1836, 1006), radius=3, fill=(10,11,10,228), outline=(72,67,57,200), width=1)
    d.rectangle((84, 822, 90, 1006), fill=ORANGE)
    caption_font = font(FONT_BODY, 27)
    lines = wrap(d, seg["body"], caption_font, 1660)
    cy = 851
    for line in lines[:4]:
        d.text((116, cy), line, font=caption_font, fill=(225,222,213))
        cy += 38
    right_panel(im, d, seg["visual"], t)
    # Progress bar and timecode.
    d.text((84, 1030), "FEDERALTURK  /  BAĞIMSIZ TOPLULUK PROJESİ", font=font(FONT_BOLD, 10), fill=(121,118,109))
    d.text((1745, 1030), f"{index+1:02d}  —  {total:02d}", font=font(FONT_BOLD, 11), fill=MUTED)
    d.rectangle((84, 1060, 1836, 1065), fill=(49,48,43))
    d.rectangle((84, 1060, 84 + int(1752 * (index + phase) / total), 1065), fill=ORANGE)
    return np.asarray(im, dtype=np.uint8)


def probe_duration(path: Path) -> float:
    p = subprocess.run([FFMPEG, "-hide_banner", "-i", str(path), "-f", "null", "-"],
                       capture_output=True, text=True)
    match = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", p.stderr)
    if not match:
        raise RuntimeError(f"Ses süresi okunamadı: {path.name}\n{p.stderr[-1200:]}")
    h, m, s = match.groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def srt_time(seconds: float) -> str:
    ms = round(seconds * 1000)
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def synthesize(text: str, audio: Path, subtitle: Path) -> None:
    cmd = [str(VOICE_PYTHON), "-m", "edge_tts", "--voice", VOICE,
           f"--rate={VOICE_RATE}", f"--pitch={VOICE_PITCH}", "--text", text,
           "--write-media", str(audio), "--write-subtitles", str(subtitle), "--no-progress"]
    last_error = None
    for attempt in range(1, 4):
        audio.unlink(missing_ok=True)
        subtitle.unlink(missing_ok=True)
        try:
            subprocess.run(cmd, check=True, timeout=120, capture_output=True, text=True)
            if audio.exists() and audio.stat().st_size >= 10_000:
                return
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            last_error = exc
        time.sleep(attempt * 2)
    raise RuntimeError(f"Edge Neural TTS üç denemede ses üretmedi: {audio.name}\n{last_error}")


def main() -> None:
    if not VOICE_PYTHON.exists():
        raise FileNotFoundError(f"Edge Neural TTS için Python bulunamadı: {VOICE_PYTHON}")
    WORK.mkdir(parents=True, exist_ok=True)
    segments = json.loads((OUT / "narration_tr.json").read_text(encoding="utf-8"))
    durations: list[float] = []
    segment_files: list[Path] = []
    voice_engine = f"Microsoft Edge Neural / {VOICE}"
    try:
        if os.environ.get("TD2_PROMO_LOCAL_TTS") == "1":
            raise RuntimeError("Yerel ses seçeneği açık")
        for i, seg in enumerate(segments, start=1):
            audio = WORK / f"voice-{i:02d}.mp3"
            subtitle = WORK / f"voice-{i:02d}.srt"
            synthesize(seg["body"], audio, subtitle)
            durations.append(probe_duration(audio))
            segment_files.append(audio)
            print(f"Ses {i}/{len(segments)}: {durations[-1]:.2f} sn — {audio.stat().st_size:,} bayt")
    except Exception as exc:
        if os.environ.get("TD2_PROMO_REQUIRE_NEURAL") == "1":
            raise RuntimeError(f"Neural ses üretilemedi; yerel sesi kullanarak sonucu değiştirmedim. {exc}") from exc
        print(f"Neural ses hizmeti yanıt vermedi; yerel Türkçe ses kullanılacak: {exc}")
        durations.clear()
        segment_files.clear()
        for p in WORK.glob("voice-*.mp3"):
            p.unlink(missing_ok=True)
        for p in WORK.glob("voice-*.wav"):
            p.unlink(missing_ok=True)
        subprocess.run([r"C:\Users\PC\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe",
                        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                        str(OUT / "synthesize_local.ps1"), "-ScriptPath", str(OUT / "narration_tr.json"),
                        "-OutputFolder", str(WORK)], check=True, timeout=240)
        voice_engine = "Microsoft SAPI / Microsoft Tolga (tr-TR), yerel"
        for i in range(1, len(segments) + 1):
            audio = WORK / f"voice-{i:02d}.wav"
            if not audio.exists() or audio.stat().st_size < 20_000:
                raise RuntimeError(f"Yerel ses bölümü boş veya beklenenden küçük: {audio}")
            durations.append(probe_duration(audio))
            segment_files.append(audio)
            print(f"Yerel ses {i}/{len(segments)}: {durations[-1]:.2f} sn — {audio.stat().st_size:,} bayt")

    # Assemble chapter clips without re-encoding their neural narration.
    list_file = WORK / "audio-list.txt"
    list_file.write_text("".join(f"file '{p.as_posix()}'\n" for p in segment_files), encoding="utf-8")
    narration = OUT / f"td2-loot-advisor-seslendirme-tr-{VOICE_SUFFIX}.mp3"
    subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(list_file), "-c:a", "libmp3lame", "-q:a", "2", str(narration)], check=True)

    # Render title cards and feature scenes, using the duration of each matching spoken section.
    bg = make_background()
    silent_video = WORK / "promo-silent.mp4"
    writer = imageio_ffmpeg.write_frames(str(silent_video), (W, H), fps=FPS,
        codec="libx264", pix_fmt_in="rgb24", pix_fmt_out="yuv420p", macro_block_size=2,
        output_params=["-crf", "18", "-preset", "fast", "-an"])
    writer.send(None)
    for i, (seg, duration) in enumerate(zip(segments, durations)):
        count = max(1, round(duration * FPS))
        for frame_no in range(count):
            writer.send(render_frame(bg, seg, i, len(segments), frame_no / FPS, duration))
        print(f"Görüntü {i+1}/{len(segments)}: {duration:.2f} sn")
    writer.close()

    final = OUT / f"td2-loot-advisor-tanitim-tr-{VOICE_SUFFIX}.mp4"
    subprocess.run([FFMPEG, "-y", "-hide_banner", "-loglevel", "error", "-i", str(silent_video), "-i", str(narration),
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", "-movflags", "+faststart", str(final)], check=True)

    # Voice-matched readable subtitles: one caption per chapter, with timings aligned to each generated clip.
    blocks, cursor = [], 0.0
    for i, (seg, duration) in enumerate(zip(segments, durations), start=1):
        start = max(0, cursor)
        end = cursor + duration
        blocks.append(f"{i}\n{srt_time(start)} --> {srt_time(end)}\n{seg['body']}\n")
        cursor = end
    subtitle_path = OUT / f"td2-loot-advisor-tanitim-tr-{VOICE_SUFFIX}.srt"
    subtitle_path.write_text("\n".join(blocks), encoding="utf-8-sig")
    voice_settings = (f"Edge Neural, rate {VOICE_RATE}, pitch {VOICE_PITCH}" if voice_engine.startswith("Microsoft Edge")
                      else "Windows SAPI, rate -1")
    info_path = OUT / f"voiceover-info-{VOICE_SUFFIX}.txt"
    info_path.write_text(
        f"Ses motoru: {voice_engine}\nSes uzunluğu: {sum(durations):.2f} saniye\nOkuma ayarı: {voice_settings}\n",
        encoding="utf-8")

    print(f"BİTTİ: {final} ({final.stat().st_size:,} bayt)")
    print(f"Süre: {sum(durations):.2f} sn | Ses: {narration.stat().st_size:,} bayt | Altyazı: {subtitle_path.stat().st_size:,} bayt | {info_path.name}")


if __name__ == "__main__":
    main()
