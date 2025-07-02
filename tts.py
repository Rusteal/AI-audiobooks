from pdf_to_string import text_pdf_to_string
import os
def eleven_labs_tts(): # have not been tested/ too big costs
    from elevenlabs import ElevenLabs

    client = ElevenLabs(
        api_key="YOUR_API_KEY",
    )
    client.text_to_speech.convert(
        voice_id="ybXKpLSv6Tnlmoczge4o", #Steve - Neutral British Narration
        output_format="mp3_44100_128",
        text="The first move is what sets everything in motion.",
        model_id="eleven_multilingual_v2",
    ) #where does it save the output? can i set sesific path?
    
def openai_tts(text: str, output_path: str):
    import os
    #from pathlib import Path
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    #speech_file_path = Path(__file__).parent / "speech.mp3"

    instructions = """
    Voice Affect: Calm, measured, and warmly engaging; convey awe and quiet reverence for the natural world.

    Tone: Inquisitive and insightful, with a gentle sense of wonder and deep respect for the subject matter.

    Pacing: Even and steady, with slight lifts in rhythm when introducing a new species or unexpected behavior; natural pauses to allow the viewer to absorb visuals.

    Emotion: Subtly emotive—imbued with curiosity, empathy, and admiration without becoming sentimental or overly dramatic.

    Emphasis: Highlight scientific and descriptive language (“delicate wings shimmer in the sunlight,” “a symphony of unseen life,” “ancient rituals played out beneath the canopy”) to enrich imagery and understanding.

    Pronunciation: Clear and articulate, with precise enunciation and slightly rounded vowels to ensure accessibility and authority.

    Pauses: Insert thoughtful pauses before introducing key facts or transitions (“And then... with a sudden rustle...”), allowing space for anticipation and reflection.
    """
    
    with client.audio.speech.with_streaming_response.create( # configure voice, good exmaple https://cookbook.openai.com/examples/gpt_with_vision_for_video_understanding
        model="gpt-4o-mini-tts",
        voice="echo", # could be alloy, ash, ballad, coral, echo, fable, nova, onyx, sage, shimmer
        input=text,
        instructions=instructions,
        response_format="mp3"
    ) as response:
        response.stream_to_file(output_path)
    # audio_response = client.audio.speech.create(
    # model="gpt-4o-mini-tts",
    # voice="echo",
    # instructions=instructions,
    # input=result.output_text,
    # response_format="wav"
    # )

    # audio_bytes = audio_response.content
    # Audio(data=audio_bytes)
    # audio_response = response = client.audio.speech.create(
    # model="gpt-4o-mini-tts",
    # voice="echo",
    # instructions=instructions,
    # input=result.output_text,
    # response_format="wav"
    # )

    # audio_bytes = audio_response.content
    # Audio(data=audio_bytes)
    
    
if __name__ == "__main__":
    dir = "cambridge-core_the-methodology-of-economics_2Jul2025" #set your directory with pdfs which you would like voice-overed
    #counter = 0
    for file in os.listdir(dir):
        # if counter >= 1:
        #     break
        openai_tts(text_pdf_to_string(dir + "/" + file), dir+ "/" +  file.replace(".pdf", ".mp3"))
        #counter +=1
    
    
        