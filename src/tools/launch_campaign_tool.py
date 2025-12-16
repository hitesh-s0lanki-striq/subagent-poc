from langchain.tools import tool
from typing import List

@tool("launch_campaign_tool")
def launch_campaign_tool(
    objective: str,
    geo: str,
    daily_budget: int,
    creative_urls: List[str]
) -> str:
    """
    Dummy tool to simulate Meta campaign launch.
    """
    return (
        "[DEMO] Campaign launch initiated. "
        f"Objective={objective}, Geo={geo}, "
        f"Daily Budget={daily_budget}, "
        f"Creatives={creative_urls}"
    )
