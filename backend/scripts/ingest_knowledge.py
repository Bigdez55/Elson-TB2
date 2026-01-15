#!/usr/bin/env python3
"""
Knowledge Base Ingestion Script

Ingests all wealth management knowledge base files into ChromaDB
for RAG-based retrieval in the Elson Financial AI system.

Usage:
    python backend/scripts/ingest_knowledge.py [--reset]

Options:
    --reset    Clear existing collection before ingesting
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.knowledge_rag import WealthManagementRAG, get_wealth_rag

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main(reset: bool = False):
    """Main ingestion function."""
    logger.info("=" * 60)
    logger.info("Elson Financial AI - Knowledge Base Ingestion")
    logger.info("=" * 60)

    # Get RAG instance
    rag = get_wealth_rag()

    # Check if knowledge base files exist
    knowledge_path = rag.knowledge_base_path
    if not knowledge_path.exists():
        logger.error(f"Knowledge base path not found: {knowledge_path}")
        sys.exit(1)

    json_files = list(knowledge_path.glob("*.json"))
    logger.info(f"Found {len(json_files)} knowledge base files")

    for f in json_files:
        logger.info(f"  - {f.name}")

    # Reset collection if requested
    if reset:
        logger.warning("Resetting collection - deleting existing data...")
        try:
            rag.client.delete_collection(rag.collection_name)
            rag._collection = None  # Reset cached collection
            logger.info("Collection reset successfully")
        except Exception as e:
            logger.warning(f"Could not reset collection: {e}")

    # Get current stats
    stats_before = rag.get_collection_stats()
    logger.info(f"Documents before ingestion: {stats_before.get('total_documents', 0)}")

    # Ingest knowledge base
    logger.info("\nStarting knowledge ingestion...")
    total_chunks = await rag.ingest_knowledge_base(
        chunk_size=500,
        chunk_overlap=50
    )

    # Get stats after
    stats_after = rag.get_collection_stats()
    logger.info(f"\nDocuments after ingestion: {stats_after.get('total_documents', 0)}")
    logger.info(f"New chunks added: {total_chunks}")

    # Test retrieval
    logger.info("\n" + "=" * 60)
    logger.info("Testing retrieval quality...")
    logger.info("=" * 60)

    test_queries = [
        ("What are the key responsibilities of a Trust Protector?", "trust_administration"),
        ("What credentials does a CFP need?", "certifications"),
        ("How does the Dream Team model work for succession?", "succession_planning"),
        ("What are the five pillars of AML compliance?", "compliance_operations"),
        ("How do I create a budget?", "financial_literacy")
    ]

    for query, expected_category in test_queries:
        results = await rag.query(query, n_results=3)

        logger.info(f"\nQuery: {query}")
        logger.info(f"Expected category: {expected_category}")

        if results:
            top_result = results[0]
            logger.info(f"Top result category: {top_result['category']}")
            logger.info(f"Relevance score: {top_result['relevance_score']:.3f}")
            logger.info(f"Content preview: {top_result['content'][:150]}...")

            # Check if expected category is in top results
            categories_found = [r['category'] for r in results]
            if expected_category in categories_found:
                logger.info(f"[PASS] Expected category found in results")
            else:
                logger.warning(f"[WARN] Expected category not in top results. Found: {categories_found}")
        else:
            logger.error(f"[FAIL] No results returned")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Ingestion Summary")
    logger.info("=" * 60)
    logger.info(f"Total documents indexed: {stats_after.get('total_documents', 0)}")
    logger.info(f"Collection: {rag.collection_name}")
    logger.info(f"Embedding model: {rag.embedding_model}")
    logger.info(f"Persist directory: {rag.persist_directory}")
    logger.info("=" * 60)


def validate_knowledge_files():
    """Validate all knowledge base JSON files."""
    rag = WealthManagementRAG()
    knowledge_path = rag.knowledge_base_path

    logger.info("Validating knowledge base files...")
    valid_count = 0
    error_count = 0

    for category, filename in rag.category_files.items():
        filepath = knowledge_path / filename

        if not filepath.exists():
            logger.warning(f"[MISSING] {filename}")
            error_count += 1
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Check for metadata
            if "metadata" not in data:
                logger.warning(f"[WARN] {filename} - missing metadata")
            else:
                version = data["metadata"].get("version", "unknown")
                logger.info(f"[OK] {filename} (v{version})")

            valid_count += 1

        except json.JSONDecodeError as e:
            logger.error(f"[ERROR] {filename} - invalid JSON: {e}")
            error_count += 1

    logger.info(f"\nValidation complete: {valid_count} valid, {error_count} errors")
    return error_count == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest wealth management knowledge base")
    parser.add_argument("--reset", action="store_true", help="Reset collection before ingesting")
    parser.add_argument("--validate", action="store_true", help="Only validate files, don't ingest")
    args = parser.parse_args()

    if args.validate:
        success = validate_knowledge_files()
        sys.exit(0 if success else 1)

    asyncio.run(main(reset=args.reset))
