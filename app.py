import docker
import uuid
import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import tempfile

app = FastAPI()
client = docker.from_env()

@app.post("/execute")
async def execute(code: UploadFile = File(...), lang: str = Form(...)):
    if lang.lower() != "python":
        return JSONResponse({"status": "error", "message": "Only Python is supported."})
    
    contents = await code.read()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Gera nome único para o arquivo
        file_name = f"{uuid.uuid4().hex}.py"
        print("file_name")
        print(file_name)
        host_file_path = os.path.join(tmpdir, file_name)
        print("host_file_path")
        print(host_file_path)
        
        # Grava o código do cliente
        with open(host_file_path, "wb") as f:
            f.write(contents)
            print("f")
            print(f)
        
        container_file_path = f"/workspace/{file_name}"
        print("container_file_path")
        print(container_file_path)
        
        try:
            # Cria o container (não auto_remove)
            container = client.containers.run(
                "python:3.11-slim",
                command=["python", container_file_path],
                volumes={tmpdir: {"bind": "/workspace", "mode": "rw"}},
                detach=True,
                auto_remove=False
            )
            
            # Espera terminar
            exit_status = container.wait()
            
            # Captura logs
            logs = container.logs(stdout=True, stderr=True).decode("utf-8")
            
            # Remove o container manualmente
            container.remove()
            
            return JSONResponse({
                "status": "finished",
                "exit_code": exit_status.get("StatusCode", -1),
                "output": logs
            })
        
        except Exception as e:
            return JSONResponse({"status": "error", "message": str(e)})
