from langchain.tools import tool

@tool("image_generation_tool")
def image_generation_tool(
    product_url: str,
    num_images: int = 3
) -> str:
    """
    Dummy tool to simulate creative image generation from a product URL.
    Returns demo image URLs.
    """
    demo_urls = [
        f"https://cdn.demo.com/generated_creative_{i+1}.png"
        for i in range(num_images)
    ]

    return (
        "[DEMO] Image generation successful. "
        f"Product URL: {product_url}. "
        f"Generated creatives: {demo_urls}"
    )
