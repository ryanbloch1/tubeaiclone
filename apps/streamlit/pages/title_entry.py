import tkinter as tk
from tkinter import font
from utils.script_generation import generate_script
from tkinter import messagebox

class TitleEntryPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f5f6fa")  # light background
        self.controller = controller
        self.title_font = font.Font(family="Helvetica", size=28, weight="bold")
        self.input_font = font.Font(family="Helvetica", size=14)
        self.credits_font = font.Font(family="Helvetica", size=10)

        # Make the frame responsive
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        container = tk.Frame(self, bg="#f5f6fa")
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)

        tk.Label(container, text="Enter Video Title", font=self.title_font, bg="#f5f6fa", fg="#222").grid(row=0, column=0, pady=(60, 30), sticky="n")

        # Modern input frame
        input_frame = tk.Frame(container, bg="#fff", bd=0, highlightthickness=2, highlightbackground="#e0e0e0", highlightcolor="#e0e0e0")
        input_frame.grid(row=1, column=0, pady=10, ipadx=8, ipady=8, sticky="ew")
        container.grid_columnconfigure(0, weight=1)
        input_frame.grid_columnconfigure(1, weight=1)
        input_frame.grid_rowconfigure(0, weight=1)

        # Left icon
        tk.Label(input_frame, text="🔍", font=self.input_font, bg="#fff", fg="#888").grid(row=0, column=0, padx=(8, 4), sticky="w")

        # White input field
        self.title_var = tk.StringVar()
        entry = tk.Entry(input_frame, textvariable=self.title_var, font=self.input_font, width=40, bd=0, relief="flat",
                         bg="#f5f6fa", fg="#222", insertbackground="#222",
                         highlightthickness=0)
        entry.grid(row=0, column=1, padx=4, sticky="nsew")
        entry.bind("<KeyRelease>", self.on_entry_change)
        input_frame.grid_columnconfigure(1, weight=1)

        # Right icons
        tk.Label(input_frame, text="🖥️", font=self.input_font, bg="#fff", fg="#e11d48").grid(row=0, column=2, padx=4, sticky="e")
        tk.Label(input_frame, text="⌨️", font=self.input_font, bg="#fff", fg="#888").grid(row=0, column=3, padx=4, sticky="e")

        # Modern Generate button
        self.generate_btn = tk.Button(
            input_frame, text="Generate", font=self.input_font,
            bg="#e0e0e0", fg="#222", activebackground="#e11d48", activeforeground="#fff",
            state="disabled", padx=20, pady=4, bd=0, relief="flat",
            highlightthickness=0, cursor="hand2",
            command=self.on_generate
        )
        self.generate_btn.grid(row=0, column=4, padx=(10, 8), sticky="e")

        # Make all columns in input_frame expand except the icons and button
        input_frame.grid_columnconfigure(0, weight=0)
        input_frame.grid_columnconfigure(1, weight=1)
        input_frame.grid_columnconfigure(2, weight=0)
        input_frame.grid_columnconfigure(3, weight=0)
        input_frame.grid_columnconfigure(4, weight=0)

        # Credits info
        tk.Label(container, text="Credits remaining: 0  |  Estimated script credits: 0", font=self.credits_font, bg="#f5f6fa", fg="#888").grid(row=2, column=0, pady=(20, 0), sticky="s")

    def on_entry_change(self, event):
        if self.title_var.get().strip():
            self.generate_btn.config(state="normal", bg="#e11d48", fg="#fff")
        else:
            self.generate_btn.config(state="disabled", bg="#e0e0e0", fg="#222")

    def on_generate(self):
        title = self.title_var.get().strip()
        if not title:
            messagebox.showerror("Error", "Please enter a video title.")
            return
        
        # Show generating state
        self.generate_btn.config(state="disabled", text="Generating...")
        self.update()
        
        try:
            # Generate the script
            script = generate_script(title)
            
            # Navigate to script display page and pass the script
            script_display = self.controller.frames["ScriptDisplayPage"]
            script_display.set_script(script)
            self.controller.show_frame("ScriptDisplayPage")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate script: {e}")
        finally:
            self.generate_btn.config(state="normal", text="Generate") 