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
    tmpdir = os.path.abspath("/tmp/docker_exec")
    os.makedirs(tmpdir, exist_ok=True)
    os.chmod(tmpdir, 0o777)
    print("tmpdir:")
    print(tmpdir)
    file_name=""
    if lang.lower() == "python":
        file_name = "code.py"
    elif lang.lower() == "c smpl":
        file_name = "code.c"
    else:
        file_name = "code.r"
    print("file_name:")
    print(file_name)
    output = client.containers.run(
    
        "python:3.11-slim",
    
        command=["ls", "-l", "/workspace"],
    
        volumes={tmpdir: {'bind': '/workspace', 'mode': 'rw'}},
    
        detach=False,
    
        auto_remove=False
    
    )
    
    
    
    
    
    print(output.decode())
