import docker
import uuid
import os
import zipfile
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import tempfile

app = FastAPI()
client = docker.from_env()
TMPDIR = "/home/ubuntu/docker_exec"
os.makedirs(TMPDIR, exist_ok=True)

@app.post("/execute")
async def execute(code: UploadFile = File(...), lang: str = Form(...)):
    contents = await code.read()
    print("contents:")
    print(contents[:100])
    if lang.lower() == "java":
        project_id = uuid.uuid4().hex
        project_path = os.path.join(TMPDIR, project_id)
        os.makedirs(project_path, exist_ok=True)
    
        # Salva o zip
        zip_path = os.path.join(project_path, code.filename)
        with open(zip_path, "wb") as f:
            f.write(await file.read())
    
        # Descompacta o zip
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(project_path)
    
        # Apaga o zip
        os.remove(zip_path)
    
        try:
            # Comando para compilar todos os arquivos .java
            compile_cmd = ["javac"] + [os.path.join(project_path, f) 
                                       for f in os.listdir(project_path) if f.endswith(".java")]
    
            # Executa o container Java
            container = client.containers.run(
                "java-17-slim",           # Nome da imagem que você construiu
                command=compile_cmd,
                volumes={project_path: {"bind": "/workspace", "mode": "rw"}},
                working_dir="/workspace",
                detach=False,
                auto_remove=True
            )
    
            # Depois, roda a classe principal
            main_class = "Main"  # ou determine a partir do usuário/manifest
            run_cmd = ["java", main_class]
            output = client.containers.run(
                "java-17-slim",
                command=run_cmd,
                volumes={project_path: {"bind": "/workspace", "mode": "rw"}},
                working_dir="/workspace",
                detach=False,
                auto_remove=True
            )
    
            return {"status": "finished", "output": output.decode("utf-8")}
        finally:
            # Limpeza
            import shutil
            shutil.rmtree(project_path)
    else:
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
        host_file_path = os.path.join(tmpdir, file_name)
        print("host_file_path:")
        print(host_file_path)
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
            # Cria o container (não auto_remove)]
            language = ""
            image = ""
            if lang.lower() == "python":
                language = "python"
                image = "python-simpy"
            else:
                language = "Rscript"
                image = "r-simmer"
                
            container = client.containers.run(
                image,
                command=[language, container_file_path],  # note o path no container
                volumes={tmpdir: {"bind": "/workspace", "mode": "rw"}},
                detach=False,
                auto_remove=True
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
        finally:
        # Apaga o arquivo enviado pelo cliente para não encher a VM
            if os.path.exists(host_file_path):
                os.remove(host_file_path)
                print(f"Arquivo {host_file_path} removido.")
    
        
    return {
        "status": "finished",
        "output": logs
    }
    

