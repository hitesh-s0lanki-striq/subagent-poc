from pydantic import BaseModel, Field
from typing import Optional, Literal, List


class LaunchingAgentState(BaseModel):
    """
    Flat, stage-driven state for Meta Ads campaign launching.
    This state is embedded inside MetaQueryAgentResponse.context.
    """

    # ────────────────────────────────────────
    # FLOW CONTROL
    # ────────────────────────────────────────

    stage: Literal["CAMPAIGN_INFO", "CREATIVE", "LAUNCHING"] = Field(
        default="CAMPAIGN_INFO",
        description="Current stage of the launch flow."
    )

    state: Literal["ongoing", "completed"] = Field(
        default="ongoing",
        description="Overall state of the launching flow."
    )

    # ────────────────────────────────────────
    # STAGE 1 — CAMPAIGN_INFO
    # ────────────────────────────────────────

    objective: Optional[str] = Field(
        default=None,
        description="Campaign objective (Traffic, Leads, Sales)."
    )

    geo: Optional[str] = Field(
        default=None,
        description="Target country or geographic region."
    )

    daily_budget: Optional[int] = Field(
        default=None,
        description="Daily budget for the campaign."
    )

    start_time: Optional[str] = Field(
        default=None,
        description="Campaign start time (ISO format)."
    )

    end_time: Optional[str] = Field(
        default=None,
        description="Optional campaign end time (ISO format)."
    )

    # ────────────────────────────────────────
    # STAGE 2 — CREATIVE
    # ────────────────────────────────────────

    creative_mode: Optional[Literal["GENERATE", "USER_PROVIDED"]] = Field(
        default=None,
        description="Creative mode selection."
    )
    
    creative_urls: Optional[List[str]] = Field(
        default=None,
        description="List of creative asset URLs (images/videos) selected or uploaded for the ad."
    )

    product_url: Optional[str] = Field(
        default=None,
        description="Landing page or product URL to be promoted."
    )

    # ────────────────────────────────────────
    # STAGE 3 — LAUNCHING
    # ────────────────────────────────────────

    user_confirmation: Optional[Literal["YES", "NO"]] = Field(
        default=None,
        description="Final user confirmation before launching the campaign."
    )

    # ────────────────────────────────────────
    # CONVERSATION DRIVER
    # ────────────────────────────────────────

    follow_up_question: Optional[str] = Field(
        default=None,
        description="Single follow-up question to ask the user next."
    )


# Alias for backward compatibility
LaunchingAgentOutput = LaunchingAgentState
