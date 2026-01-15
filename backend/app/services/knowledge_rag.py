"""
Wealth Management RAG (Retrieval-Augmented Generation) Service

This service provides knowledge retrieval capabilities for the Elson Financial AI
wealth management platform using ChromaDB for vector storage and sentence-transformers
for embeddings.

Supports all wealth tiers from $0 to $1B+ with domain-specific knowledge retrieval.
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional
from enum import Enum

try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None

logger = logging.getLogger(__name__)


class AdvisoryMode(str, Enum):
    """Advisory modes for specialized wealth management guidance."""
    GENERAL = "general"
    ESTATE_PLANNING = "estate_planning"
    INVESTMENT_ADVISORY = "investment_advisory"
    TAX_OPTIMIZATION = "tax_optimization"
    SUCCESSION_PLANNING = "succession_planning"
    FAMILY_GOVERNANCE = "family_governance"
    TRUST_ADMINISTRATION = "trust_administration"
    CREDIT_FINANCING = "credit_financing"
    COMPLIANCE_OPERATIONS = "compliance_operations"
    FINANCIAL_LITERACY = "financial_literacy"


class WealthTier(str, Enum):
    """
    Democratized service tiers aligned with US average salary ($66,622/year).

    Design Philosophy: Help clients establish generational wealth EARLY.
    Traditional wealth management gatekeeps advice behind high AUM minimums -
    Elson breaks this barrier with same quality advice for everyone.
    """
    FOUNDATION = "foundation"      # $0-10K - Full CFP access, financial literacy foundation
    BUILDER = "builder"            # $10K-75K - ~1 year median US savings, achievable for most
    GROWTH = "growth"              # $75K-500K - Earlier CFA access for middle-class families
    AFFLUENT = "affluent"          # $500K-5M - Full team for growing wealth
    HNW_UHNW = "hnw_uhnw"          # $5M+ - Family office, philanthropy, specialists


class DecisionAuthority(str, Enum):
    """
    Decision authority levels determining how AI handles role expertise.

    Critical for implementation - not all 70+ roles are treated equally.
    """
    BINDING = "binding"            # Deterministic rules, must be followed (compliance, legal)
    SENIOR_ADVISORY = "senior"     # High-weight recommendations, near-binding
    ADVISORY = "advisory"          # Standard recommendations, user decides
    SUPPORT_ROLE = "support"       # Informational only, background context


class WealthManagementRAG:
    """
    RAG service for wealth management knowledge retrieval.

    Provides semantic search across the comprehensive wealth management
    knowledge base including:
    - Family office structure and operations
    - Professional roles and certifications
    - Estate planning and trust administration
    - Investment governance and strategy
    - Business succession planning
    - Compliance and risk management
    - Financial literacy for beginners
    """

    def __init__(
        self,
        persist_directory: str = "./chroma_db",
        collection_name: str = "wealth_management",
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """
        Initialize the RAG service.

        Args:
            persist_directory: Directory for ChromaDB persistence
            collection_name: Name of the vector collection
            embedding_model: Sentence transformer model for embeddings
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self._client = None
        self._collection = None
        self._embedding_function = None

        # Knowledge base path
        self.knowledge_base_path = Path(__file__).parent.parent / "knowledge_base" / "wealth_management" / "data"

        # Category to file mapping
        self.category_files = {
            "family_office": "family_office_structure.json",
            "professional_roles": "professional_roles.json",
            "certifications": "certifications.json",
            "study_materials": "study_materials.json",
            "estate_planning": "estate_planning.json",
            "trust_administration": "trust_administration.json",
            "financial_advisors": "financial_advisors.json",
            "governance": "governance.json",
            "succession_planning": "succession_planning.json",
            "generational_wealth": "generational_wealth.json",
            "credit_financing": "credit_financing.json",
            "treasury_banking": "treasury_banking.json",
            "compliance_operations": "compliance_operations.json",
            "financial_literacy": "financial_literacy_basics.json"
        }

        # Advisory mode to relevant categories mapping
        self.mode_categories = {
            AdvisoryMode.GENERAL: list(self.category_files.keys()),
            AdvisoryMode.ESTATE_PLANNING: ["estate_planning", "trust_administration", "generational_wealth"],
            AdvisoryMode.INVESTMENT_ADVISORY: ["financial_advisors", "governance", "certifications"],
            AdvisoryMode.TAX_OPTIMIZATION: ["estate_planning", "succession_planning", "compliance_operations"],
            AdvisoryMode.SUCCESSION_PLANNING: ["succession_planning", "professional_roles", "family_office"],
            AdvisoryMode.FAMILY_GOVERNANCE: ["governance", "family_office", "generational_wealth"],
            AdvisoryMode.TRUST_ADMINISTRATION: ["trust_administration", "estate_planning", "professional_roles"],
            AdvisoryMode.CREDIT_FINANCING: ["credit_financing", "treasury_banking"],
            AdvisoryMode.COMPLIANCE_OPERATIONS: ["compliance_operations", "governance"],
            AdvisoryMode.FINANCIAL_LITERACY: ["financial_literacy"]
        }

    @property
    def client(self):
        """Lazy initialization of ChromaDB client."""
        if self._client is None:
            if not CHROMADB_AVAILABLE:
                raise ImportError("chromadb is not installed. Install with: pip install chromadb")
            self._client = chromadb.PersistentClient(path=self.persist_directory)
        return self._client

    @property
    def embedding_function(self):
        """Lazy initialization of embedding function."""
        if self._embedding_function is None:
            if not CHROMADB_AVAILABLE:
                raise ImportError("chromadb is not installed")
            self._embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=self.embedding_model
            )
        return self._embedding_function

    @property
    def collection(self):
        """Lazy initialization of ChromaDB collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    async def query(
        self,
        question: str,
        n_results: int = 5,
        advisory_mode: AdvisoryMode = AdvisoryMode.GENERAL,
        wealth_tier: Optional[WealthTier] = None,
        include_metadata: bool = True
    ) -> list[dict]:
        """
        Retrieve relevant knowledge chunks for a question.

        Args:
            question: The user's question or query
            n_results: Number of results to return
            advisory_mode: The advisory context for filtering
            wealth_tier: Optional wealth tier for context-specific results
            include_metadata: Whether to include source metadata

        Returns:
            List of relevant document chunks with metadata
        """
        try:
            # Build filter based on advisory mode
            where_filter = None
            relevant_categories = self.mode_categories.get(advisory_mode, [])

            if relevant_categories and advisory_mode != AdvisoryMode.GENERAL:
                where_filter = {
                    "category": {"$in": relevant_categories}
                }

            # Add wealth tier filter if specified
            if wealth_tier:
                tier_filter = {"wealth_tier": {"$in": [wealth_tier.value, "all"]}}
                if where_filter:
                    where_filter = {"$and": [where_filter, tier_filter]}
                else:
                    where_filter = tier_filter

            # Query the collection
            results = self.collection.query(
                query_texts=[question],
                n_results=n_results,
                where=where_filter if where_filter else None,
                include=["documents", "metadatas", "distances"] if include_metadata else ["documents"]
            )

            # Format results
            formatted_results = []
            if results and results.get("documents") and results["documents"][0]:
                documents = results["documents"][0]
                metadatas = results.get("metadatas", [[]])[0] if include_metadata else [{}] * len(documents)
                distances = results.get("distances", [[]])[0] if include_metadata else [0] * len(documents)

                for doc, meta, dist in zip(documents, metadatas, distances):
                    formatted_results.append({
                        "content": doc,
                        "metadata": meta or {},
                        "relevance_score": 1 - dist if dist else 1.0,
                        "source": meta.get("source", "unknown") if meta else "unknown",
                        "category": meta.get("category", "general") if meta else "general"
                    })

            logger.info(f"RAG query returned {len(formatted_results)} results for: {question[:50]}...")
            return formatted_results

        except Exception as e:
            logger.error(f"Error querying RAG: {e}")
            return []

    async def add_documents(
        self,
        documents: list[dict],
        batch_size: int = 100
    ) -> int:
        """
        Index documents into the vector store.

        Args:
            documents: List of documents with 'content', 'id', and 'metadata' keys
            batch_size: Number of documents to process at once

        Returns:
            Number of documents added
        """
        try:
            total_added = 0

            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]

                ids = [doc["id"] for doc in batch]
                contents = [doc["content"] for doc in batch]
                metadatas = [doc.get("metadata", {}) for doc in batch]

                self.collection.add(
                    ids=ids,
                    documents=contents,
                    metadatas=metadatas
                )

                total_added += len(batch)
                logger.info(f"Added batch of {len(batch)} documents (total: {total_added})")

            return total_added

        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return 0

    async def ingest_knowledge_base(self, chunk_size: int = 500, chunk_overlap: int = 50) -> int:
        """
        Ingest all knowledge base files into the vector store.

        Args:
            chunk_size: Target size of each text chunk in characters
            chunk_overlap: Overlap between chunks

        Returns:
            Total number of chunks indexed
        """
        total_chunks = 0

        for category, filename in self.category_files.items():
            filepath = self.knowledge_base_path / filename

            if not filepath.exists():
                logger.warning(f"Knowledge file not found: {filepath}")
                continue

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                chunks = self._extract_chunks(data, category, chunk_size, chunk_overlap)

                if chunks:
                    added = await self.add_documents(chunks)
                    total_chunks += added
                    logger.info(f"Ingested {added} chunks from {filename}")

            except Exception as e:
                logger.error(f"Error ingesting {filename}: {e}")

        logger.info(f"Total chunks ingested: {total_chunks}")
        return total_chunks

    def _extract_chunks(
        self,
        data: dict,
        category: str,
        chunk_size: int,
        chunk_overlap: int,
        parent_key: str = ""
    ) -> list[dict]:
        """
        Extract text chunks from JSON data recursively.

        Args:
            data: JSON data structure
            category: Category name for metadata
            chunk_size: Target chunk size
            chunk_overlap: Overlap between chunks
            parent_key: Parent key path for context

        Returns:
            List of document chunks
        """
        chunks = []
        chunk_id = 0

        def flatten_json(obj: Any, prefix: str = "") -> list[tuple[str, str]]:
            """Flatten JSON to key-value pairs."""
            items = []

            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_prefix = f"{prefix}.{key}" if prefix else key
                    if key == "metadata":
                        continue
                    items.extend(flatten_json(value, new_prefix))
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    new_prefix = f"{prefix}[{i}]"
                    items.extend(flatten_json(item, new_prefix))
            else:
                if obj and str(obj).strip():
                    items.append((prefix, str(obj)))

            return items

        # Flatten the JSON structure
        flat_items = flatten_json(data)

        # Group related items into chunks
        current_chunk = []
        current_size = 0

        for key_path, value in flat_items:
            # Format as readable text
            formatted = f"{key_path.replace('.', ' > ').replace('_', ' ').title()}: {value}"
            item_size = len(formatted)

            if current_size + item_size > chunk_size and current_chunk:
                # Save current chunk
                chunk_text = "\n".join(current_chunk)
                chunks.append({
                    "id": f"{category}_{chunk_id}",
                    "content": chunk_text,
                    "metadata": {
                        "category": category,
                        "source": f"knowledge_base/{category}",
                        "chunk_index": chunk_id,
                        "wealth_tier": self._determine_wealth_tier(chunk_text, category)
                    }
                })
                chunk_id += 1

                # Start new chunk with overlap
                overlap_items = current_chunk[-2:] if len(current_chunk) > 2 else current_chunk
                current_chunk = overlap_items + [formatted]
                current_size = sum(len(item) for item in current_chunk)
            else:
                current_chunk.append(formatted)
                current_size += item_size

        # Don't forget the last chunk
        if current_chunk:
            chunk_text = "\n".join(current_chunk)
            chunks.append({
                "id": f"{category}_{chunk_id}",
                "content": chunk_text,
                "metadata": {
                    "category": category,
                    "source": f"knowledge_base/{category}",
                    "chunk_index": chunk_id,
                    "wealth_tier": self._determine_wealth_tier(chunk_text, category)
                }
            })

        return chunks

    def _determine_wealth_tier(self, content: str, category: str) -> str:
        """
        Determine the wealth tier relevance of content using democratized tiers.

        Democratized Service Tiers (aligned with $66,622 US average salary):
        - Foundation ($0-10K): Full CFP access, financial literacy
        - Builder ($10K-75K): Tax optimization, retirement accounts
        - Growth ($75K-500K): Portfolio construction, CFA access
        - Affluent ($500K-5M): Full team, trust structures
        - HNW/UHNW ($5M+): Family office, specialists

        Args:
            content: The text content
            category: The category of the content

        Returns:
            Wealth tier string or 'all'
        """
        content_lower = content.lower()

        # Financial literacy is for Foundation tier - FULL CFP access from day one
        if category == "financial_literacy":
            return WealthTier.FOUNDATION.value

        # HNW/UHNW indicators ($5M+)
        hnw_uhnw_keywords = [
            "family office", "uhnw", "ultra-high", "dynasty", "multi-generational",
            "$50m", "$100m", "private foundation", "family council", "hnw",
            "trust protector", "complex estate", "private equity", "$5m", "$10m"
        ]
        if any(kw in content_lower for kw in hnw_uhnw_keywords):
            return WealthTier.HNW_UHNW.value

        # Affluent indicators ($500K-5M)
        affluent_keywords = [
            "trust structure", "multi-entity", "business succession", "family governance",
            "investment policy", "comprehensive planning", "$500k", "$1m", "$2m"
        ]
        if any(kw in content_lower for kw in affluent_keywords):
            return WealthTier.AFFLUENT.value

        # Growth indicators ($75K-500K) - earlier CFA access
        growth_keywords = [
            "portfolio construction", "cfa", "estate basics", "tax-loss harvesting",
            "real estate", "investment portfolio", "$100k", "$250k", "$75k"
        ]
        if any(kw in content_lower for kw in growth_keywords):
            return WealthTier.GROWTH.value

        # Builder indicators ($10K-75K) - achievable for most Americans
        builder_keywords = [
            "401k", "ira", "roth", "tax optimization", "retirement account",
            "insurance fundamentals", "first investment", "$10k", "$25k", "$50k"
        ]
        if any(kw in content_lower for kw in builder_keywords):
            return WealthTier.BUILDER.value

        # Foundation tier keywords ($0-10K) - financial literacy foundation
        foundation_keywords = [
            "budget", "emergency fund", "debt payoff", "credit building",
            "savings automation", "financial literacy", "beginner"
        ]
        if any(kw in content_lower for kw in foundation_keywords):
            return WealthTier.FOUNDATION.value

        return "all"

    def get_collection_stats(self) -> dict:
        """Get statistics about the indexed collection."""
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": self.collection_name,
                "embedding_model": self.embedding_model,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}

    async def search_by_category(
        self,
        question: str,
        categories: list[str],
        n_results: int = 5
    ) -> list[dict]:
        """
        Search within specific categories.

        Args:
            question: The search query
            categories: List of category names to search within
            n_results: Number of results to return

        Returns:
            List of relevant documents
        """
        try:
            results = self.collection.query(
                query_texts=[question],
                n_results=n_results,
                where={"category": {"$in": categories}},
                include=["documents", "metadatas", "distances"]
            )

            formatted_results = []
            if results and results.get("documents") and results["documents"][0]:
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                ):
                    formatted_results.append({
                        "content": doc,
                        "metadata": meta,
                        "relevance_score": 1 - dist,
                        "source": meta.get("source", "unknown"),
                        "category": meta.get("category", "general")
                    })

            return formatted_results

        except Exception as e:
            logger.error(f"Error in category search: {e}")
            return []

    async def get_professional_recommendations(
        self,
        situation: str,
        wealth_tier: WealthTier
    ) -> list[dict]:
        """
        Get professional advisor recommendations based on situation.

        Args:
            situation: Description of the client's situation/needs
            wealth_tier: The client's wealth tier

        Returns:
            List of recommended professionals with relevance scores
        """
        # Query professional roles and certifications
        results = await self.search_by_category(
            situation,
            ["professional_roles", "certifications", "financial_advisors"],
            n_results=10
        )

        return results

    async def get_succession_planning_guidance(self, business_details: str) -> list[dict]:
        """
        Get business succession planning guidance.

        Args:
            business_details: Description of the business and situation

        Returns:
            Relevant succession planning knowledge
        """
        return await self.search_by_category(
            business_details,
            ["succession_planning", "professional_roles", "estate_planning"],
            n_results=8
        )

    async def get_financial_literacy_content(
        self,
        topic: str,
        level: str = "beginner"
    ) -> list[dict]:
        """
        Get financial literacy educational content.

        Args:
            topic: The financial topic to learn about
            level: Learning level (beginner, intermediate, advanced)

        Returns:
            Educational content chunks
        """
        query = f"{level} {topic} financial education basics"
        return await self.search_by_category(
            query,
            ["financial_literacy"],
            n_results=5
        )


# Singleton instance for application-wide use
_rag_instance: Optional[WealthManagementRAG] = None


def get_wealth_rag() -> WealthManagementRAG:
    """Get or create the singleton RAG instance."""
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = WealthManagementRAG()
    return _rag_instance
