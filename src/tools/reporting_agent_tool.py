from langchain.tools import tool

@tool("reporting_agent_tool")
def reporting_agent_tool(
    campaign_id: str,
) -> str:
    """
    Dummy tool to simulate Meta Ads reporting from a campaign ID.
    Returns demo reporting data.
    """
    
    demo_reporting_data = {
        "spend": 100,
        "impressions": 1000,
        "clicks": 100,
        "ctr": 10,
        "conversions": 10,
        "roas": 10
    }

    return (
        "[DEMO] Reporting successful. "
        f"Campaign ID: {campaign_id}. "
        f"Reporting data: {demo_reporting_data}"            # TODO: Implement actual reporting data
    )
