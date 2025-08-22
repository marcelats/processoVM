from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import docker
import os

app = FastAPI()
client = docker.from_env()

@app.post("/run")
async def run_code(request: Request):
    body = await request.json()
    code = body.get("code", "")

    # caminho local temporário
    file_path = "/tmp/code.py"
    with open(file_path, "w") as f:
        f.write(code)

    # cria container com bind mount do arquivo
    container = client.containers.run(
        image="python:3.9-slim",
        command=["python", "/tmp/code.py"],   # importante usar caminho absoluto dentro do container
        volumes={file_path: {"bind": "/tmp/code.py", "mode": "ro"}},
        detach=True
    )


    result = container.wait()  # espera terminar
    logs = container.logs().decode("utf-8")  # pega saída
    container.remove()  # limpa

    return JSONResponse({
        "status": "finished",
        "returncode": result.get("StatusCode"),
        "output": logs
    })
