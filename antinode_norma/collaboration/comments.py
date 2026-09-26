"""Comments and mentions models and in-memory store for collaboration."""

import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class Comment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    feature_id: str
    author_id: str
    text: str
    mentions: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def extract_mentions(text: str) -> List[str]:
    """Extracts @username mentions from comment text."""
    pattern = r"@([a-zA-Z0-9_\-\.]+)"
    matches = re.findall(pattern, text)
    return list(set(matches))


class CommentStore:
    def __init__(self, database_url: Optional[str] = None) -> None:
        self.database_url = database_url
        self._comments: List[Comment] = []
        if database_url:
            from antinode_norma.database import load_comments

            self._comments = [Comment(**item) for item in load_comments(database_url)]

    def add_comment(
        self,
        feature_id: str,
        author_id: str,
        text: str,
        mentions: Optional[List[str]] = None,
    ) -> Comment:
        """Creates and stores a comment, auto-extracting mentions if not explicitly supplied."""
        extracted = mentions if mentions is not None else extract_mentions(text)
        comment = Comment(
            feature_id=feature_id,
            author_id=author_id,
            text=text,
            mentions=extracted,
        )
        self._comments.append(comment)
        if self.database_url:
            from antinode_norma.database import save_comment

            save_comment(self.database_url, comment.model_dump())
        return comment

    def get_comments(self, feature_id: Optional[str] = None) -> List[Comment]:
        """Lists comments, optionally filtered by feature_id."""
        if feature_id:
            return [c for c in self._comments if c.feature_id == feature_id]
        return list(self._comments)
