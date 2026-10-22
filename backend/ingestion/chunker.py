from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_documents(docs: list[dict], chunk_size: int = 500, chunk_overlap: int = 75) -> list[dict]:
    """Нарезает длинные тексты документов на более мелкие чанки."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    all_chunks = []
    for doc in docs:
        texts = splitter.split_text(doc.get("body", ""))
        
        for i, text in enumerate(texts):
            chunk = doc.copy()
            chunk["chunk_id"] = f"{doc.get('doc_id', 'unknown')}_c{i}"
            chunk["text"] = text
            
            if "body" in chunk:
                del chunk["body"]
                
            all_chunks.append(chunk)
            
    return all_chunks