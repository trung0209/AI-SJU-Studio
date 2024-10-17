# AI-SJU-Studio
Using ComfyUI for building and testing pipline.

Environment recommendations: 
Using google collab: ComfyUI/notebooks/comfyui_colab.ipynb at master · comfyanonymous/ComfyUI (github.com)

You can use your local machine please check the github link for detail installation:
comfyanonymous/ComfyUI: The most powerful and modular diffusion model GUI, api and backend with a graph/nodes interface. (github.com)

Stage 1: Building Pipeline for text to image
Each member need to construct a pipline using ComfyUI:

1.	Marina, Nilufar
•	black-forest-labs/FLUX.1-dev · Hugging Face
2.	Hung,Maksim: use the smaller version of SD3 which only use 2 endcoder. Link for download encoder if needed
•	Link for encoder: stabilityai/stable-diffusion-3-medium · Hugging Face
•	Link for model check point sd3_medium_incl_clips.safetensors (5.5GB)

Please try to adjust parameter if needed or add/change different layer to orginal pipline to produce best output. 
If better try to apply any optimization techniques to model such as Lora(optional)

Example is a basic text-to-image using SD1.5 model, you need to construct the same for your assign modelel and modify if needed 
How to submit: send me your email or marina so I will add to git collaborator to monitor progress
To export the pipline use save button then you can upload the export pipline to git
If any problem arise or questions please send in the group or private
Deadline: Monday 28 but if possible send early
