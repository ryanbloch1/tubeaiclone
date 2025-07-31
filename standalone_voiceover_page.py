import tkinter as tk
from pages.voiceover_page import VoiceoverPage

class DummyController:
    def __init__(self, root, frame):
        self.root = root
        self.frames = {"VoiceoverPage": frame}
    def show_frame(self, name):
        frame = self.frames.get(name)
        if frame:
            frame.tkraise()

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Standalone VoiceoverPage Test")
    root.geometry("1100x700")
    
    # Create the VoiceoverPage
    frame = VoiceoverPage(root, None)
    frame.pack(fill="both", expand=True)
    
    # Inject a dummy controller for navigation compatibility
    controller = DummyController(root, frame)
    frame.controller = controller
    
    # Pre-fill with a test script
    test_script = (
        "YouTube Video Script: Ancient Aliens in Egypt?\n"
        "Scene 1 (0:00-0:30): Mysterious Monuments\n"
        "(Open on a shot of the Giza pyramids. Upbeat, slightly mysterious music plays.)\n"
        "Narrator: Hey, YouTube explorers! Ever wonder how the ancient Egyptians built such amazing things? "
        "We're talking HUGE pyramids, super-strong statues, and temples filled with incredible carvings. "
        "It's amazing, right? Some people think the Egyptians couldn't have done it all by themselves. "
        "They think maybe…aliens helped!\n"
        "(Show quick cuts of various Egyptian artifacts: Sphinx, hieroglyphs, a sarcophagus.)\n"
        "Narrator: Now, we don't know for sure if aliens were involved. But there are some things about ancient Egypt that are still a bit of a mystery. "
        "For example, how did they move those giant stones? They were heavier than school buses! "
        "And those precise carvings…how did they do that without super-advanced tools?\n"
        "(Show a graphic of a pyramid with arrows pointing to its precise angles and massive stones.)\n"
        "Narrator: These are questions that scientists are still trying to answer. "
        "We'll look at some of the amazing engineering skills the Egyptians did have in the next scene. "
        "It was pretty impressive, even without little green men!\n"
    )
    frame.set_script(test_script)
    
    root.mainloop() 