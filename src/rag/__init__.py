"""
RAG Module Index

Central export module for the Retrieval Augmented Generation system.

Usage Example
-------------

Initialize system:

    from src.rag import initialize_vector_store, start_indexer

    await initialize_vector_store()
    start_indexer()

Search context:

    from src.rag import retrieve, build_context_string, should_use_rag

    if should_use_rag(query):
        results = await retrieve(query)
        context = build_context_string(results.results)

Manual indexing:

    from src.rag import index_single_message

    await index_single_message(message, channel_id, channel_name)
"""

# =========================================================
# Embeddings
# =========================================================

from .embeddings import (
    create_embedding,
    create_embeddings,
    cosine_similarity,
    preprocess_text,
    get_embedding_config,
    initialize_embedding_provider,
    is_embedding_provider_ready,
)

# =========================================================
# Vector Store
# =========================================================

from .vectorstore import (
    initialize_vector_store,
    add_documents,
    update_documents,
    delete_documents,
    search,
    get_document_count,
    document_exists,
    get_documents,
    clear_all,
    Document,
    DocumentMetadata,
    SearchResult,
)

# =========================================================
# Indexer
# =========================================================

from .indexer import (
    start_indexer,
    stop_indexer,
    run_index,
    index_channel_manually,
    index_single_message,
    get_indexer_status,
)

# =========================================================
# Retriever
# =========================================================

from .retriever import (
    retrieve,
    retrieve_context,
    build_context_string,
    should_use_rag,
    parse_query_filters,
    RetrievalOptions,
    RetrievedDocument,
    RetrievalResponse,
)

# =========================================================
# Public API
# =========================================================

__all__ = [

    # embeddings
    "create_embedding",
    "create_embeddings",
    "cosine_similarity",
    "preprocess_text",
    "get_embedding_config",
    "initialize_embedding_provider",
    "is_embedding_provider_ready",

    # vector store
    "initialize_vector_store",
    "add_documents",
    "update_documents",
    "delete_documents",
    "search",
    "get_document_count",
    "document_exists",
    "get_documents",
    "clear_all",
    "Document",
    "DocumentMetadata",
    "SearchResult",

    # indexer
    "start_indexer",
    "stop_indexer",
    "run_index",
    "index_channel_manually",
    "index_single_message",
    "get_indexer_status",

    # retriever
    "retrieve",
    "retrieve_context",
    "build_context_string",
    "should_use_rag",
    "parse_query_filters",
    "RetrievalOptions",
    "RetrievedDocument",
    "RetrievalResponse",
]