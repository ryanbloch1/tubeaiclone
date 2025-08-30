import tkinter as tk
from tkinter import ttk, font, scrolledtext, messagebox, filedialog
from utils.voiceover import generate_voiceover, get_available_voices, estimate_voiceover_duration
import os
from pathlib import Path
from playsound import playsound
import sounddevice as sd
from scipy.io.wavfile import write
import threading
import os
try:
    import torch
    TORCH_AVAILABLE = True
except Exception:
    TORCH_AVAILABLE = False

class VoiceoverPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f5f6fa")
        self.controller = controller
        self.title_font = font.Font(family="Helvetica", size=20, weight="bold")
        self.text_font = font.Font(family="Helvetica", size=12)
        self.script = ""
        self.voiceover_path = None
        self.voice_name_to_id = {}  # Mapping for ElevenLabs voices
        
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
                           command=lambda: controller.show_frame("ScriptDisplayPage"))
        back_btn.grid(row=0, column=0, sticky="w", padx=(0,20))
        
        # Title
        title_label = tk.Label(header, text="Voiceover Generation", font=self.title_font, 
                              bg="#fff", fg="#222")
        title_label.grid(row=0, column=1, sticky="w")
        
        # Action buttons
        actions_frame = tk.Frame(header, bg="#fff")
        actions_frame.grid(row=0, column=2, sticky="e")
        
        self.generate_btn = tk.Button(actions_frame, text="Generate Voiceover", font=self.text_font,
                                    bg="#00b894", fg="#fff", bd=0, padx=15, pady=5,
                                    command=self.generate_voiceover)
        self.generate_btn.pack(side="left", padx=(0,10))
        
        next_btn = tk.Button(actions_frame, text="Continue →", font=self.text_font,
                           bg="#e11d48", fg="#fff", bd=0, padx=15, pady=5,
                           command=self.continue_to_next)
        next_btn.pack(side="left")

        # Main content area
        content = tk.Frame(self, bg="#fff")
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)

        # Left panel - Script and settings
        left_panel = tk.Frame(content, bg="#fff")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0,10))
        left_panel.grid_rowconfigure(1, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)

        # Settings frame
        settings_frame = tk.Frame(left_panel, bg="#f8f9fa", padx=15, pady=15)
        settings_frame.grid(row=0, column=0, sticky="ew", pady=(0,15))
        settings_frame.grid_columnconfigure(1, weight=1)

        # Voice selection
        tk.Label(settings_frame, text="Voice:", font=self.text_font, bg="#f8f9fa").grid(row=0, column=0, sticky="w", pady=5)
        self.voice_var = tk.StringVar()
        voices = get_available_voices()
        # Store mapping for ElevenLabs voices
        self.voice_name_to_id = voices["elevenlabs"]
        voice_options = list(self.voice_name_to_id.keys()) + voices["local"]
        self.voice_var.set(voice_options[0] if voice_options else "default")
        voice_combo = ttk.Combobox(settings_frame, textvariable=self.voice_var, values=voice_options, 
                                  font=self.text_font, state="readonly")
        voice_combo.grid(row=0, column=1, sticky="ew", padx=(10,0), pady=5)

        # TTS Engine selection
        tk.Label(settings_frame, text="Engine:", font=self.text_font, bg="#f8f9fa").grid(row=1, column=0, sticky="w", pady=5)
        self.engine_var = tk.StringVar(value="ElevenLabs")
        engine_combo = ttk.Combobox(settings_frame, textvariable=self.engine_var, 
                                   values=["ElevenLabs", "Local TTS"], 
                                   font=self.text_font, state="readonly")
        engine_combo.grid(row=1, column=1, sticky="ew", padx=(10,0), pady=5)

        # Voice sample controls for XTTS
        sample_frame = tk.Frame(settings_frame, bg="#f8f9fa")
        sample_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10,0))
        self.sample_label = tk.Label(sample_frame, text="Current sample: voice_sample.wav", font=("Helvetica", 10), bg="#f8f9fa", fg="#555")
        self.sample_label.pack(side="left", padx=(0,10))
        tk.Button(sample_frame, text="Record Sample", font=("Helvetica", 10), command=self.record_sample).pack(side="left", padx=(0,5))
        tk.Button(sample_frame, text="Select Sample", font=("Helvetica", 10), command=self.select_sample).pack(side="left")

        # Script preview
        script_label = tk.Label(left_panel, text="Script Preview:", font=self.text_font, bg="#fff")
        script_label.grid(row=1, column=0, sticky="w", pady=(0,5))

        self.script_text = scrolledtext.ScrolledText(
            left_panel, 
            font=("Consolas", 10),
            bg="#f8f9fa",
            fg="#222",
            height=15,
            wrap="word",
            padx=10,
            pady=10,
            borderwidth=0,
            relief="flat"
        )
        self.script_text.grid(row=2, column=0, sticky="nsew")

        # Right panel - Status and controls
        right_panel = tk.Frame(content, bg="#f8f9fa", width=300)
        right_panel.grid(row=0, column=1, sticky="ns", padx=(10,0))
        right_panel.grid_propagate(False)
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        # Status header
        status_header = tk.Label(right_panel, text="Generation Status", 
                               font=self.text_font, bg="#f8f9fa", fg="#222")
        status_header.grid(row=0, column=0, sticky="ew", padx=15, pady=15)

        # Status content
        status_content = tk.Frame(right_panel, bg="#fff")
        status_content.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0,15))
        status_content.grid_rowconfigure(1, weight=1)
        status_content.grid_columnconfigure(0, weight=1)

        # Script info
        self.script_info = tk.Label(status_content, text="No script loaded", 
                                  font=self.text_font, bg="#fff", fg="#666", justify="left")
        self.script_info.grid(row=0, column=0, sticky="w", pady=(10,5))

        # Progress bar
        self.progress = ttk.Progressbar(status_content, mode='indeterminate')
        self.progress.grid(row=1, column=0, sticky="ew", pady=5)

        # Status text
        # Device status
        device_str = "CPU"
        if TORCH_AVAILABLE:
            try:
                if hasattr(torch, 'cuda') and torch.cuda.is_available():
                    device_str = "GPU"
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    device_str = "MPS"
            except Exception:
                pass
        self.device_label = tk.Label(status_content, text=f"Device: {device_str}",
                                     font=self.text_font, bg="#fff", fg="#666")
        self.device_label.grid(row=2, column=0, sticky="w", pady=(0,5))

        self.status_text = tk.Label(status_content, text="Ready to generate voiceover", 
                                  font=self.text_font, bg="#fff", fg="#666")
        self.status_text.grid(row=3, column=0, sticky="w", pady=5)

        # Audio player frame (placeholder)
        audio_frame = tk.Frame(status_content, bg="#fff")
        audio_frame.grid(row=3, column=0, sticky="ew", pady=(10,0))

        self.audio_label = tk.Label(audio_frame, text="No audio generated yet", 
                                  font=self.text_font, bg="#fff", fg="#666")
        self.audio_label.pack()

        # Play button (initially disabled)
        self.play_btn = tk.Button(audio_frame, text="Play Voiceover", font=self.text_font, bg="#00b894", fg="#fff", bd=0, padx=15, pady=5, state="disabled", command=self.play_voiceover)
        self.play_btn.pack(pady=(10,0))

    def set_script(self, script):
        """Set the script content and update the display"""
        self.script = script
        self.script_text.delete(1.0, tk.END)
        self.script_text.insert(1.0, script)
        
        # Update script info
        words = len(script.split())
        duration = estimate_voiceover_duration(script)
        self.script_info.config(text=f"Script: {words} words\nEstimated duration: {duration:.1f} seconds")
    
    def generate_voiceover(self):
        """Generate voiceover from the current script"""
        if not self.script.strip():
            messagebox.showwarning("Warning", "No script to generate voiceover from!")
            return
        
        # Get settings
        voice_name = self.voice_var.get()
        engine = self.engine_var.get()
        
        # Determine the correct voice_id
        if engine == "ElevenLabs" and voice_name in self.voice_name_to_id:
            voice_id = self.voice_name_to_id[voice_name]
        else:
            voice_id = voice_name  # For local TTS, use the name
        
        # Show generating state
        self.generate_btn.config(state="disabled", text="Generating...")
        self.progress.start()
        self.status_text.config(text="Generating voiceover...")
        self.update()
        
        try:
            # Generate voiceover
            use_elevenlabs = engine == "ElevenLabs"
            voiceover_path = generate_voiceover(
                script=self.script,
                voice_id=voice_id,
                use_elevenlabs=use_elevenlabs
            )
            
            if voiceover_path:
                self.voiceover_path = voiceover_path
                self.audio_label.config(text=f"✅ Voiceover generated!\nSaved to: {os.path.basename(voiceover_path)}")
                self.status_text.config(text="Voiceover generation completed!")
                self.play_btn.config(state="normal")
                messagebox.showinfo("Success", f"Voiceover generated successfully!\nSaved to: {voiceover_path}")
            else:
                self.audio_label.config(text="❌ Voiceover generation failed")
                self.status_text.config(text="Generation failed")
                self.play_btn.config(state="disabled")
                messagebox.showerror("Error", "Failed to generate voiceover. Please check your settings.")
                
        except Exception as e:
            self.audio_label.config(text="❌ Voiceover generation failed")
            self.status_text.config(text="Generation failed")
            self.play_btn.config(state="disabled")
            messagebox.showerror("Error", f"Failed to generate voiceover: {e}")
        finally:
            self.generate_btn.config(state="normal", text="Generate Voiceover")
            self.progress.stop()
    
    def continue_to_next(self):
        """Continue to next step (image generation)"""
        if not self.voiceover_path:
            messagebox.showwarning("Warning", "Please generate a voiceover first!")
            return
        
        # Pass script to image generation page
        image_page = self.controller.frames["ImageGenerationPage"]
        image_page.set_script(self.script)
        self.controller.show_frame("ImageGenerationPage") 

    def play_voiceover(self):
        """Play the generated voiceover audio file"""
        if self.voiceover_path and os.path.exists(self.voiceover_path):
            try:
                playsound(self.voiceover_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to play audio: {e}")
        else:
            messagebox.showwarning("Warning", "No voiceover audio file found!") 

    def record_sample(self):
        """Record a new voice sample using the microphone and save as voice_sample.wav"""
        def do_record():
            fs = 22050  # Sample rate
            seconds = 5  # Duration
            self.status_text.config(text="Recording... Speak now!")
            self.update()
            try:
                audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1, dtype='int16')
                sd.wait()
                write('voice_sample.wav', fs, audio)
                self.sample_label.config(text="Current sample: voice_sample.wav")
                self.status_text.config(text="Recording complete!")
                messagebox.showinfo("Success", "Voice sample recorded and saved as voice_sample.wav")
            except Exception as e:
                self.status_text.config(text="Recording failed")
                messagebox.showerror("Error", f"Failed to record sample: {e}")
            self.status_text.config(text="Ready to generate voiceover")
        threading.Thread(target=do_record).start()

    def select_sample(self):
        """Select an existing WAV file as the voice sample for XTTS"""
        file_path = filedialog.askopenfilename(filetypes=[("WAV files", "*.wav")])
        if file_path:
            try:
                import shutil
                shutil.copy(file_path, 'voice_sample.wav')
                self.sample_label.config(text="Current sample: voice_sample.wav")
                messagebox.showinfo("Success", f"Voice sample set to: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to set sample: {e}") 