#!/usr/bin/env python3
"""
Stems Downloader & DSP Signal Analyzer for 'No Lo Entiende'
Uses browser_cookie3 to fetch Google Drive files and librosa/soundfile for DSP audio analysis.
"""

import os
import sys
import json
import time
import requests
import browser_cookie3
import librosa
import numpy as np
import soundfile as sf

STEMS_MANIFEST = [
    ("1MytyjWT-M2Ci38mS7yRPri0S1_079kkG", "01_kick_selections.wav", "Kick Drums"),
    ("1ZbyMYutK6mk0YboCGG5M6JDCAl-e9xjF", "02_teddy_pendergrass_sample.wav", "Teddy Pendergrass Sample"),
    ("1CQZNpxUCqEqstWizrbDXTB4JfISxD6DL", "03_bass.wav", "Bassline"),
    ("1_JkRWguLFcGj_fJ5C7yA3R-9-7b6ymFi", "04_claps.wav", "Claps"),
    ("1hlEAA_3SEWcYbLrX8jks5m0G5Wrj-l9Y", "05_dub_synth_2.wav", "Dub Synth 2"),
    ("1UdHMPH_rgjla5SwQos3SwCQIsF4FNb0R", "06_dub_synth_1.wav", "Dub Synth 1"),
    ("1_Qkp88ALcVBXrArj7vq-1ndBMVHYvv9E", "07_low_end.wav", "Low End Sub"),
    ("1dJhFq2XB3fGBzkFaP_LSmPFRBBNUqst1", "08_shaker_2.wav", "Shaker 2"),
    ("1uItVVL23Zpy5MbfsI6mGklWER-Ji6YMe", "09_shakers.wav", "Shakers Loop"),
    ("1lDPrVeeZjJgVKdGbtIWB1ASTL2vfupdG", "10_sinte_prin.wav", "Main Synth"),
    ("1sFSXlMkCV0lp_HW_yjQOzEksKhq7FtOs", "11_top_loop.wav", "Top Loop"),
    ("1wTHVR5g42UfwbCmLlZMzw2BIexBnNbKV", "12_track_masterizado.wav", "Master Track")
]

TARGET_DIR = os.path.expanduser("~/10_PROJECTS/No_Lo_Entiende_Stems")

def get_authenticated_session():
    session = requests.Session()
    try:
        cj = browser_cookie3.chrome(domain_name='google.com')
        session.cookies = cj
    except Exception as e:
        print(f"[Warning] Failed to load Chrome cookies, trying Brave: {e}")
        cj = browser_cookie3.brave(domain_name='google.com')
        session.cookies = cj
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    return session

def download_stems(session):
    os.makedirs(TARGET_DIR, exist_ok=True)
    downloaded_files = []

    for file_id, filename, label in STEMS_MANIFEST:
        dest_path = os.path.join(TARGET_DIR, filename)
        if os.path.exists(dest_path) and os.path.getsize(dest_path) > 100000:
            print(f"[Exist] {filename} already downloaded ({os.path.getsize(dest_path) / (1024*1024):.2f} MB)")
            downloaded_files.append((dest_path, label))
            continue

        url = f"https://drive.google.com/uc?id={file_id}&export=download"
        print(f"[Downloading] {label} ({filename})...")
        res = session.get(url, allow_redirects=True, stream=True)

        if res.status_code == 200 and ('audio' in res.headers.get('Content-Type', '') or 'octet-stream' in res.headers.get('Content-Type', '')):
            with open(dest_path, 'wb') as f:
                for chunk in res.iter_content(65536):
                    if chunk:
                        f.write(chunk)
            print(f"[Success] Saved {filename} ({os.path.getsize(dest_path) / (1024*1024):.2f} MB)")
            downloaded_files.append((dest_path, label))
        else:
            # Check for large file warning page redirect
            confirm_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"
            res2 = session.get(confirm_url, allow_redirects=True, stream=True)
            if res2.status_code == 200:
                with open(dest_path, 'wb') as f:
                    for chunk in res2.iter_content(65536):
                        if chunk:
                            f.write(chunk)
                print(f"[Success Direct] Saved {filename} ({os.path.getsize(dest_path) / (1024*1024):.2f} MB)")
                downloaded_files.append((dest_path, label))
            else:
                print(f"[Error] Failed to download {filename}: HTTP {res.status_code}")

    return downloaded_files


def analyze_audio_stem(file_path, label):
    print(f"[Analyzing DSP] {label}...")
    y, sr = librosa.load(file_path, sr=None, mono=False)
    
    is_stereo = (y.ndim > 1 and y.shape[0] == 2)
    mono_y = librosa.to_mono(y) if is_stereo else y
    
    duration = librosa.get_duration(y=mono_y, sr=sr)
    rms = float(np.sqrt(np.mean(mono_y**2)))
    rms_db = 20 * np.log10(rms + 1e-9)
    peak = float(np.max(np.abs(mono_y)))
    peak_db = 20 * np.log10(peak + 1e-9)
    
    # Spectral Centroid (Brightness)
    spec_cent = float(np.mean(librosa.feature.spectral_centroid(y=mono_y, sr=sr)))
    
    # Stereo Correlation (Phase Coherence) if stereo
    phase_corr = 1.0
    if is_stereo:
        corr_matrix = np.corrcoef(y[0], y[1])
        phase_corr = float(corr_matrix[0, 1])

    # Key/Pitch Detection
    chroma = librosa.feature.chroma_stft(y=mono_y, sr=sr)
    chroma_mean = np.mean(chroma, axis=1)
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    dominant_note = notes[int(np.argmax(chroma_mean))]

    return {
        "label": label,
        "filename": os.path.basename(file_path),
        "duration_sec": round(duration, 2),
        "sample_rate": sr,
        "channels": 2 if is_stereo else 1,
        "peak_db": round(peak_db, 2),
        "rms_db": round(rms_db, 2),
        "spectral_centroid_hz": round(spec_cent, 1),
        "dominant_note": dominant_note,
        "phase_correlation": round(phase_corr, 3)
    }


def main():
    session = get_authenticated_session()
    downloaded = download_stems(session)
    
    analysis_results = []
    for path, label in downloaded:
        res = analyze_audio_stem(path, label)
        analysis_results.append(res)
        
    out_json = os.path.join(TARGET_DIR, "dsp_analysis.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(analysis_results, f, indent=2)

    print("\n" + "="*60)
    print("DSP STEM ANALYSIS REPORT COMPLETE!")
    print("="*60)
    for item in analysis_results:
        print(f"{item['label']:<25} | Peak: {item['peak_db']:>6.1f}dB | RMS: {item['rms_db']:>6.1f}dB | Centroid: {item['spectral_centroid_hz']:>6.0f}Hz | Key: {item['dominant_note']:<2} | Phase: {item['phase_correlation']:>5.2f}")


if __name__ == "__main__":
    main()
