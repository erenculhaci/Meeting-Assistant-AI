from transcriber import transcribe_meeting, MeetingTranscriber

transcriber = MeetingTranscriber(
    model_name="base",
    enable_speaker_diarization=True
)

result = transcribe_meeting(
    "./samples/marketing_meeting.mp3",
    model_name="medium",
    enable_speaker_diarization=True,
    output_format="json",
    output_file="./outputs/meeting_transcript2.json"
)