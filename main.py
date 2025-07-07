import tkinter as tk
from tkinter import ttk, font
import json
import os
from pages.title_entry import TitleEntryPage
from pages.style_creation import StyleCreationPage
from pages.script_display import ScriptDisplayPage
from pages.voiceover_page import VoiceoverPage
from pages.image_generation_page import ImageGenerationPage
from utils.script_generation import generate_script
from tkinter import messagebox

class StyleCreatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TubeGenAI - Create Style")
        self.root.configure(bg="#f5f6fa")

        # Fonts
        self.title_font = font.Font(family="Helvetica", size=22, weight="bold")
        self.text_font = font.Font(family="Helvetica", size=12)

        # Title
        tk.Label(root, text="Create New Style", font=self.title_font, bg="#f5f6fa", fg="#2d3436").pack(pady=(20,10))

        form = tk.Frame(root, bg="#fff", padx=30, pady=20)
        form.pack(pady=10)

        # Style Name
        tk.Label(form, text="Style Name*", font=self.text_font, bg="#fff").grid(row=0, column=0, sticky="w", pady=5)
        self.style_name = tk.Entry(form, width=40, font=self.text_font)
        self.style_name.grid(row=0, column=1, pady=5)

        # Voice Dropdown
        tk.Label(form, text="Voice*", font=self.text_font, bg="#fff").grid(row=1, column=0, sticky="w", pady=5)
        self.voice_var = tk.StringVar()
        voices = [
            "Matt", "Frederick", "Nash", "Declan", "Ian", "Drew", "Archer", "Hope", "Julian", "Josh", "Owen", "Lovejoy"
        ]
        self.voice_var.set(voices[0])
        ttk.Combobox(form, textvariable=self.voice_var, values=voices, font=self.text_font, state="readonly").grid(row=1, column=1, pady=5)

        # YouTube URLs
        tk.Label(form, text="Reference YouTube URLs*", font=self.text_font, bg="#fff").grid(row=2, column=0, sticky="nw", pady=5)
        self.url_entries = []
        url_frame = tk.Frame(form, bg="#fff")
        url_frame.grid(row=2, column=1, pady=5, sticky="w")
        for i in range(4):
            entry = tk.Entry(url_frame, width=40, font=self.text_font)
            entry.grid(row=i, column=0, pady=2)
            self.url_entries.append(entry)
        # Add more URLs button
        self.add_url_btn = tk.Button(url_frame, text="+ Add URL", font=self.text_font, command=self.add_url_entry)
        self.add_url_btn.grid(row=4, column=0, pady=5, sticky="w")

        # Save Button
        self.save_btn = tk.Button(root, text="Save Style", font=self.text_font, bg="#00b894", fg="#fff", command=self.save_style)
        self.save_btn.pack(pady=20)

        # Status
        self.status = tk.Label(root, text="", font=self.text_font, bg="#f5f6fa", fg="#0984e3")
        self.status.pack()

    def add_url_entry(self):
        idx = len(self.url_entries)
        entry = tk.Entry(self.save_btn.master.children['!frame'].children['!frame'], width=40, font=self.text_font)
        entry.grid(row=idx, column=0, pady=2)
        self.url_entries.append(entry)
        self.add_url_btn.grid(row=idx+1, column=0, pady=5, sticky="w")

    def save_style(self):
        name = self.style_name.get().strip()
        voice = self.voice_var.get()
        urls = [e.get().strip() for e in self.url_entries if e.get().strip()]
        if not name or not voice or len(urls) == 0:
            self.status.config(text="Please fill all required fields.", fg="#d35400")
            return
        style = {"name": name, "voice": voice, "urls": urls}
        # Save to styles.json
        styles_file = "styles.json"
        if os.path.exists(styles_file):
            with open(styles_file, "r") as f:
                try:
                    styles = json.load(f)
                except Exception:
                    styles = []
        else:
            styles = []
        styles.append(style)
        with open(styles_file, "w") as f:
            json.dump(styles, f, indent=2)
        self.status.config(text="Style saved!", fg="#00b894")
        self.style_name.delete(0, tk.END)
        for e in self.url_entries:
            e.delete(0, tk.END)

class TubeGenAIApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TubeGenAI")
        self.geometry("1200x700")
        self.configure(bg="#18181b")

        # Make the root window responsive
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        container = tk.Frame(self, bg="#18181b")
        container.grid(row=0, column=0, sticky="nsew")  # Use grid, not pack

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (TitleEntryPage, StyleCreationPage, ScriptDisplayPage, VoiceoverPage, ImageGenerationPage):
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("TitleEntryPage")

    def show_frame(self, name):
        frame = self.frames[name]
        frame.tkraise()

if __name__ == "__main__":
    app = TubeGenAIApp()
    app.mainloop()