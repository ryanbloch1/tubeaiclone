"""Timestamps module: calculates timestamps for each image/scene based on audio duration."""

def calculate_timestamps(audio_duration, image_count):
    """
    Calculate start/end timestamps for each image/scene.
    Args:
        audio_duration (float): Total audio duration in seconds.
        image_count (int): Number of images/scenes.
    Returns:
        list of tuple: List of (start, end) timestamps for each scene.
    """
    # TODO: Implement timestamp calculation
    segment = audio_duration / image_count
    return [(i*segment, (i+1)*segment) for i in range(image_count)]
