"""
Test script for MeetingTranscriber
"""
import json
from speech_recognition import MeetingTranscriber

def test_transcription():
    print("=" * 50)
    print("Testing MeetingTranscriber")
    print("=" * 50)
    
    # Initialize transcriber
    print("\n1. Initializing transcriber (tiny model, no diarization)...")
    transcriber = MeetingTranscriber(
        model_name='tiny',  # Fast for testing
        language=None,  # Auto-detect
        enable_speaker_diarization=False  # Test without diarization first
    )
    print("   ✓ Transcriber initialized")
    
    # Test transcription
    print("\n2. Transcribing sample audio...")
    result = transcriber.transcribe_audio('speech_recognition/samples/sample1.wav')
    
    print(f"\n3. Results:")
    print(f"   Status: {result.get('status')}")
    
    if result.get('status') == 'success':
        print(f"   Duration: {result['metadata']['duration']:.1f} seconds")
        print(f"   Language: {result['metadata']['language']}")
        print(f"   Processing time: {result['metadata']['processing_time']:.2f} seconds")
        print(f"   Segments: {len(result['transcript'])}")
        
        print("\n4. First 3 transcript segments:")
        for i, seg in enumerate(result['transcript'][:3]):
            start = seg.get('start', 0)
            text = seg.get('text', '')[:80]
            print(f"   [{start:.1f}s] {text}")
        
        print("\n5. Full text preview (first 200 chars):")
        print(f"   {result.get('full_text', '')[:200]}...")
    else:
        print(f"   Error: {result.get('message')}")
    
    return result

def test_diarization():
    print("\n" + "=" * 50)
    print("Testing with Speaker Diarization")
    print("=" * 50)
    
    print("\n1. Initializing transcriber with diarization...")
    transcriber = MeetingTranscriber(
        model_name='tiny',
        language=None,
        enable_speaker_diarization=True
    )
    
    if not transcriber.enable_speaker_diarization:
        print("   ⚠ Diarization not available (check HF_ACCESS_TOKEN)")
        return None
    
    print("   ✓ Diarization enabled")
    
    print("\n2. Transcribing with speaker detection...")
    result = transcriber.transcribe_audio(
        'speech_recognition/samples/sample1.wav',
        segment_by_speaker=True
    )
    
    if result.get('status') == 'success':
        print(f"\n3. Results:")
        print(f"   Segments: {len(result['transcript'])}")
        
        # Count unique speakers
        speakers = set()
        for seg in result['transcript']:
            if 'speaker' in seg:
                speakers.add(seg['speaker'])
        
        print(f"   Unique speakers detected: {len(speakers)}")
        if speakers:
            print(f"   Speakers: {sorted(speakers)}")
        
        print("\n4. Segments by speaker:")
        for seg in result['transcript'][:5]:
            speaker = seg.get('speaker', 'Unknown')
            start = seg.get('start', 0)
            text = seg.get('text', '')[:60]
            print(f"   [{speaker}] ({start:.1f}s) {text}")
    else:
        print(f"   Error: {result.get('message')}")
    
    return result

if __name__ == "__main__":
    # Test basic transcription
    result1 = test_transcription()
    
    # Test with diarization
    result2 = test_diarization()
    
    print("\n" + "=" * 50)
    print("Tests completed!")
    print("=" * 50)
