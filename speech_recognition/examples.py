from transcriber import transcribe_meeting, MeetingTranscriber

transcriber = MeetingTranscriber(
    model_name="base",
    enable_speaker_diarization=True
)

result = transcribe_meeting(
    "./samples/sample1.wav",
    model_name="medium",
    enable_speaker_diarization=True,
    output_format="srt",
    output_file="./outputs/meeting_transcript.srt"
)