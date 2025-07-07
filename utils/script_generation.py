"""Script generation module: generates a YouTube script using Google Gemini (free) or fallback to mock."""

import google.generativeai as genai
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

def generate_script(topic, style_profile=None, context_mode=None, transcript=None, web_data=None, image_count=10):
    """
    Generate a YouTube script using Google Gemini (free) or fallback to mock.
    Args:
        topic (str): The video topic/title.
        style_profile (dict): Style info (tone, pacing, etc.).
        context_mode (str): 'default', 'video', or 'web'.
        transcript (str): Video transcript for context.
        web_data (str): Web search data for context.
        image_count (int): Number of scenes/images.
    Returns:
        str: Generated script.
    """
    
    # Try to use Google Gemini first
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    if gemini_api_key and gemini_api_key != "your_api_key_here":
        try:
            print(f"Using Gemini API with key: {gemini_api_key[:10]}...")
            genai.configure(api_key=gemini_api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Build the prompt
            prompt = f"""Write a YouTube video script for the title: '{topic}'.
            
            Requirements:
            - Break into {image_count} scenes
            - Use 4th grade reading level
            - Be curiosity-driven and YouTube-safe
            - Each scene should be engaging and informative
            - Write about the actual topic, not just repeat the title
            
            Format each scene like this:
            Scene 1 (0:00-0:30): [content]
            Scene 2 (0:30-1:00): [content]
            etc.
            
            Make it engaging and educational!"""
            
            if style_profile:
                prompt += f"\n\nUse the style: {style_profile.get('name', 'default')}."
            
            if context_mode == 'video' and transcript:
                prompt += f"\n\nUse this transcript for structure inspiration: {transcript[:500]}..."
            
            if context_mode == 'web' and web_data:
                prompt += f"\n\nUse these facts: {web_data[:500]}..."
            
            print("Sending request to Gemini...")
            response = model.generate_content(prompt)
            print("Received response from Gemini!")
            return response.text
            
        except Exception as e:
            error_msg = str(e)
            print(f"Gemini API error: {error_msg}")
            
            if "429" in error_msg and "quota" in error_msg.lower():
                return f"""QUOTA EXCEEDED - Using Fallback Script

Your Gemini API free tier quota has been exceeded. Here's a generated script for: {topic}

Scene 1 (0:00-0:30):
Welcome to our deep dive into {topic}! Today we're going to explore every fascinating aspect of this incredible subject. Whether you're a beginner or an expert, there's something here for everyone.

Scene 2 (0:30-1:00):
Let's start with the fundamentals. {topic} has roots that go back much further than most people realize. Understanding its origins helps us appreciate why it's so important in our world today.

Scene 3 (1:00-1:30):
One of the most surprising things about {topic} is how it has evolved over time. From its early beginnings to the modern era, the transformation has been nothing short of remarkable.

Scene 4 (1:30-2:00):
But here's where it gets really interesting. {topic} isn't just about facts and figures - it's about the human connection. It touches lives in ways that are both profound and personal.

Scene 5 (2:00-2:30):
As we explore the future of {topic}, we can see exciting developments on the horizon. The possibilities are endless, and the potential for innovation is enormous.

Scene 6 (2:30-3:00):
Let's talk about the practical applications. How does {topic} affect our daily lives? The answer might surprise you, and it's more relevant than you might think.

Scene 7 (3:00-3:30):
But it's not all smooth sailing. {topic} faces challenges that we need to address. Understanding these obstacles is the first step toward finding solutions.

Scene 8 (3:30-4:00):
The experts have some fascinating insights about {topic}. Their research reveals patterns and trends that could shape the future in unexpected ways.

Scene 9 (4:00-4:30):
What does this mean for you and me? The impact of {topic} on our personal and professional lives is more significant than we often realize.

Scene 10 (4:30-5:00):
As we wrap up our exploration of {topic}, remember that this is just the beginning. The journey of discovery never truly ends, and there's always more to learn.

[Note: Your Gemini API free tier quota has been exceeded. Wait 24 hours for quota reset, or upgrade to a paid plan at https://ai.google.dev/pricing]"""
            else:
                return f"Error generating script with Gemini: {error_msg}\n\nPlease check your API key and try again."
    
    # Only show mock if no API key
    if not gemini_api_key or gemini_api_key == "your_api_key_here":
        return f"""GENERATED SCRIPT FOR: {topic}

Scene 1 (0:00-0:30):
Welcome to our deep dive into {topic}! Today we're going to explore every fascinating aspect of this incredible subject. Whether you're a beginner or an expert, there's something here for everyone.

Scene 2 (0:30-1:00):
Let's start with the fundamentals. {topic} has roots that go back much further than most people realize. Understanding its origins helps us appreciate why it's so important in our world today.

Scene 3 (1:00-1:30):
One of the most surprising things about {topic} is how it has evolved over time. From its early beginnings to the modern era, the transformation has been nothing short of remarkable.

Scene 4 (1:30-2:00):
But here's where it gets really interesting. {topic} isn't just about facts and figures - it's about the human connection. It touches lives in ways that are both profound and personal.

Scene 5 (2:00-2:30):
As we explore the future of {topic}, we can see exciting developments on the horizon. The possibilities are endless, and the potential for innovation is enormous.

Scene 6 (2:30-3:00):
Let's talk about the practical applications. How does {topic} affect our daily lives? The answer might surprise you, and it's more relevant than you might think.

Scene 7 (3:00-3:30):
But it's not all smooth sailing. {topic} faces challenges that we need to address. Understanding these obstacles is the first step toward finding solutions.

Scene 8 (3:30-4:00):
The experts have some fascinating insights about {topic}. Their research reveals patterns and trends that could shape the future in unexpected ways.

Scene 9 (4:00-4:30):
What does this mean for you and me? The impact of {topic} on our personal and professional lives is more significant than we often realize.

Scene 10 (4:30-5:00):
As we wrap up our exploration of {topic}, remember that this is just the beginning. The journey of discovery never truly ends, and there's always more to learn.

[Note: To get real AI-generated scripts, add your Gemini API key to the .env file:
GEMINI_API_KEY=your_api_key_here
Get a free API key from: https://makersuite.google.com/app/apikey]"""
    
    return "No API key found. Please add your Gemini API key to the .env file."
