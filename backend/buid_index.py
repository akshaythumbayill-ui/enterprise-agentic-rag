"""
Manual index building script (if needed for testing).
In production, indexes are built automatically via /api/documents/upload endpoint.

Usage:
    from services.document_service import build_index_from_uploaded_pdfs
    result = build_index_from_uploaded_pdfs(user_id=1)
"""

if __name__ == "__main__":
    print(__doc__)