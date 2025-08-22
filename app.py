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
    print("contents:")
    print(contents[:100])
#with tempfile.TemporaryDirectory() as tmpdir:
    # Gera nome único para o arquivo
    tmpdir = "/home/ubuntu/docker_exec"
    os.makedirs(tmpdir, exist_ok=True)
    os.chmod(tmpdir, 0o777)
    print("tmpdir:")
    print(tmpdir)
    file_name = f"{uuid.uuid4().hex}.py"
    print("file_name:")
    print(file_name)
    host_file_path = os.path.join(tmpdir, "code.py")
    print("host_file_path:")
    print(host_file_path)
    host_file_path = os.path.join(tmpdir, "code.py")  
    # Grava o código do cliente
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
        # Cria o container (não auto_remove)

        container = client.containers.run(
            "python:3.11-slim",
            command=["python", "/workspace/code.py"],  # note o path no container
            volumes={tmpdir: {"bind": "/workspace", "mode": "rw"}},
            detach=False,
            auto_remove=False
        )
   
        # Agora você pode executar comandos dentro do container
        #exit_code, output = container.exec_run("ls -l /workspace")
        #print(output.decode())

        #exit_code, output = container.exec_run(f"cat workspace/code.py")
        #print(output.decode())

        #container.exec_run("python /workspace/code.py")

        # Depois finalize o container
        logs = container.decode("utf-8")
        #container.stop()
        #container.remove()

        
        return {
            "status": "finished",
            "output": logs
        }
    
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)})
