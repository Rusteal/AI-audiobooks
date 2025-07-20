from pdf_to_string import text_pdf_to_string
import os
import torchaudio as ta
from chatterbox.tts import ChatterboxTTS

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
        model="tts-1", #tts-1, tts-1-hd, gpt-4o-mini-tts,
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


def chatterbox_tts(text:str, output_path:str, voice_sample_path: str, from_voice: bool = False, cfg_weight: float = 0.5, exaggeration: float = 0.5):
    """Tips
    General Use (TTS and Voice Agents):

    The default settings (exaggeration=0.5, cfg_weight=0.5) work well for most prompts.
    If the reference speaker has a fast speaking style, lowering cfg_weight to around 0.3 can improve pacing.
    
    Expressive or Dramatic Speech:
    Try lower cfg_weight values (e.g. ~0.3) and increase exaggeration to around 0.7 or higher.
    Higher exaggeration tends to speed up speech; reducing cfg_weight helps compensate with slower, more deliberate pacing."""
    model = ChatterboxTTS.from_pretrained(device="cpu")
    if from_voice:
        wav = model.generate(text, audio_prompt_path=voice_sample_path, cfg_weight=cfg_weight, exaggeration=exaggeration)
    else:
        wav = model.generate(text,  cfg_weight=cfg_weight, exaggeration=exaggeration)
    ta.save(output_path, wav, model.sr)


def split_text_into_n_tokens_chunks(
    text: str,
    model: str = "gpt-4o-mini-tts",
    max_tokens: int = 2000
) -> list[str]:
    """
    Splits text into chunks that stay within the model-specific token limit.

    Args:
        text (str): The input text to split.
        model (str): The TTS model to use ('tts-1', 'tts-1-hd', or 'gpt-4o-mini-tts').
        max_tokens (int): Maximum tokens per chunk.

    Returns:
        List[str]: List of text chunks that do not exceed max_tokens each.
    """
    import tiktoken
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # For TTS models not directly supported, fallback
        encoding = tiktoken.get_encoding("cl100k_base")
        print(f"Could not find the encoding for the model {model}. So the defauld cl100k_base encoder will be used")

    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        # Add word to current chunk
        current_chunk.append(word)
        tokens = encoding.encode(" ".join(current_chunk))
        if len(tokens) > max_tokens:
            # Remove last word and commit chunk
            current_chunk.pop()
            chunks.append(" ".join(current_chunk))
            current_chunk = [word]

    # Add final chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks


def split_text_by_sentences(
    text: str,
    base_limit: int = 3900,
    max_limit: int = 4096,
    sentence_endings: tuple = (".", "!", "?")
) -> list[str]:
    """
    Splits text into chunks up to max_limit characters,
    breaking only at sentence-ending punctuation for TTS-1.

    Args:
        text (str): The input text.
        base_limit (int): Starting cutoff for scanning. Should be a bit below max_limit.
        max_limit (int): Hard max characters per chunk.
        sentence_endings (tuple): Sentence-ending punctuation marks.

    Returns:
        List[str]: List of sentence-based chunks.
    """
    chunks = []

    while text:
        if len(text) <= max_limit:
            # Remaining text fits in one chunk
            chunks.append(text.strip())
            break

        # Start scanning at base_limit
        cutoff = base_limit
        extended = False

        while cutoff < len(text) and cutoff < max_limit:
            if text[cutoff] in sentence_endings:
                # Include the punctuation mark
                cutoff += 1
                extended = True
                break
            cutoff += 1

        # If no sentence-ending punctuation found in range, fallback
        if not extended:
            cutoff = max_limit

        chunk = text[:cutoff].strip()
        chunks.append(chunk)
        text = text[cutoff:].lstrip()  # Remove leading spaces for next round

    return chunks

if __name__ == "__main__":
    # dir = "C:/Users/rusla/Downloads/cambridge-core_the-methodology-of-economics_2Jul2025" #set your directory with pdfs which you would like voice-overed"
    # # counter = 0
    # for file in os.listdir(dir):
    #     if file.endswith("pdf"):
            
    #         text = text_pdf_to_string(dir + "/" + file)
    #         splitted = split_text_by_sentences(text)
    #         for id, chunk in enumerate(splitted):
    #             # if counter >= 1:
    #             #     break
    #             openai_tts(chunk, dir + "/" + file.replace(".pdf", "") + str(id) + ".mp3")
    #             # counter +=1
    import time
    
    start_time = time.time()
    text = "Hello there, I am here testing if chatterbox works at all and how long will it take for it to run"
    chatterbox_tts(text, "output.wav") # works, make sure numpy of proper version is installed
    # NumPy version >=1.21.6 and <1.28.0 detected → good!
    # Very good voice quality. Eve nbetter than cheapest (but not really cheap openai)
    
    end_time = time.time()
    
    print("total execution time " + str(end_time - start_time))
    
    
        