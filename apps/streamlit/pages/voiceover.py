"""Voiceover page: Generate voiceover audio from script."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
from pathlib import Path

from utils.voiceover import generate_voiceover, get_available_voices, estimate_voiceover_duration

class VoiceoverPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.script = ""
        self.voices = {}
        self.setup_ui()
        self.load_voices()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main title
        title_label = tk.Label(self, text="Voiceover Generation", font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # Description
        desc_label = tk.Label(self, text="Generate professional voiceover audio from your script", font=("Arial", 10))
        desc_label.pack(pady=10)
        
        # Main frame
        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left panel - Script display
        left_panel = tk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Script section
        script_frame = tk.LabelFrame(left_panel, text="Script", font=("Arial", 12, "bold"))
        script_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Script text area
        self.script_text = tk.Text(script_frame, height=15, width=50, wrap=tk.WORD, font=("Arial", 10))
        script_scrollbar = tk.Scrollbar(script_frame, orient=tk.VERTICAL, command=self.script_text.yview)
        self.script_text.configure(yscrollcommand=script_scrollbar.set)
        
        self.script_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        script_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Script info
        self.script_info_label = tk.Label(script_frame, text="No script loaded", font=("Arial", 9), fg="gray")
        self.script_info_label.pack(pady=(0, 10))
        
        # Right panel - Voiceover settings
        right_panel = tk.Frame(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # Settings frame
        settings_frame = tk.LabelFrame(right_panel, text="Voiceover Settings", font=("Arial", 12, "bold"))
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # TTS Service selection
        service_frame = tk.Frame(settings_frame)
        service_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(service_frame, text="TTS Service:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.service_var = tk.StringVar(value="Hugging Face TTS")
        service_combo = ttk.Combobox(service_frame, textvariable=self.service_var, 
                                   values=["Hugging Face TTS", "ElevenLabs", "Azure TTS", "Google TTS", "Local TTS"],
                                   state="readonly", font=("Arial", 10))
        service_combo.pack(fill=tk.X, pady=2)
        service_combo.bind("<<ComboboxSelected>>", self.on_service_change)
        
        # Voice selection
        voice_frame = tk.Frame(settings_frame)
        voice_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(voice_frame, text="Voice:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.voice_var = tk.StringVar()
        self.voice_combo = ttk.Combobox(voice_frame, textvariable=self.voice_var, state="readonly", font=("Arial", 10))
        self.voice_combo.pack(fill=tk.X, pady=2)
        
        # Service info
        self.service_info_label = tk.Label(settings_frame, text="", font=("Arial", 9), fg="blue", wraplength=200)
        self.service_info_label.pack(padx=10, pady=5)
        
        # Output settings
        output_frame = tk.Frame(settings_frame)
        output_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(output_frame, text="Output File:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        output_path_frame = tk.Frame(output_frame)
        output_path_frame.pack(fill=tk.X, pady=2)
        
        self.output_path_var = tk.StringVar(value="output/voiceovers/voiceover.mp3")
        self.output_entry = tk.Entry(output_path_frame, textvariable=self.output_path_var, font=("Arial", 9))
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_btn = tk.Button(output_path_frame, text="Browse", command=self.browse_output_path, 
                             font=("Arial", 9), bg="#4CAF50", fg="white")
        browse_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Generate button
        generate_frame = tk.Frame(settings_frame)
        generate_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.generate_btn = tk.Button(generate_frame, text="Generate Voiceover", 
                                    command=self.generate_voiceover, 
                                    font=("Arial", 12, "bold"), 
                                    bg="#2196F3", fg="white", 
                                    height=2)
        self.generate_btn.pack(fill=tk.X)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(generate_frame, variable=self.progress_var, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        # Status label
        self.status_label = tk.Label(generate_frame, text="Ready to generate voiceover", 
                                   font=("Arial", 9), fg="gray")
        self.status_label.pack(pady=5)
        
        # Results frame
        results_frame = tk.LabelFrame(right_panel, text="Results", font=("Arial", 12, "bold"))
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # Results text
        self.results_text = tk.Text(results_frame, height=8, width=30, wrap=tk.WORD, font=("Arial", 9))
        results_scrollbar = tk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=results_scrollbar.set)
        
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        results_scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Navigation buttons
        nav_frame = tk.Frame(self)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)
        
        back_btn = tk.Button(nav_frame, text="← Back to Script", 
                           command=lambda: self.controller.show_frame("ScriptDisplayPage"),
                           font=("Arial", 10), bg="#FF9800", fg="white")
        back_btn.pack(side=tk.LEFT)
        
        next_btn = tk.Button(nav_frame, text="Image Generation →", 
                           command=lambda: self.controller.show_frame("ImageGenerationPage"),
                           font=("Arial", 10), bg="#4CAF50", fg="white")
        next_btn.pack(side=tk.RIGHT)
    
    def load_voices(self):
        """Load available voices from all services."""
        try:
            self.voices = get_available_voices()
            self.update_voice_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load voices: {e}")
    
    def update_voice_list(self):
        """Update the voice dropdown based on selected service."""
        service = self.service_var.get()
        
        if service == "Hugging Face TTS":
            voices = list(self.voices.get("huggingface", {}).keys())
            self.service_info_label.config(text="🎯 FREE & FAST - No API key required!")
        elif service == "ElevenLabs":
            voices = list(self.voices.get("elevenlabs", {}).keys())
            self.service_info_label.config(text="High-quality AI voices (requires API key)")
        elif service == "Azure TTS":
            voices = list(self.voices.get("azure", {}).keys())
            self.service_info_label.config(text="Microsoft Neural voices (free tier available)")
        elif service == "Google TTS":
            voices = list(self.voices.get("google", {}).keys())
            self.service_info_label.config(text="Google Cloud TTS (free tier available)")
        elif service == "Local TTS":
            voices = self.voices.get("local", [])
            self.service_info_label.config(text="System voices (slow but reliable)")
        else:
            voices = []
            self.service_info_label.config(text="")
        
        self.voice_combo['values'] = voices
        if voices:
            self.voice_var.set(voices[0])
        else:
            self.voice_var.set("")
    
    def on_service_change(self, event=None):
        """Handle service selection change."""
        self.update_voice_list()
    
    def browse_output_path(self):
        """Browse for output file path."""
        filename = filedialog.asksaveasfilename(
            title="Save Voiceover As",
            defaultextension=".mp3",
            filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")]
        )
        if filename:
            self.output_path_var.set(filename)
    
    def generate_voiceover(self):
        """Generate voiceover in a separate thread."""
        if not self.script.strip():
            messagebox.showwarning("Warning", "No script loaded. Please go back and generate a script first.")
            return
        
        # Get selected service and voice
        service = self.service_var.get()
        voice = self.voice_var.get()
        
        if not voice:
            messagebox.showwarning("Warning", "Please select a voice.")
            return
        
        # Get voice ID based on service
        voice_id = voice
        if service == "ElevenLabs":
            voice_id = self.voices.get("elevenlabs", {}).get(voice, voice)
        elif service == "Azure TTS":
            voice_id = self.voices.get("azure", {}).get(voice, voice)
        elif service == "Google TTS":
            voice_id = self.voices.get("google", {}).get(voice, voice)
        
        # Disable generate button and show progress
        self.generate_btn.config(state=tk.DISABLED)
        self.progress_bar.start()
        self.status_label.config(text="Generating voiceover...")
        self.results_text.delete(1.0, tk.END)
        
        # Run generation in separate thread
        thread = threading.Thread(target=self._generate_voiceover_thread, 
                                args=(voice_id, service))
        thread.daemon = True
        thread.start()
    
    def _generate_voiceover_thread(self, voice_id, service):
        """Generate voiceover in background thread."""
        try:
            # Determine if we should use ElevenLabs
            use_elevenlabs = (service == "ElevenLabs")
            
            # Generate voiceover - Hugging Face is now the default
            output_path = generate_voiceover(
                script=self.script,
                voice_id=voice_id,
                output_path=self.output_path_var.get(),
                use_elevenlabs=use_elevenlabs
            )
            
            # Update UI in main thread
            self.after(0, self._on_voiceover_complete, output_path)
            
        except Exception as e:
            # Show error in main thread
            self.after(0, self._on_voiceover_error, str(e))
    
    def _on_voiceover_complete(self, output_path):
        """Handle voiceover generation completion."""
        self.generate_btn.config(state=tk.NORMAL)
        self.progress_bar.stop()
        
        if output_path:
            self.status_label.config(text="Voiceover generated successfully!", fg="green")
            
            # Show results
            results = f"✅ Voiceover Generated Successfully!\n\n"
            results += f"📁 File: {output_path}\n"
            results += f"🎵 Service: {self.service_var.get()}\n"
            results += f"🗣️ Voice: {self.voice_var.get()}\n"
            
            # Calculate file size
            try:
                file_size = os.path.getsize(output_path)
                results += f"📊 Size: {file_size / 1024:.1f} KB\n"
            except:
                pass
            
            # Estimate duration
            duration = estimate_voiceover_duration(self.script)
            results += f"⏱️ Estimated Duration: {duration:.1f} seconds\n"
            
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(1.0, results)
            
            messagebox.showinfo("Success", f"Voiceover generated successfully!\nSaved to: {output_path}")
        else:
            self.status_label.config(text="Failed to generate voiceover", fg="red")
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(1.0, "❌ Failed to generate voiceover.\n\nPlease check your API keys and try again.")
    
    def _on_voiceover_error(self, error_msg):
        """Handle voiceover generation error."""
        self.generate_btn.config(state=tk.NORMAL)
        self.progress_bar.stop()
        self.status_label.config(text="Error generating voiceover", fg="red")
        
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(1.0, f"❌ Error: {error_msg}")
        
        messagebox.showerror("Error", f"Failed to generate voiceover:\n{error_msg}")
    
    def set_script(self, script):
        """Set the script to generate voiceover from."""
        self.script = script
        self.script_text.delete(1.0, tk.END)
        self.script_text.insert(1.0, script)
        
        # Update script info
        words = len(script.split())
        duration = estimate_voiceover_duration(script)
        self.script_info_label.config(text=f"Words: {words} | Estimated Duration: {duration:.1f} seconds") 