from pathlib import Path
from datetime import datetime

from pypdf import PdfReader

from .index_service import (
    build_index,
    delete_knowledge_base,
)

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"


def get_user_upload_dir(user_id: int):
    return UPLOADS_DIR / "users" / str(user_id)


def chunk_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 150,
):
    clean_text = " ".join(text.split())

    chunks = []
    start = 0

    while start < len(clean_text):
        end = start + chunk_size
        chunks.append(clean_text[start:end])

        if end >= len(clean_text):
            break

        start = end - overlap

    return chunks


def extract_text_from_pdf(pdf_path: Path):
    try:
        reader = PdfReader(str(pdf_path))
    except Exception as error:
        raise ValueError(f"Could not read PDF {pdf_path.name}.") from error

    text = "\n".join(
        page.extract_text() or ""
        for page in reader.pages
    ).strip()

    if not text:
        raise ValueError(
            f"No readable text found in {pdf_path.name}."
        )

    return text


def build_index_from_uploaded_pdfs(user_id: int):
    upload_dir = get_user_upload_dir(user_id)
    pdf_files = sorted(upload_dir.glob("*.pdf"))

    if not pdf_files:
        raise ValueError("You have not uploaded any PDF files yet.")

    documents = []

    for pdf_file in pdf_files:
        text = extract_text_from_pdf(pdf_file)

        for chunk in chunk_text(text):
            documents.append(
                {
                    "filename": pdf_file.name,
                    "content": chunk,
                }
            )

    return build_index(documents, user_id)

def list_uploaded_pdfs(user_id: int):
    upload_dir = get_user_upload_dir(user_id)

    if not upload_dir.exists():
        return []

    return [
        {
            "filename": pdf_file.name,
            "size_bytes": pdf_file.stat().st_size,
            "uploaded_at": datetime.fromtimestamp(
                pdf_file.stat().st_mtime
            ).isoformat(),
        }
        for pdf_file in sorted(upload_dir.glob("*.pdf"))
    ]


def delete_uploaded_pdf(user_id: int, filename: str):
    safe_filename = Path(filename).name

    if safe_filename != filename or not filename.lower().endswith(".pdf"):
        raise ValueError("Invalid PDF filename.")

    upload_dir = get_user_upload_dir(user_id)
    pdf_path = upload_dir / safe_filename

    if not pdf_path.exists():
        raise FileNotFoundError("PDF file was not found.")

    pdf_path.unlink()

    remaining_files = list(upload_dir.glob("*.pdf"))

    if remaining_files:
        index_result = build_index_from_uploaded_pdfs(user_id)

        return {
            "message": "PDF deleted and knowledge base re-indexed.",
            "documents_indexed": index_result["documents_indexed"],
        }

    delete_knowledge_base(user_id)

    return {
        "message": "PDF deleted. Your knowledge base is now empty.",
        "documents_indexed": 0,
    }