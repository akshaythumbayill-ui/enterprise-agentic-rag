import pymupdf


def extract_text_from_pdf(pdf_path: str):

    document = pymupdf.open(pdf_path)

    full_text = ""

    for page in document:
        full_text += page.get_text()

    return full_text