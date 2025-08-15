from docx import Document
from tts import chatterbox_tts
import time
def extract_text_from_docx(filepath: str) -> str:
    """
    Extracts all text from a one-page .docx file and returns it as a single string.

    Args:
        filepath (str): The path to the .docx file.

    Returns:
        str: The extracted text as a single string.
    """
    doc = Document(filepath)
    text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    return text

# Example usage
if __name__ == "__main__":
    filepath = "C:/Users/Ruslan/Downloads/John Walton Audiobook/SilencingAmbiPage1.docx"  # Replace with the actual path
    extracted_text = extract_text_from_docx(filepath)
    start_time = time.time()
    chatterbox_tts(text = extracted_text[:1158], 
                   output_path= "SilencingAmbiPage1(2).wav", 
                   voice_sample_path="C:/Users/Ruslan/Downloads/John Walton Audiobook/20250720_155854.wav", from_voice=False,
                   exaggeration=0.5, cfg_weight=0.3)
    end_time = time.time()
    print("total execution time " + str(end_time - start_time))
