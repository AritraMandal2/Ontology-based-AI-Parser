import os
import math
import numpy as np
import wave
import subprocess
from PIL import Image, ImageDraw, ImageFont
import imageio
import imageio_ffmpeg

# Resolution and Framerate
WIDTH, HEIGHT = 1280, 720
FPS = 30
DURATION_SEC = 24
TOTAL_FRAMES = FPS * DURATION_SEC

# Output paths
SCRATCH_DIR = "/config/.gemini/antigravity/brain/59a0c50f-a1d4-4083-820e-e17f7f58ac16/scratch"
ARTIFACT_DIR = "/config/.gemini/antigravity/brain/59a0c50f-a1d4-4083-820e-e17f7f58ac16"
os.makedirs(SCRATCH_DIR, exist_ok=True)

AUDIO_PATH = os.path.join(SCRATCH_DIR, "lofi_music.wav")
VIDEO_ONLY_PATH = os.path.join(SCRATCH_DIR, "video_silent.mp4")
FINAL_MP4_PATH = os.path.join(ARTIFACT_DIR, "chromatography_agent_demo.mp4")

# Load Fonts
try:
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    font_subtitle = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    font_code = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 15)
    font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
except Exception:
    font_title = font_subtitle = font_body = font_code = font_small = ImageFont.load_default()

# ---------------------------------------------------------
# 1. Synthesize Upbeat Lo-Fi Background Music (WAV)
# ---------------------------------------------------------
print("Synthesizing Upbeat Lo-Fi Background Music...")
sr = 44100
t_audio = np.linspace(0, DURATION_SEC, int(sr * DURATION_SEC), False)
audio_data = np.zeros_like(t_audio)

beat_sec = 60.0 / 85.0
bar_sec = beat_sec * 4

chords = [
    [261.63, 329.63, 392.00, 493.88],  # Cmaj7
    [220.00, 261.63, 329.63, 392.00, 493.88], # Am9
    [174.61, 220.00, 261.63, 329.63],  # Fmaj7
    [196.00, 246.94, 293.66, 349.23]   # G7
]

for i, sample in enumerate(t_audio):
    bar_num = int((sample % (bar_sec * 4)) / bar_sec)
    chord = chords[bar_num % 4]
    beat_phase = (sample % beat_sec) / beat_sec
    env_chord = np.exp(-1.5 * beat_phase) + 0.3
    
    root_freq = chord[0] / 2.0
    bass = 0.25 * np.sin(2 * np.pi * root_freq * sample) * (np.exp(-2.0 * beat_phase) + 0.2)
    
    rhodes = 0.0
    for f in chord:
        rhodes += 0.08 * np.sin(2 * np.pi * f * sample) + 0.03 * np.sin(4 * np.pi * f * sample)
    rhodes *= env_chord
    
    beat_num = (sample % bar_sec) / beat_sec
    drum = 0.0
    
    if (beat_num % 2.0) < 0.15:
        k_t = beat_num % 2.0
        k_freq = 120.0 * np.exp(-20 * k_t) + 40.0
        drum += 0.35 * np.sin(2 * np.pi * k_freq * sample) * np.exp(-8 * k_t)
        
    if (beat_num % 2.0) > 0.95 and (beat_num % 2.0) < 1.15:
        s_t = (beat_num % 2.0) - 0.95
        noise = (np.random.rand() * 2.0 - 1.0) * np.exp(-15 * s_t)
        drum += 0.22 * noise
        
    sub_beat = (sample % (beat_sec / 2.0)) / (beat_sec / 2.0)
    if sub_beat < 0.08:
        hh = (np.random.rand() * 2.0 - 1.0) * np.exp(-35 * sub_beat)
        drum += 0.08 * hh

    audio_data[i] = bass + rhodes + drum

crackle = (np.random.rand(len(t_audio)) * 2.0 - 1.0) * 0.015
audio_data = (audio_data + crackle)
audio_data = audio_data / np.max(np.abs(audio_data)) * 0.85
audio_pcm = (audio_data * 32767).astype(np.int16)

with wave.open(AUDIO_PATH, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sr)
    wf.writeframes(audio_pcm.tobytes())

print("Audio track saved to:", AUDIO_PATH)

# ---------------------------------------------------------
# 2. Render Video Frames (720p HD)
# ---------------------------------------------------------
print("Rendering Video Frames (720p HD)...")
writer = imageio.get_writer(VIDEO_ONLY_PATH, fps=FPS, codec="libx264")

def draw_glass_card(draw, box, fill=(24, 32, 47, 230), outline=(59, 130, 246, 180)):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle([x1, y1, x2, y2], radius=12, fill=fill, outline=outline, width=2)

def draw_header(draw, title_text):
    draw.rectangle([0, 0, WIDTH, 60], fill=(15, 23, 42))
    draw.line([0, 60, WIDTH, 60], fill=(30, 41, 59), width=2)
    draw.ellipse([20, 20, 36, 36], fill="#F97316")
    draw.text((45, 18), "ChromatographyOntologyAgent", font=font_title, fill=(248, 250, 252))
    draw.text((500, 22), title_text, font=font_subtitle, fill=(148, 163, 184))
    
    draw.rounded_rectangle([1080, 16, 1250, 44], radius=14, fill=(16, 185, 129, 40), outline=(16, 185, 129))
    draw.text((1095, 22), "● GxP ALCOA+", font=font_small, fill=(52, 211, 153))

for frame_idx in range(TOTAL_FRAMES):
    sec = frame_idx / FPS
    img = Image.new("RGB", (WIDTH, HEIGHT), (11, 15, 25))
    draw = ImageDraw.Draw(img, "RGBA")
    
    if sec < 3.0:
        for r in range(50, 600, 80):
            draw.ellipse([WIDTH//2 - r, HEIGHT//2 - r, WIDTH//2 + r, HEIGHT//2 + r], outline=(30, 58, 138, 40), width=1)
            
        draw_glass_card(draw, [240, 180, 1040, 540], fill=(15, 23, 42, 240), outline=(249, 115, 22, 200))
        draw.text((320, 230), "ChromatographyOntologyAgent", font=font_title, fill=(248, 250, 252))
        draw.text((320, 280), "GxP Telemetry Extraction & Central Analyte OKG Visualizer", font=font_subtitle, fill=(148, 163, 184))
        
        draw.rounded_rectangle([320, 340, 480, 375], radius=8, fill=(30, 58, 138), outline=(59, 130, 246))
        draw.text((335, 348), "CFR 21 Part 11", font=font_small, fill=(224, 231, 255))
        
        draw.rounded_rectangle([495, 340, 645, 375], radius=8, fill=(6, 78, 59), outline=(16, 185, 129))
        draw.text((510, 348), "ALCOA++ Verified", font=font_small, fill=(209, 250, 229))

        draw.rounded_rectangle([660, 340, 860, 375], radius=8, fill=(124, 45, 18), outline=(249, 115, 22))
        draw.text((675, 348), "★ Analyte Central Hub", font=font_small, fill=(254, 215, 170))

        draw.text((320, 440), "Initializing Agent Session & Knowledge Graph...", font=font_subtitle, fill=(96, 165, 250))

    elif sec < 11.0:
        draw_header(draw, "Scene 1: Raw Telemetry Ingestion & ALCOA+ Audit")
        
        draw_glass_card(draw, [40, 80, 580, 680], fill=(15, 23, 42, 220), outline=(51, 65, 85))
        draw.text((60, 100), "User Prompt 1", font=font_subtitle, fill=(148, 163, 184))
        
        prompt1 = "Extract, verify and parse raw HPLC telemetry file for Paracetamol\n(Agilent 1290 Infinity II format). Ensure ALCOA+ compliance."
        draw.rounded_rectangle([60, 135, 560, 210], radius=8, fill=(30, 41, 59), outline=(59, 130, 246))
        draw.text((75, 148), prompt1, font=font_body, fill=(248, 250, 252))
        
        rel_t = sec - 4.5
        if rel_t > 0:
            draw.text((60, 230), "Agent Response & Audit Execution:", font=font_subtitle, fill=(52, 211, 153))
            draw_glass_card(draw, [60, 265, 560, 650], fill=(11, 15, 25, 230), outline=(16, 185, 129))
            
            lines = [
                "✔ File: raw_hplc_agilent_1290_paracetamol.tsv",
                "✔ SHA-256: a9f4e21b8c094132... (Logged)",
                "✔ Analyte: Paracetamol (Acetaminophen)",
                "✔ Retention Time (tR): 2.45 min (> 0.0m PASS)",
                "✔ Peak Area: 1,420,500 mAU*s",
                "✔ Peak Height: 185,400 mAU",
                "✔ % RSD: 0.42% (Limit < 2.0% PASS)",
                "✔ USP Plate Count (N): 14,850 (Limit > 2000 PASS)",
                "✔ Tailing Factor (T): 1.08 (Symmetric PASS)",
                "--------------------------------------------------",
                "ALCOA+ STATUS: VERIFIED & GxP AUDITED",
                "Record saved to Firestore & OKG Store."
            ]
            
            num_lines = min(len(lines), int(rel_t * 2.5) + 1)
            y_pos = 280
            for l_idx in range(num_lines):
                col = (52, 211, 153) if "✔" in lines[l_idx] or "VERIFIED" in lines[l_idx] else (203, 213, 225)
                draw.text((75, y_pos), lines[l_idx], font=font_code, fill=col)
                y_pos += 28

        draw_glass_card(draw, [600, 80, 1240, 680], fill=(15, 23, 42, 220), outline=(51, 65, 85))
        draw.text((620, 100), "Live Telemetry Chromatogram Signal", font=font_subtitle, fill=(248, 250, 252))
        
        draw.line([660, 600, 1200, 600], fill=(148, 163, 184), width=2)
        draw.line([660, 200, 660, 600], fill=(148, 163, 184), width=2)
        draw.text((1120, 615), "Time (min)", font=font_small, fill=(148, 163, 184))
        draw.text((600, 180), "mAU", font=font_small, fill=(148, 163, 184))
        
        pts = []
        progress = min(1.0, max(0.0, (sec - 3.5) / 4.0))
        max_x = int(660 + progress * 500)
        for px in range(660, max_x):
            tx = (px - 660) / 500.0 * 5.0
            peak = 350.0 * math.exp(-((tx - 2.45) ** 2) / (2 * (0.15 ** 2)))
            py = int(600 - peak)
            pts.append((px, py))
            
        if len(pts) > 1:
            draw.line(pts, fill=(59, 130, 246), width=3)
            
        if sec > 6.0:
            peak_px = int(660 + (2.45 / 5.0) * 500)
            peak_py = int(600 - 350)
            draw.line([peak_px, peak_py, peak_px, 600], fill=(249, 115, 22), width=1)
            draw.ellipse([peak_px-5, peak_py-5, peak_px+5, peak_py+5], fill="#F97316")
            draw.rounded_rectangle([peak_px+10, peak_py-20, peak_px+190, peak_py+30], radius=6, fill=(30, 41, 59), outline=(249, 115, 22))
            draw.text((peak_px+18, peak_py-14), "★ Paracetamol Peak", font=font_small, fill=(249, 115, 22))
            draw.text((peak_px+18, peak_py+4), "tR = 2.45m | Area = 1.42M", font=font_small, fill=(248, 250, 252))

    elif sec < 20.0:
        draw_header(draw, "Scene 2: Database Lookup, Tool Calls & OKG Graph")
        
        draw_glass_card(draw, [40, 80, 540, 680], fill=(15, 23, 42, 220), outline=(51, 65, 85))
        draw.text((60, 100), "User Prompt 2 (Richer Multi-Tool Request)", font=font_subtitle, fill=(148, 163, 184))
        
        prompt2 = "Query Open Knowledge Graph for Paracetamol across all Agilent,\nWaters & Shimadzu systems. Display central analyte topology\nand trigger Omni 3D video visualization tool."
        draw.rounded_rectangle([60, 135, 520, 225], radius=8, fill=(30, 41, 59), outline=(147, 51, 234))
        draw.text((75, 148), prompt2, font=font_body, fill=(248, 250, 252))
        
        rel_t2 = sec - 12.0
        if rel_t2 > 0:
            draw.text((60, 245), "Tool Executions & Database Query:", font=font_subtitle, fill=(168, 85, 247))
            
            tool_steps = [
                "⚙ Tool Call: get_okg_graph(analyte='Paracetamol')",
                "  └─ Query Firestore: 15 molecules, 20 runs matched",
                "⚙ Tool Call: generate_chromatography_item_video('Paracetamol')",
                "  └─ Vertex AI location='global', model='gemini-omni-flash-preview'",
                "  └─ Saved Playground Artifact: paracetamol_viz.mp4",
                "  └─ Public GCS URL: https://storage.googleapis.com/...",
                "--------------------------------------------------",
                "STATUS: OKG Graph Topology Updated Live!"
            ]
            
            y_pos2 = 275
            for t_idx in range(min(len(tool_steps), int(rel_t2 * 2.0) + 1)):
                col2 = (168, 85, 247) if "Tool Call" in tool_steps[t_idx] else (52, 211, 153) if "Public" in tool_steps[t_idx] or "STATUS" in tool_steps[t_idx] else (203, 213, 225)
                draw.text((75, y_pos2), tool_steps[t_idx], font=font_code, fill=col2)
                y_pos2 += 26

        draw_glass_card(draw, [560, 80, 1240, 680], fill=(15, 23, 42, 220), outline=(249, 115, 22, 180))
        draw.text((580, 100), "Open Knowledge Graph: Central Analyte Topology", font=font_subtitle, fill=(248, 250, 252))
        
        draw.rounded_rectangle([580, 130, 800, 160], radius=6, fill=(249, 115, 22, 40), outline=(249, 115, 22))
        draw.ellipse([590, 140, 602, 152], fill="#F97316")
        draw.text((610, 138), "★ Analyte (Central Hub)", font=font_small, fill=(254, 215, 170))
        
        cx, cy = 900, 380
        
        satellites = [
            ("Agilent 1290 II", "#3B82F6", 140, 0.0),
            ("Waters Acquity", "#10B981", 160, 1.25),
            ("Shimadzu Prominence", "#8B5CF6", 150, 2.5),
            ("Thermo Dionex", "#EC4899", 170, 3.8),
            ("Column: C18 150x4.6", "#EAB308", 145, 5.0)
        ]
        
        angle_offset = sec * 0.4
        
        for name, color, dist, init_angle in satellites:
            ang = init_angle + angle_offset
            sx = cx + int(dist * math.cos(ang))
            sy = cy + int(dist * math.sin(ang))
            draw.line([cx, cy, sx, sy], fill=(100, 116, 139, 180), width=2)
            
            draw.ellipse([sx-16, sy-16, sx+16, sy+16], fill=color, outline=(248, 250, 252), width=2)
            draw.text((sx-30, sy+20), name, font=font_small, fill=(226, 232, 240))
            
        pulse = 4.0 * math.sin(sec * 6.0)
        c_radius = int(28 + pulse)
        draw.ellipse([cx - c_radius - 12, cy - c_radius - 12, cx + c_radius + 12, cy + c_radius + 12], fill=(255, 237, 213, 80))
        draw.ellipse([cx - c_radius, cy - c_radius, cx + c_radius, cy + c_radius], fill="#F97316", outline=(255, 255, 255), width=3)
        draw.text((cx - 55, cy - 8), "★ Paracetamol", font=font_code, fill=(255, 255, 255))
        
        if sec > 16.0:
            draw_glass_card(draw, [960, 180, 1220, 660], fill=(15, 23, 42, 245), outline=(249, 115, 22))
            draw.text((975, 195), "Central Hub Inspector", font=font_subtitle, fill=(249, 115, 22))
            draw.text((975, 225), "Analyte: Paracetamol", font=font_body, fill=(248, 250, 252))
            draw.text((975, 250), "Connected Systems: 4", font=font_small, fill=(148, 163, 184))
            draw.text((975, 270), "Formulas: C8H9NO2", font=font_small, fill=(148, 163, 184))
            draw.text((975, 290), "Mean tR: 2.45 min", font=font_small, fill=(148, 163, 184))
            draw.text((975, 310), "Mean % RSD: 0.42%", font=font_small, fill=(52, 211, 153))
            
            draw.rounded_rectangle([975, 340, 1205, 410], radius=8, fill=(30, 58, 138), outline=(59, 130, 246))
            draw.text((985, 350), "▶ Omni 3D Video Preview", font=font_small, fill=(224, 231, 255))
            draw.text((985, 375), "Generated via Omni Model", font=font_small, fill=(148, 163, 184))

    else:
        draw_glass_card(draw, [200, 140, 1080, 580], fill=(15, 23, 42, 240), outline=(16, 185, 129, 200))
        draw.text((360, 180), "ChromatographyOntologyAgent", font=font_title, fill=(248, 250, 252))
        draw.text((360, 230), "GxP Compliance, OKG Visualization & Omni Video", font=font_subtitle, fill=(148, 163, 184))
        
        summary_items = [
            "✔ 15 Known Molecules Seeded Across 5 Instrument Vendors & Formats",
            "✔ ALCOA++ Audit Trail & CFR 21 Part 11 Compliant Verification Engine",
            "✔ Open Knowledge Graph with Central Analyte Pivoting (#F97316 Coral)",
            "✔ Google Omni Model (gemini-omni-flash-preview) Video Generation",
            "✔ Direct Public Cloud Storage Hosting & Playground Artifact Panel Support"
        ]
        
        y_sum = 280
        for item in summary_items:
            draw.text((260, y_sum), item, font=font_body, fill=(52, 211, 153))
            y_sum += 36

        draw.text((380, 500), "Ready for Production & GxP Platform Integration!", font=font_subtitle, fill=(96, 165, 250))

    writer.append_data(np.array(img))

writer.close()
print("Silent video generated:", VIDEO_ONLY_PATH)

# ---------------------------------------------------------
# 3. Merge Audio + Video using imageio-ffmpeg
# ---------------------------------------------------------
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
cmd = [
    ffmpeg_exe, "-y",
    "-i", VIDEO_ONLY_PATH,
    "-i", AUDIO_PATH,
    "-c:v", "copy",
    "-c:a", "aac",
    "-strict", "experimental",
    FINAL_MP4_PATH
]

print("Merging audio and video using ffmpeg...")
subprocess.run(cmd, check=True)
print("FINAL DEMO VIDEO CREATED SUCCESSFULLY:", FINAL_MP4_PATH)
