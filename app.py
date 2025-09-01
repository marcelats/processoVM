import docker
import uuid
import os
import zipfile
import shutil
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import tempfile
import logging
app = FastAPI()
client = docker.from_env()
TMPDIR = "/home/ubuntu/docker_exec"
os.makedirs(TMPDIR, exist_ok=True)

@app.post("/execute")
async def execute(code: UploadFile = File(...), lang: str = Form(...)):

    contents = await code.read()
    print("contents:")
    print(contents[:100])
    tmpdir = os.path.abspath("/home/ubuntu/docker_exec")
    output = client.containers.run(
    
        "python:3.11-slim",
    
        command=["ls", "-l", "/workspace"],
    
        volumes={tmpdir: {'bind': '/workspace', 'mode': 'rw'}},
    
        detach=False,
    
        auto_remove=False
    
    )
    
    
    
    
    
    print(output.decode())
