def chunk_text(
    text: str,
    chunk_size: int = 600,
    overlap: int = 150
):
    """
    Improved chunking with overlap for better semantic search.
    Smaller chunks (600) with moderate overlap (150) for more precise retrieval.
    Chunks overlap to preserve context between segments.
    """
    clean_text = " ".join(text.split())

    chunks = []
    start = 0

    while start < len(clean_text):
        end = start + chunk_size
        
        # Try to break at sentence boundaries for better semantic coherence
        if end < len(clean_text):
            # Look for sentence endings in the last 100 characters
            sentence_enders = ['.', '!', '?', '\n']
            best_break = end
            
            for i in range(min(100, chunk_size)):
                check_pos = end - i
                if check_pos < start:
                    break
                if clean_text[check_pos] in sentence_enders:
                    best_break = check_pos + 1
                    break
            
            end = best_break

        chunks.append(clean_text[start:end])
        
        # Move start with overlap
        start = end - overlap if end - overlap > 0 else end

    return chunks