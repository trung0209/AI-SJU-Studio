from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uuid
import json
import requests
import random
import os
from PIL import Image
import io
import websockets
import asyncio

app = FastAPI()
client_id = str(uuid.uuid4())
server_address = "war-others-pizza-controls.trycloudflare.com"

# Ensure the 'images' directory exists
if not os.path.exists('images'):
    os.makedirs('images')

# Pydantic model for the request body
class GenerateRequest(BaseModel):
    positive_prompt: str
    negative_prompt: str
    seed: int = None  # Optional seed parameter

async def connect_websocket(ws_url):
    ws = await websockets.connect(ws_url)
    return ws

async def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    url = f"https://{server_address}/prompt"
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, json=p, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        error_message = response.text
        print(f"HTTP Error {response.status_code}: {e}\nDetails: {error_message}")
        return None

async def get_history(prompt_id):
    url = f"https://{server_address}/history/{prompt_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error {response.status_code}: {e}")
        return None

async def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url = f"https://{server_address}/view"
    try:
        response = requests.get(url, params=data)
        response.raise_for_status()
        return response.content
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error {response.status_code}: {e}")
        return None

async def get_images(ws, prompt):
    response = await queue_prompt(prompt)
    if response is None or 'prompt_id' not in response:
        print("Failed to queue prompt.")
        return {}
    prompt_id = response['prompt_id']
    print(f"Queued prompt with ID: {prompt_id}")
    output_images = {}
    while True:
        try:
            out = await ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['node'] is None and data['prompt_id'] == prompt_id:
                        print("Execution completed.")
                        break  # Execution is done
            else:
                continue  # Handle binary data if necessary
        except Exception as e:
            print(f"Error receiving WebSocket message: {e}")
            break

    history_data = await get_history(prompt_id)
    if history_data is None or prompt_id not in history_data:
        print("Failed to retrieve history.")
        return {}
    history = history_data[prompt_id]
    print("Retrieved history.")

    if 'outputs' not in history:
        print("No outputs in history.")
        return {}

    for node_id, node_output in history['outputs'].items():
        print(f"Processing node {node_id}")
        if 'images' in node_output:
            images_output = []
            for image_info in node_output['images']:
                image_data = await get_image(image_info['filename'], image_info['subfolder'], image_info['type'])
                if image_data is not None:
                    images_output.append(image_data)
                    print(f"Retrieved image {image_info['filename']}")
                else:
                    print(f"Failed to retrieve image {image_info['filename']}")
            if images_output:
                output_images[node_id] = images_output
            else:
                print(f"No images retrieved for node {node_id}")

    return output_images

# FastAPI endpoint with Pydantic model
@app.post("/generate")
async def generate_image(request: GenerateRequest):
    # Load workflow from file
    with open("workflow_api.json", "r", encoding="utf-8") as f:
        workflow_data = f.read()
    workflow = json.loads(workflow_data)

    # Modify the workflow using the request data
    workflow["6"]["inputs"]["text"] = request.positive_prompt
    workflow["71"]["inputs"]["text"] = request.negative_prompt

    # Use provided seed or generate a random one
    seed = request.seed if request.seed is not None else random.randint(1, 1000000000)
    workflow["271"]["inputs"]["seed"] = seed

    # Ensure the models specified exist on the server or adjust accordingly
    workflow["252"]["inputs"]["ckpt_name"] = "sd3_medium_incl_clips.safetensors"
    workflow["11"]["inputs"]["clip_name2"] = "clip_l.safetensors"
    workflow["273"]["inputs"]["clip_name"] = "clip_l.safetensors"
    workflow["11"]["inputs"]["clip_name1"] = "clip_g.safetensors"
    workflow["11"]["inputs"]["clip_name3"] = "t5xxl_fp8_e4m3fn.safetensors"
    # Start the WebSocket connection
    ws_url = f"wss://{server_address}/ws?clientId={client_id}"
    try:
        ws = await connect_websocket(ws_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"WebSocket connection failed: {e}")

    images = await get_images(ws, workflow)
    await ws.close()
    if not images:
        raise HTTPException(status_code=500, detail="No images retrieved.")
    else:
        saved_images = []
        for node_id in images:
            for idx, image_data in enumerate(images[node_id]):
                try:
                    image = Image.open(io.BytesIO(image_data))
                    image_filename = f"images/{node_id}-{seed}-{idx}.png"
                    image.save(image_filename)
                    saved_images.append(image_filename)
                except Exception as e:
                    print(f"Error saving image for node {node_id}: {e}")

        return {"status": "success", "images": saved_images}

# Serve images statically
app.mount("/images", StaticFiles(directory="images"), name="images")
