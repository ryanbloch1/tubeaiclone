import tkinter as tk
from tkinter import ttk, font, scrolledtext, messagebox
from utils.image_generation import analyze_script_for_scenes, generate_image_prompt, generate_images_for_script, get_available_services
import os
from pathlib import Path
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
import threading

class ImageGenerationPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg="#f5f6fa")
        self.controller = controller
        self.title_font = font.Font(family="Helvetica", size=20, weight="bold")
        self.text_font = font.Font(family="Helvetica", size=12)
        self.script = ""
        self.scenes = []
        self.generated_images = []
        self.image_widgets = []
        
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
                           command=lambda: controller.show_frame("VoiceoverPage"))
        back_btn.grid(row=0, column=0, sticky="w", padx=(0,20))
        
        # Title
        title_label = tk.Label(header, text="Image Generation", font=self.title_font, 
                              bg="#fff", fg="#222")
        title_label.grid(row=0, column=1, sticky="w")
        
        # Action buttons
        actions_frame = tk.Frame(header, bg="#fff")
        actions_frame.grid(row=0, column=2, sticky="e")
        
        self.analyze_btn = tk.Button(actions_frame, text="Analyze Script", font=self.text_font,
                                   bg="#00b894", fg="#fff", bd=0, padx=15, pady=5,
                                   command=self.analyze_script)
        self.analyze_btn.pack(side="left", padx=(0,10))
        
        self.generate_btn = tk.Button(actions_frame, text="Generate Images", font=self.text_font,
                                    bg="#e11d48", fg="#fff", bd=0, padx=15, pady=5,
                                    command=self.generate_images, state="disabled")
        self.generate_btn.pack(side="left", padx=(0,10))
        
        next_btn = tk.Button(actions_frame, text="Continue →", font=self.text_font,
                           bg="#f59e0b", fg="#fff", bd=0, padx=15, pady=5,
                           command=self.continue_to_next)
        next_btn.pack(side="left")

        # Main content area
        content = tk.Frame(self, bg="#fff")
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)

        # Left panel - Script and scenes
        left_panel = tk.Frame(content, bg="#fff")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0,10))
        left_panel.grid_rowconfigure(1, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)

        # Script preview
        script_label = tk.Label(left_panel, text="Script Preview:", font=self.text_font, bg="#fff")
        script_label.grid(row=0, column=0, sticky="w", pady=(0,5))

        self.script_text = scrolledtext.ScrolledText(
            left_panel, 
            font=("Consolas", 10),
            bg="#f8f9fa",
            fg="#222",
            height=10,
            wrap="word",
            padx=10,
            pady=10,
            borderwidth=0,
            relief="flat"
        )
        self.script_text.grid(row=1, column=0, sticky="nsew")

        # Right panel - Scenes and images
        right_panel = tk.Frame(content, bg="#f8f9fa", width=400)
        right_panel.grid(row=0, column=1, sticky="ns", padx=(10,0))
        right_panel.grid_propagate(False)
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        # Scenes header
        scenes_header = tk.Label(right_panel, text="Scenes & Images", 
                               font=self.text_font, bg="#f8f9fa", fg="#222")
        scenes_header.grid(row=0, column=0, sticky="ew", padx=15, pady=15)

        # Scenes content
        self.scenes_content = tk.Frame(right_panel, bg="#fff")
        self.scenes_content.grid(row=1, column=0, sticky="nsew", padx=15, pady=(0,15))
        self.scenes_content.grid_rowconfigure(0, weight=1)
        self.scenes_content.grid_columnconfigure(0, weight=1)

        # Status
        self.status_label = tk.Label(self.scenes_content, text="No script analyzed yet", 
                                   font=self.text_font, bg="#fff", fg="#666")
        self.status_label.grid(row=0, column=0, sticky="nsew")

    def set_script(self, script):
        """Set the script content and update the display"""
        self.script = script
        self.script_text.delete(1.0, tk.END)
        self.script_text.insert(1.0, script)
    
    def analyze_script(self):
        """Analyze the script and identify scenes"""
        if not self.script.strip():
            messagebox.showwarning("Warning", "No script to analyze!")
            return
        
        try:
            # Analyze script for scenes
            self.scenes = analyze_script_for_scenes(self.script)
            
            if not self.scenes:
                messagebox.showinfo("Info", "No scenes found in script. Will create one scene from the entire script.")
                self.scenes = [{
                    "text": self.script,
                    "scene_number": 1,
                    "description": "Main scene"
                }]
            
            # Update display
            self.update_scenes_display()
            
            # Enable generate button
            self.generate_btn.config(state="normal")
            
            messagebox.showinfo("Success", f"Found {len(self.scenes)} scene(s) in the script!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to analyze script: {e}")
    
    def update_scenes_display(self):
        """Update the scenes display"""
        # Clear existing content
        for widget in self.scenes_content.winfo_children():
            widget.destroy()
        
        if not self.scenes:
            self.status_label = tk.Label(self.scenes_content, text="No scenes found", 
                                       font=self.text_font, bg="#fff", fg="#666")
            self.status_label.grid(row=0, column=0, sticky="nsew")
            return
        
        # Create scrollable frame for scenes
        canvas = tk.Canvas(self.scenes_content, bg="#fff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.scenes_content, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#fff")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Add scenes
        for i, scene in enumerate(self.scenes):
            scene_frame = tk.Frame(scrollable_frame, bg="#f8f9fa", relief="flat", bd=1)
            scene_frame.pack(fill="x", padx=5, pady=5)
            
            # Scene header
            header_frame = tk.Frame(scene_frame, bg="#e0e0e0")
            header_frame.pack(fill="x", padx=5, pady=5)
            
            scene_num = tk.Label(header_frame, text=f"Scene {scene['scene_number']}", 
                               font=self.text_font, bg="#e0e0e0", fg="#222")
            scene_num.pack(side="left")
            
            # Scene text preview
            text_preview = scene["text"][:100] + "..." if len(scene["text"]) > 100 else scene["text"]
            text_label = tk.Label(scene_frame, text=text_preview, 
                                font=("Consolas", 9), bg="#f8f9fa", fg="#666", 
                                wraplength=350, justify="left")
            text_label.pack(fill="x", padx=5, pady=(0,5))
            
            # Generated prompt preview
            prompt = generate_image_prompt(scene["text"], scene["scene_number"])
            prompt_label = tk.Label(scene_frame, text=f"Prompt: {prompt[:80]}...", 
                                  font=("Consolas", 8), bg="#f8f9fa", fg="#888", 
                                  wraplength=350, justify="left")
            prompt_label.pack(fill="x", padx=5, pady=(0,5))
            
            # Image placeholder
            image_placeholder = tk.Label(scene_frame, text="[Image will be generated here]", 
                                       font=self.text_font, bg="#fff", fg="#ccc", 
                                       width=20, height=8, relief="solid", bd=1)
            image_placeholder.pack(padx=5, pady=5)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def generate_images(self):
        """Generate images for all scenes"""
        if not self.scenes:
            messagebox.showwarning("Warning", "Please analyze the script first!")
            return
        
        # Check for available services
        services = get_available_services()
        available_services = [s for s in services if s["status"] == "Available"]
        
        if not available_services:
            messagebox.showinfo("Info", "No API keys configured. Will use mock image generation for testing.")
        
        # Show generating state
        self.generate_btn.config(state="disabled", text="Generating...")
        self.update()
        
        # Run generation in a separate thread
        def generate_thread():
            try:
                # Generate images
                self.generated_images = generate_images_for_script(self.script)
                
                # Update UI in main thread
                self.after(0, self.generation_complete)
                
            except Exception as e:
                self.after(0, lambda: self.generation_error(str(e)))
        
        thread = threading.Thread(target=generate_thread)
        thread.daemon = True
        thread.start()
    
    def generation_complete(self):
        """Called when image generation is complete"""
        self.generate_btn.config(state="normal", text="Generate Images")
        
        if self.generated_images:
            messagebox.showinfo("Success", f"Generated {len(self.generated_images)} images successfully!")
            # Update display to show generated images
            self.update_scenes_display()
        else:
            messagebox.showwarning("Warning", "No images were generated. Please check your API key and try again.")
    
    def generation_error(self, error_msg):
        """Called when image generation fails"""
        self.generate_btn.config(state="normal", text="Generate Images")
        messagebox.showerror("Error", f"Failed to generate images: {error_msg}")
    
    def continue_to_next(self):
        """Continue to next step (timestamp mapping)"""
        if not self.generated_images:
            messagebox.showwarning("Warning", "Please generate images first!")
            return
        
        # For now, just show a message
        messagebox.showinfo("Next Step", "This would continue to timestamp mapping!")
        # Later: controller.show_frame("TimestampPage") 