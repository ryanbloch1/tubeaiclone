import os
import time
from diffusers import StableDiffusionPipeline
import torch
from PIL import Image

prompt = os.environ.get("PROMPT", "a professional photograph of an astronaut riding a horse, 4k, high detail")
outdir = os.environ.get("OUTDIR", "/Users/ryan.bloch/Desktop/tubeaiclone/output/images")
model_id = os.environ.get("MODEL_ID", "stabilityai/stable-diffusion-2-1-base")

os.makedirs(outdir, exist_ok=True)

torch_dtype = torch.float16 if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available() else torch.float32
pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch_dtype)

if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
    pipe = pipe.to("mps")
else:
    pipe = pipe.to("cpu")

start = time.time()
image = pipe(prompt, num_inference_steps=30, guidance_scale=7.5).images[0]
fn = os.path.join(outdir, f"sd2_txt2img_{int(start)}.png")
image.save(fn)
print(fn)
print(f"elapsed: {time.time()-start:.1f}s, device: {'mps' if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available() else 'cpu'}")
