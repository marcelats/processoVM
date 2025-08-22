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

    # gera um nome temporário de arquivo único
    file_id = str(uuid.uuid4())
    file_path = f"/tmp/{file_id}.py"

    # grava o código em um arquivo temporário
    with open(file_path, "w") as f:
        f.write(contents)

    try:
        # executa container e monta o arquivo
        container = client.containers.run(
            "python:3.11-slim",
            command=["python", f"/tmp/{file_id}.py"],
            volumes={"/tmp": {"bind": "/tmp", "mode": "rw"}},
            detach=True
        )

        # espera o container terminar
        exit_code = container.wait()
        logs = container.logs().decode("utf-8")

        # remove container depois
        container.remove()

        return JSONResponse({
            "status": "finished",
            "exit_code": exit_code["StatusCode"],
            "output": logs
        })

    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})

    finally:
        # apaga o arquivo temporário
        try:
            import os
            os.remove(file_path)
        except OSError:
            pass
            
