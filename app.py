from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import docker
import tempfile
import os
import uuid

app = FastAPI()
client = docker.from_env()  # Conecta ao Docker no host

@app.post("/execute")
async def execute(code: UploadFile = File(...)):
    # Cria um ID único para o arquivo
    file_id = str(uuid.uuid4())
    
    # Cria um diretório temporário isolado
    with tempfile.TemporaryDirectory(prefix=f"docker_exec_{file_id}_") as tmpdir:
        # Caminho do arquivo Python no host
        host_file_path = os.path.join(tmpdir, "code.py")
        
        # Salva o conteúdo do upload no host
        contents = await code.read()
        with open(host_file_path, "wb") as f:
            f.write(contents)
        
        try:
            # Executa o container Python montando o arquivo
            container = client.containers.run(
                "python:3.11-slim",
                command="python /tmp/code.py",
                volumes={tmpdir: {"bind": "/tmp", "mode": "rw"}},  # monta tmpdir no container
                working_dir="/tmp",
                detach=True,
                auto_remove=True
            )

            # Espera o container terminar
            exit_code = container.wait()
            logs = container.logs().decode("utf-8")

            return JSONResponse({
                "status": "finished",
                "exit_code": exit_code.get("StatusCode", -1),
                "output": logs
            })

        except Exception as e:
            return JSONResponse({
                "status": "error",
                "message": str(e)
            })
