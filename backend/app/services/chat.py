"""Sending a message: daily cap, history, model call and persistence."""

import logging
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime

from flask import current_app
from openai import APITimeoutError, OpenAIError, RateLimitError

from ..db import repositories
from . import history, llm

logger = logging.getLogger(__name__)


class DailyLimitReached(Exception):
    """The global daily message cap was reached."""


class AssistantBusy(Exception):
    """The model provider is rate limiting or timing out."""


class AssistantUnavailable(Exception):
    """The model provider failed for another reason (details stay in the log)."""


@dataclass
class ChatResult:
    conversation_id: str
    answer: str
    truncated: bool


def send_message(user_id, conversation_id, text):
    daily_limit = current_app.config["DAILY_MESSAGE_LIMIT"]
    if daily_limit > 0:
        day_start = datetime.now(UTC).strftime("%Y-%m-%d 00:00:00")
        if repositories.count_messages_since(day_start) >= daily_limit:
            logger.warning("Daily message limit reached (%s)", daily_limit)
            raise DailyLimitReached

    try:
        answer, truncated = llm.generate_answer(
            text,
            history.load_history(user_id, conversation_id),
            history.producer_context(repositories.get_user(user_id)),
        )
    except (RateLimitError, APITimeoutError) as error:
        logger.exception("LLM busy or timed out (user_id=%s)", user_id)
        raise AssistantBusy from error
    except OpenAIError as error:
        logger.exception("LLM request failed (user_id=%s)", user_id)
        raise AssistantUnavailable from error

    if truncated:
        # Cut by LLM_MAX_TOKENS; raise the limit if this is frequent
        logger.warning("LLM answer truncated by max_tokens (user_id=%s)", user_id)

    try:
        repositories.add_message(user_id, conversation_id, text, answer)
    except sqlite3.Error:
        logger.exception("Failed to save the message (user_id=%s)", user_id)

    return ChatResult(conversation_id=conversation_id, answer=answer, truncated=truncated)
