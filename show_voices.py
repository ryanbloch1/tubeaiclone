#!/usr/bin/env python3
"""
Script to show all available ElevenLabs voices
"""

from utils.voiceover import get_available_voices

def show_voices():
    """Display all available voices"""
    print("Fetching available voices...")
    print("=" * 50)
    
    voices = get_available_voices()
    
    print(f"\nElevenLabs Voices ({len(voices['elevenlabs'])} total):")
    print("-" * 30)
    for i, (name, voice_id) in enumerate(voices['elevenlabs'].items(), 1):
        print(f"{i:2d}. {name:<20} (ID: {voice_id})")
    
    print(f"\nLocal TTS Voices ({len(voices['local'])} total):")
    print("-" * 30)
    for i, name in enumerate(voices['local'], 1):
        print(f"{i:2d}. {name}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    show_voices() 