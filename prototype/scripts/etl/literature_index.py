#!/usr/bin/env python3
"""
Index PubMed abstracts in ChromaDB for literature-based drug repurposing.
Creates a vector database of PubMed abstracts for semantic search.

Note: This requires chromadb to be installed: pip install chromadb
"""
import json
from pathlib import Path

import structlog

logger = structlog.get_logger()


def create_literature_index(raw_dir: Path, data_dir: Path) -> None:
    """Index PubMed abstracts in ChromaDB."""
    chroma_dir = data_dir / "chroma_db"
    chroma_dir.mkdir(parents=True, exist_ok=True)

    # Load publications
    jsonl_path = raw_dir / "pubmed_npc.jsonl"
    if not jsonl_path.exists():
        logger.warning("pubmed_file_missing", path=str(jsonl_path))
        return

    publications = []
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                publications.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not publications:
        logger.warning("pubmed_no_publications")
        return

    # Try to use ChromaDB
    try:
        import chromadb
        from chromadb.utils import embedding_functions

        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path=str(chroma_dir))

        # Use a lightweight embedding model
        ef = embedding_functions.DefaultEmbeddingFunction()

        # Create collection
        collection = client.get_or_create_collection(
            name="pubmed_abstracts",
            embedding_function=ef,
            metadata={"description": "PubMed abstracts for rare disease drug repurposing"},
        )

        # Prepare documents
        documents = []
        metadatas = []
        ids = []

        for pub in publications:
            # Create document text
            doc_text = f"{pub['title']}. {pub['abstract']}"
            documents.append(doc_text)

            metadatas.append({
                "pmid": pub["pmid"],
                "title": pub["title"],
                "year": pub["year"],
                "journal": pub["journal"],
                "disease_ids": ",".join(pub.get("disease_ids", [])),
                "drug_names": ",".join(pub.get("drug_names", [])),
            })
            ids.append(pub["pmid"])

        # Add to collection
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )

        count = collection.count()
        logger.info("chroma_index_created", documents=count, path=str(chroma_dir))
        print(f"  ✓ ChromaDB index created: {count} documents")

    except ImportError:
        logger.warning("chromadb_not_installed")
        print("  ⚠️  ChromaDB not installed. Creating JSON index instead.")

        # Fallback: create a simple JSON index
        index = {
            "publications": publications,
            "total": len(publications),
            "note": "Install chromadb for vector search: pip install chromadb",
        }
        with open(chroma_dir / "literature_index.json", "w") as f:
            json.dump(index, f, indent=2)

        logger.info("json_index_created", publications=len(publications))

    # Also save a processed version for easy access
    processed_dir = data_dir / "processed" / "pubmed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    with open(processed_dir / "pubmed_index.json", "w") as f:
        json.dump({"publications": publications, "total": len(publications)}, f, indent=2)


def main() -> None:
    import sys
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./prototype/data")
    raw_dir = data_dir / "raw" / "pubmed"

    print("📚 Indexing literature in ChromaDB...")
    create_literature_index(raw_dir, data_dir)
    print(f"\nLiterature index complete. Output: {data_dir / 'chroma_db'}")


if __name__ == "__main__":
    main()
