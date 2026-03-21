"""
Retriever Module

Performs semantic retrieval over indexed Slack messages.
Transforms user queries into contextual information for the LLM.
"""

import time
import re
from typing import List, Dict, Optional
from dataclasses import dataclass

from src.utils.logger import get_logger
from src.rag.embeddings import create_embedding, preprocess_text
from src.rag.vectorstore import search

logger = get_logger("retriever")


# ---------------------------------------------------------
# Data Models
# ---------------------------------------------------------

@dataclass
class RetrievalOptions:
    limit: int = 10
    min_score: float = 0.3
    channel_name: Optional[str] = None
    channel_id: Optional[str] = None
    user_id: Optional[str] = None
    include_context: bool = False
    context_window: int = 2


@dataclass
class RetrievedDocument:
    text: str
    score: float
    channel_name: str
    user_name: str
    timestamp: str
    message_id: str
    is_thread: bool
    formatted: str
    context_before: Optional[List[str]] = None
    context_after: Optional[List[str]] = None


@dataclass
class RetrievalResponse:
    query: str
    results: List[RetrievedDocument]
    total_found: int
    search_time_ms: int


# ---------------------------------------------------------
# Main Retrieval Function
# ---------------------------------------------------------

async def retrieve(query: str, options: RetrievalOptions = RetrievalOptions()) -> RetrievalResponse:

    start = time.time()

    logger.info(f"Retrieving context for query: {query[:50]}")

    processed_query = preprocess_text(query) or query

    query_embedding = await create_embedding(processed_query)

    search_results = await search(
        query_embedding,
        limit=options.limit * 2,
        channel_name=options.channel_name,
        channel_id=options.channel_id,
        user_id=options.user_id,
    )

    filtered = [r for r in search_results if r.score >= options.min_score]

    retrieved_docs: List[RetrievedDocument] = []

    for result in filtered[: options.limit]:

        doc = RetrievedDocument(
            text=result.text,
            score=result.score,
            channel_name=result.metadata.channelName,
            user_name=result.metadata.userName,
            timestamp=result.metadata.timestamp,
            message_id=result.metadata.messageTs,
            is_thread=result.metadata.isThread or False,
            formatted=format_for_llm(result),
        )

        retrieved_docs.append(doc)

    duration = int((time.time() - start) * 1000)

    logger.info(f"Retrieved {len(retrieved_docs)} docs in {duration}ms")

    return RetrievalResponse(
        query=query,
        results=retrieved_docs,
        total_found=len(filtered),
        search_time_ms=duration,
    )


# ---------------------------------------------------------
# Format Result For LLM
# ---------------------------------------------------------

def format_for_llm(result) -> str:

    ts = result.metadata.timestamp

    date = ts[:10]

    thread_indicator = " (thread reply)" if result.metadata.isThread else ""

    return (
        f"[{date} in #{result.metadata.channelName}{thread_indicator}] "
        f"{result.metadata.userName}: {result.text}"
    )


# ---------------------------------------------------------
# Build Context Block For LLM
# ---------------------------------------------------------

def build_context_string(docs: List[RetrievedDocument]) -> str:

    if not docs:
        return ""

    header = (
        "## Relevant Slack History\n\n"
        "The following Slack messages may help answer the question:\n\n"
    )

    messages = "\n".join(
        f"{i+1}. {doc.formatted}" for i, doc in enumerate(docs)
    )

    footer = "\n\n---\nUse these messages to inform your response."

    return header + messages + footer


# ---------------------------------------------------------
# Convenience Retrieval
# ---------------------------------------------------------

async def retrieve_context(query: str, options: RetrievalOptions = RetrievalOptions()) -> str:

    results = await retrieve(query, options)

    return build_context_string(results.results)


# ---------------------------------------------------------
# RAG Heuristic
# ---------------------------------------------------------

def should_use_rag(query: str) -> bool:

    q = query.lower()

    rag_indicators = [
        "what did",
        "who said",
        "when did",
        "decision about",
        "discussed",
        "mentioned",
        "talked about",
        "conversation about",
        "history of",
        "remember when",
        "last time",
        "previously",
        "what was",
        "find messages",
        "search for",
        "look up",
    ]

    no_rag_indicators = [
        "send message",
        "schedule",
        "remind me",
        "hello",
        "hi",
        "hey",
        "thanks",
        "help",
        "what can you do",
        "list channels",
        "list users",
    ]

    for indicator in no_rag_indicators:
        if indicator in q:
            return False

    for indicator in rag_indicators:
        if indicator in q:
            return True

    return (
        "?" in q
        or q.startswith("what ")
        or q.startswith("who ")
        or q.startswith("when ")
        or q.startswith("where ")
        or q.startswith("why ")
        or q.startswith("how ")
    )


# ---------------------------------------------------------
# Query Filter Parser
# ---------------------------------------------------------

def parse_query_filters(query: str):

    filters: Dict = {}

    channel_match = re.search(r"#(\w+[-\w]*)", query)
    if channel_match:
        filters["channel_name"] = channel_match.group(1)

    slack_user = re.search(r"<@([A-Z0-9]+)>", query)
    if slack_user:
        filters["user_id"] = slack_user.group(1)

    if "today" in query:
        filters["time_filter"] = "today"
    elif "week" in query:
        filters["time_filter"] = "week"
    elif "month" in query:
        filters["time_filter"] = "month"

    return filters
