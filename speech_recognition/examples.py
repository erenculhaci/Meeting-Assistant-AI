"""
Example usage of the Groq-based Speech Recognition module
"""

from speech_recognition import Transcriber
import os
from pathlib import Path

# Proje kök dizinini bul
project_root = Path(__file__).parent.parent
os.chdir(project_root)

print("Speech Recognition Example (Groq Whisper API)")
print("=" * 50)

# Transcriber oluştur
print("\n1. Creating transcriber...")
transcriber = Transcriber()

# Ses dosyası yolu
input_file = "speech_recognition/samples/sample1.wav"

if not Path(input_file).exists():
    print(f"Error: Sample file not found: {input_file}")
    print("Please add a sample audio file to speech_recognition/samples/")
    exit(1)

# Transkripsiyon yap
print(f"\n2. Transcribing: {input_file}")
result = transcriber.transcribe(
    input_path=input_file,
    language=None,  # Auto-detect
    detect_speakers=True
)

# Sonuçları göster
print("\n3. Results:")
print(f"   Status: success")
print(f"   Duration: {result.duration:.1f} seconds")
print(f"   Language: {result.language}")
print(f"   Model: {result.model}")
print(f"   Processing Time: {result.processing_time:.1f} seconds")

print("\n4. Transcript (first 10 segments):")
for seg in result.segments[:10]:
    speaker = f"[{seg.speaker}]" if seg.speaker else ""
    print(f"   {speaker} {seg.text}")

# JSON ve SRT olarak kaydet
print("\n5. Saving output files...")
output_dir = "outputs/transcription"
Path(output_dir).mkdir(parents=True, exist_ok=True)

saved_files = transcriber.transcribe_and_save(
    input_path=input_file,
    output_dir=output_dir,
    formats=["json", "srt"],
    detect_speakers=True
)

print("\n" + "=" * 50)
for fmt, path in saved_files.items():
    print(f"Saved {fmt.upper()}: {path}")
