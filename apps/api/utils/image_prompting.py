"""Image prompting module: generates image prompts for each scene in the script."""

def generate_image_prompts(script, image_count=10):
    """
    Generate image prompts for each scene in the script.
    Args:
        script (str): The full script.
        image_count (int): Number of images/scenes.
    Returns:
        list of str: List of image prompts.
    """
    # TODO: Implement scene splitting and prompt generation
    return [f"Prompt for scene {i+1}" for i in range(image_count)]
