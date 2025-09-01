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
    #tmpdir = os.path.abspath("/tmp/docker_exec")
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
    host_file_path = os.path.join(tmpdir, "code.py")
    print("host_file_path:")
    print(host_file_path)
    with open(host_file_path, "wb") as f:
        f.write(contents)
        print("f:")
        print(f)
    with open(host_file_path, "rb") as f:
        print("dentro de f:")
        print(f.read(100))
    print("Arquivos em tmpdir:", os.listdir(tmpdir))
    for filename in os.listdir(tmpdir):
        file_path = os.path.join(tmpdir, filename)
        # verifica se é um arquivo regular (não diretório)
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(100)  # lê os primeiros 100 caracteres
            print(f"Arquivo: {filename}")
            print(f"Conteúdo (100 primeiros caracteres):\n{content}")
            print("-" * 40)
    container_file_path = f"/workspace/{file_name}"
    print("container_file_path")
    print(container_file_path)
    try:
        command = []
        image = ""
        volumes = {}
        if lang.lower() == "python":
            command = ["python", container_file_path]
            image = "python-simpy"
            volumes={tmpdir: {"bind": "/workspace", "mode": "rw"}}
        elif lang.lower() == "c smpl":
            LIBS_DIR = "/opt/smpl"
            language = [
                "bash", "-c",
                "gcc /workspace/code/{main} -I/workspace/libs /workspace/libs/*.c -o /workspace/code/a.out && /workspace/code/a.out".format(main=host_file_path)
            ]
            image="c_runner:latest"
            volumes = {
                tmpdir: {"bind": "/workspace", "mode": "ro"},
                LIBS_DIR: {"bind": "/smpl", "mode": "ro"},
            }
        else:
            command = ["Rscript", container_file_path]
            image = "r-simmer"
            volumes={tmpdir: {"bind": "/workspace", "mode": "rw"}}
    finally:
        if os.path.exists(host_file_path):
            os.remove(host_file_path)
            print(f"Arquivo {host_file_path} removido.")
            
    output = client.containers.run(
    
        "python:3.11-slim",
    
        command=["ls", "-l", "/workspace"],
    
        volumes={tmpdir: {'bind': '/workspace', 'mode': 'rw'}},
    
        detach=False,
    
        auto_remove=False
    
    )
    
    
    
    
    
    print(output.decode())
