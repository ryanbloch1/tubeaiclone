import tkinter as tk
from tkinter import ttk, font
import json
import os
import threading
from tkinter import messagebox

class StyleCreationPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f5f6fa")
        self.controller = controller
        self.title_font = font.Font(family="Helvetica", size=22, weight="bold")
        self.text_font = font.Font(family="Helvetica", size=12)

        # Make the frame responsive
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        tk.Label(self, text="Create New Style", font=self.title_font, bg="#f5f6fa", fg="#2d3436").grid(row=0, column=0, pady=(20,10), sticky="n")

        form = tk.Frame(self, bg="#fff", padx=30, pady=20)
        form.grid(row=1, column=0, pady=10, sticky="nsew")
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        form.grid_columnconfigure(1, weight=1)

        tk.Label(form, text="Style Name*", font=self.text_font, bg="#fff").grid(row=0, column=0, sticky="w", pady=5)
        self.style_name = tk.Entry(form, width=40, font=self.text_font)
        self.style_name.grid(row=0, column=1, pady=5, sticky="ew")

        tk.Label(form, text="Voice*", font=self.text_font, bg="#fff").grid(row=1, column=0, sticky="w", pady=5)
        self.voice_var = tk.StringVar()
        voices = [
            "Matt", "Frederick", "Nash", "Declan", "Ian", "Drew", "Archer", "Hope", "Julian", "Josh", "Owen", "Lovejoy"
        ]
        self.voice_var.set(voices[0])
        ttk.Combobox(form, textvariable=self.voice_var, values=voices, font=self.text_font, state="readonly").grid(row=1, column=1, pady=5, sticky="ew")

        tk.Label(form, text="Reference YouTube URLs*", font=self.text_font, bg="#fff").grid(row=2, column=0, sticky="nw", pady=5)
        self.url_entries = []
        url_frame = tk.Frame(form, bg="#fff")
        url_frame.grid(row=2, column=1, pady=5, sticky="ew")
        for i in range(4):
            entry = tk.Entry(url_frame, width=40, font=self.text_font)
            entry.grid(row=i, column=0, pady=2, sticky="ew")
            url_frame.grid_columnconfigure(0, weight=1)
            self.url_entries.append(entry)
        self.add_url_btn = tk.Button(url_frame, text="+ Add URL", font=self.text_font, command=self.add_url_entry)
        self.add_url_btn.grid(row=4, column=0, pady=5, sticky="w")

        self.save_btn = tk.Button(self, text="Save Style", font=self.text_font, bg="#00b894", fg="#fff", command=self.save_style)
        self.save_btn.grid(row=2, column=0, columnspan=2, pady=20, sticky="ew")

        self.status = tk.Label(self, text="", font=self.text_font, bg="#f5f6fa", fg="#0984e3")
        self.status.grid(row=3, column=0, columnspan=2, sticky="ew")

    def add_url_entry(self):
        idx = len(self.url_entries)
        entry = tk.Entry(self.save_btn.master.children['!frame'].children['!frame'], width=40, font=self.text_font)
        entry.grid(row=idx, column=0, pady=2, sticky="ew")
        entry.master.grid_columnconfigure(0, weight=1)
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