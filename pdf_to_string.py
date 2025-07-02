def text_pdf_to_string(pdf_filepath: str) -> str:
    """
    Extract text from a text-based PDF file.

    This function uses PyPDF2 (or pypdf) to extract text from each page of the PDF.
    It works best for PDFs that contain selectable text (not scanned images).

    Args:
        pdf_filepath (str): Path to the PDF file.

    Returns:
        str: The full extracted text from the PDF, concatenated page by page.
    """
    from PyPDF2 import PdfReader
    reader = PdfReader(pdf_filepath)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def image_pdf_to_string(pdf_filepath: str) -> str: #have not been tested/ draft
    """
    Extract text from an image-based (scanned) PDF using OCR.

    This function converts each page of a scanned PDF to an image,
    then uses Tesseract OCR to extract text from each image.

    Args:
        pdf_filepath (str): Path to the scanned PDF file.

    Returns:
        str: The full extracted text from the scanned PDF, page by page.
    """
    from pdf2image import convert_from_path
    import pytesseract # do not forget to install pytheseract from thier website, set a path variable for it to work if you are from a windows machine

    pages = convert_from_path(pdf_filepath)
    text = ""
    for page in pages:
        text += pytesseract.image_to_string(page)
    return text


if __name__ == "__main__":
    print(text_pdf_to_string("04.0_pp_xxv_xxviii_Preface_to_first_edition.pdf"))