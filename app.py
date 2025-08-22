import docker
import uuid
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import JSONResponse
import zipfile
import subprocess
import tempfile
import os
import glob
import logging

app = FastAPI()
client = docker.from_env()

@app.post("/execute")
async def execute(code: UploadFile = File(...), lang: str = Form(...)):
    contents = await code.read()

    # diretório dedicado
    base_dir = "/tmp/docker_exec"
    os.makedirs(base_dir, exist_ok=True)

    # gera um nome único para o arquivo
    file_id = str(uuid.uuid4())
    file_path = os.path.join(base_dir, f"{file_id}.py")

    # salva o código no diretório dedicado
    with open(file_path, "wb") as f:
        f.write(contents)

    try:
        container = client.containers.run(
            "python:3.11-slim",
            command=["python", f"/code/{file_id}.py"],  # dentro do container
            volumes={base_dir: {"bind": "/code", "mode": "rw"}},  # monta na pasta /code
            detach=True
        )

        exit_code = container.wait()
        logs = container.logs().decode("utf-8")
        container.remove()

        return JSONResponse({
            "status": "finished",
            "exit_code": exit_code["StatusCode"],
            "output": logs
        })

    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

    finally:
        try:
            os.remove(file_path)
        except OSError:
            pass
