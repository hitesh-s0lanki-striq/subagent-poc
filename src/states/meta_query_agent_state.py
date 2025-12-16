from pydantic import BaseModel, Field


class MetaQueryAgentResponse(BaseModel):
    """
    Standard response format for the Meta Query Agent.
    This is the ONLY format exposed to the user.
    """

    context: str = Field(
        ...,
        description=(
            "Internal context string describing what stage the flow is in, "
            "which agent/tool was called, and what information is missing or completed. "
            "Format: 'mode=<launch|reporting> | stage=<stage_name> | <description>'. "
            "This helps UI/state managers understand the conversation flow."
        )
    )

    response: str = Field(
        ...,
        description=(
            "Human-readable response shown to the user. "
            "This may include questions, confirmations, or final outputs."
        )
    )


# Alias for backward compatibility
MetaQueryAgentOutput = MetaQueryAgentResponse
