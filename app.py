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
    file_path = f"/tmp/{file_id}.py"
    with open(file_path, "wb") as f:
        f.write(contents)


    # cria container com bind mount do arquivo
    container = client.containers.run(
        "python:3.11-slim",
        command=f"python /tmp/{file_id}.py",
        volumes={ "/tmp": {"bind": "/tmp", "mode": "rw"} },  # monta /tmp do host no /tmp do container
        working_dir="/tmp",  # define diretório de trabalho
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
