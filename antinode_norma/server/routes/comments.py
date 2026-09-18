"""Comments and collaboration routes for Norma BDD Platform FastAPI server."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from antinode_norma.auth.middleware import log_user_action, requires_permission
from antinode_norma.auth.models import User
from antinode_norma.auth.roles import FEATURE_READ
from antinode_norma.collaboration.comments import Comment, CommentStore

router = APIRouter(prefix="/api/comments", tags=["Comments"])

# Shared in-memory CommentStore instance for server
comment_store = CommentStore()


class CreateCommentRequest(BaseModel):
    feature_id: str
    text: str
    mentions: Optional[List[str]] = None


@router.get(
    "",
    response_model=List[Comment],
    dependencies=[Depends(requires_permission(FEATURE_READ))],
)
async def list_comments(feature_id: Optional[str] = Query(None)) -> List[Comment]:
    """Retrieves comments, optionally filtered by feature_id."""
    return comment_store.get_comments(feature_id=feature_id)


@router.post(
    "",
    response_model=Comment,
)
async def create_comment(
    request: Request,
    payload: CreateCommentRequest,
    user: User = Depends(requires_permission(FEATURE_READ)),
) -> Comment:
    """Creates a new comment on a feature with automatic mention extraction."""
    comment = comment_store.add_comment(
        feature_id=payload.feature_id,
        author_id=user.id,
        text=payload.text,
        mentions=payload.mentions,
    )

    log_user_action(
        request=request,
        user=user,
        action="comments:create",
        resource=f"feature:{payload.feature_id}",
        result="success",
        payload={
            "comment_id": comment.id,
            "feature_id": comment.feature_id,
            "mentions": comment.mentions,
        },
    )

    return comment
