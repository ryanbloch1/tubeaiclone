import tkinter as tk
from tkinter import ttk, font, scrolledtext
from tkinter import messagebox
from utils.sanitization import sanitize_script, split_script_into_segments, add_voiceover_instructions

class ScriptDisplayPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f5f6fa")
        self.controller = controller
        self.title_font = font.Font(family="Helvetica", size=20, weight="bold")
        self.text_font = font.Font(family="Helvetica", size=12)
        self.script = ""
        
        # Make the frame responsive
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Header
        header = tk.Frame(self, bg="#fff", height=60)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20,0))
        header.grid_columnconfigure(1, weight=1)
        header.grid_propagate(False)
        
        # Back button
        back_btn = tk.Button(header, text="← Back", font=self.text_font, 
                           bg="#e0e0e0", fg="#222", bd=0, padx=15, pady=5,
                           command=lambda: controller.show_frame("TitleEntryPage"))
        back_btn.grid(row=0, column=0, sticky="w", padx=(0,20))
        
        # Title
        title_label = tk.Label(header, text="Generated Script", font=self.title_font, 
                              bg="#fff", fg="#222")
        title_label.grid(row=0, column=1, sticky="w")
        
        # Action buttons
        actions_frame = tk.Frame(header, bg="#fff")
        actions_frame.grid(row=0, column=2, sticky="e")
        
        self.sanitize_btn = tk.Button(actions_frame, text="Sanitize Script", font=self.text_font,
                                    bg="#f59e0b", fg="#fff", bd=0, padx=15, pady=5,
                                    command=self.sanitize_script)
        self.sanitize_btn.pack(side="left", padx=(0,10))
        
        copy_btn = tk.Button(actions_frame, text="Copy Script", font=self.text_font,
                           bg="#e11d48", fg="#fff", bd=0, padx=15, pady=5,
                           command=self.copy_script)
        copy_btn.pack(side="left", padx=(0,10))
        
        next_btn = tk.Button(actions_frame, text="Continue →", font=self.text_font,
                           bg="#00b894", fg="#fff", bd=0, padx=15, pady=5,
                           command=self.continue_to_next)
        next_btn.pack(side="left")

        # Main content area
        content = tk.Frame(self, bg="#fff")
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)

        # Script editor
        script_frame = tk.Frame(content, bg="#fff")
        script_frame.grid(row=0, column=0, sticky="nsew")
        script_frame.grid_rowconfigure(0, weight=1)
        script_frame.grid_columnconfigure(0, weight=1)

        # Script text area
        self.script_text = scrolledtext.ScrolledText(
            script_frame, 
            font=("Consolas", 11),
            bg="#f8f9fa",
            fg="#222",
            insertbackground="#222",
            selectbackground="#e11d48",
            selectforeground="#fff",
            wrap="word",
            padx=15,
            pady=15,
            borderwidth=0,
            relief="flat"
        )
        self.script_text.grid(row=0, column=0, sticky="nsew")

        # Scene breakdown panel
        breakdown_frame = tk.Frame(content, bg="#f8f9fa", width=300)
        breakdown_frame.grid(row=0, column=1, sticky="ns", padx=(20,0))
        breakdown_frame.grid_propagate(False)
        breakdown_frame.grid_rowconfigure(1, weight=1)
        breakdown_frame.grid_columnconfigure(0, weight=1)

        # Breakdown header
        breakdown_header = tk.Label(breakdown_frame, text="Scene Breakdown", 
                                  font=self.text_font, bg="#f8f9fa", fg="#222")
        breakdown_header.grid(row=0, column=0, sticky="ew", padx=15, pady=15)

        # Scene list
        self.scene_listbox = tk.Listbox(
            breakdown_frame,
            font=("Consolas", 10),
            bg="#fff",
            fg="#222",
            selectbackground="#e11d48",
            selectforeground="#fff",
            borderwidth=0,
            relief="flat",
            activestyle="none"
        )
        self.scene_listbox.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0,15))
        
        # Scrollbar for scene list
        scene_scrollbar = ttk.Scrollbar(breakdown_frame, orient="vertical", command=self.scene_listbox.yview)
        scene_scrollbar.grid(row=1, column=1, sticky="ns")
        self.scene_listbox.configure(yscrollcommand=scene_scrollbar.set)

    def set_script(self, script):
        """Set the script content and update the display"""
        self.script = script
        self.script_text.delete(1.0, tk.END)
        self.script_text.insert(1.0, script)
        
        # Parse and display scenes
        self.update_scene_breakdown(script)
    
    def update_scene_breakdown(self, script):
        """Parse script and update scene breakdown"""
        self.scene_listbox.delete(0, tk.END)
        
        lines = script.split('\n')
        scene_count = 0
        
        for line in lines:
            line = line.strip()
            if line.startswith('Scene ') and ':' in line:
                scene_count += 1
                # Extract scene info
                scene_info = line.split(':', 1)[0]
                self.scene_listbox.insert(tk.END, f"Scene {scene_count}")
        
        if scene_count == 0:
            self.scene_listbox.insert(tk.END, "No scenes detected")
    
    def sanitize_script(self):
        """Sanitize the current script for YouTube safety and voiceover optimization"""
        current_script = self.script_text.get(1.0, tk.END).strip()
        if not current_script:
            messagebox.showwarning("Warning", "No script to sanitize!")
            return
        
        try:
            # Show sanitizing state
            self.sanitize_btn.config(state="disabled", text="Sanitizing...")
            self.update()
            
            # Sanitize the script
            sanitized_script = sanitize_script(current_script)
            
            # Update the display
            self.script_text.delete(1.0, tk.END)
            self.script_text.insert(1.0, sanitized_script)
            self.script = sanitized_script
            
            # Update scene breakdown
            self.update_scene_breakdown(sanitized_script)
            
            # Show success message
            messagebox.showinfo("Success", "Script sanitized successfully!\n\nChanges made:\n• Removed markdown formatting\n• Cleaned up profanity and sensitive content\n• Normalized spacing and punctuation\n• Optimized for voiceover")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to sanitize script: {e}")
        finally:
            self.sanitize_btn.config(state="normal", text="Sanitize Script")
    
    def copy_script(self):
        """Copy script to clipboard"""
        script_content = self.script_text.get(1.0, tk.END)
        self.clipboard_clear()
        self.clipboard_append(script_content)
        messagebox.showinfo("Copied", "Script copied to clipboard!")
    
    def continue_to_next(self):
        """Continue to next step (voiceover generation)"""
        # Pass the script to the voiceover page
        voiceover_page = self.controller.frames["VoiceoverPage"]
        voiceover_page.set_script(self.script)
        self.controller.show_frame("VoiceoverPage") 