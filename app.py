import docker
import requests
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
    if lang.lower() == "java":
        output_path = "/workspace/out"
        os.makedirs(output_path, exist_ok=True)
        project_id = uuid.uuid4().hex
        project_path = os.path.join(TMPDIR, project_id)
        os.makedirs(project_path, exist_ok=True)
        jar_path = os.path.join(os.path.dirname(__file__), 'javasim-2.3.jar')

        if not os.path.exists(jar_path):
            raise FileNotFoundError(f"Arquivo .jar não encontrado: {jar_path}")
        else:
            logging.info(f"JAR localizado: {jar_path}")
        # Salva o zip
        zip_path = os.path.join(project_path, code.filename)
        with open(zip_path, "wb") as f:
            #f.write(await code.read())
            shutil.copyfileobj(code.file, f)
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(project_path)
        except zipfile.BadZipFile:
            return {"status": "error", "message": "O arquivo enviado não é um zip válido"}

        # Descompacta o zip
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(project_path)
        # Apaga o zip
        os.remove(zip_path)

        try:
            # Comando para compilar todos os arquivos .java
            java_files = []
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    if file.endswith(".java"):
                        # transforma o caminho do host para o caminho dentro do container
                        container_path = os.path.join("/workspace", os.path.relpath(os.path.join(root, file), project_path))
                        java_files.append(container_path)
            compile_cmd = [
                "javac",
                "-cp", "/workspace/javasim-2.3.jar",
                "-d", "/workspace/out"
            ] + java_files
            shutil.copy(jar_path, project_path) 
            container = client.containers.run(
                "java-17-slim",           # Nome da imagem que você construiu
                command=compile_cmd,
                volumes = {
                    project_path: {"bind": "/workspace", "mode": "rw"},
                },
                working_dir="/workspace",
                detach=False,
                auto_remove=True
            )
            run_cmd = [
                "java",
                "-cp", "/workspace/out:/workspace/javasim-2.3.jar",
                "com.javasim.teste.basic.Main"
            ]
            log_config = LogConfig(type="none")
            container = client.containers.run(
                "java-17-slim",
                command=run_cmd,
                volumes = {
                    project_path: {"bind": "/workspace", "mode": "rw"},
                },
                working_dir="/workspace",
                detach=True,
                auto_remove=False,
                mem_limit="512m",     # 512 MB RAM
                log_config=log_config
            )

            try:
                exit_code = container.wait(timeout=10)["StatusCode"]  # tempo limite de 10s
            except requests.exceptions.ReadTimeout:
                    print("Exceeded limit time")
                    container.kill()
                    exit_code = -1
                
            logs = container.logs(stdout=True, stderr=True).decode()
            container.remove()
            
            print("Logs completos:")
            print(logs)
            
            if exit_code != 0:
                print("Error in container", exit_code)

        finally:
            # Limpeza
            #import shutil
            shutil.rmtree(project_path)
    else:
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
        if lang.lower() == "r":
            file_name = "code.r"
        elif lang.lower() == "c smpl" or lang.lower() == "c smplx":
            file_name = "code.c"
        else:
            file_name = "code.py"
        print("file_name:")
        print(file_name)
        host_file_path = os.path.join(tmpdir, file_name)
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
                
                LIBS_DIR = "/home/ubuntu/smpl"
                command = [
                    "bash", "-c",
                    "gcc /workspace/code.c /smpl/*.c -I/smpl -lm -o /workspace/a.out && /workspace/a.out"
                ]

                image="c_runner:latest"
                volumes = {
                    tmpdir: {"bind": "/workspace", "mode": "rw"},
                    LIBS_DIR: {"bind": "/smpl", "mode": "ro"},
                }
            elif lang.lower() == "c smplx":
                LIBS_DIR = "/home/ubuntu/smplx"
                command = [
                    "bash", "-c",
                    "gcc /workspace/code.c /smplx/*.c -I/smplx -lm -o /workspace/a.out && /workspace/a.out"
                ]

                image="c_runner:latest"
                volumes = {
                    tmpdir: {"bind": "/workspace", "mode": "rw"},
                    LIBS_DIR: {"bind": "/smplx", "mode": "ro"},
                }
            else:
                command = ["Rscript", container_file_path]
                image = "r-simmer"
                volumes={tmpdir: {"bind": "/workspace", "mode": "rw"}}
            log_config = LogConfig(type="none")
            container = client.containers.run(
            image,
            command=command,
            volumes=volumes,
            detach=True,
            auto_remove=False,
            mem_limit="512m",
            log_config=log_config
        )
            try:
                exit_code = container.wait(timeout=10)["StatusCode"]  # tempo limite de 10s
            except requests.exceptions.ReadTimeout:
                print("Exceeded limit time")
                container.kill()
                exit_code = -1
            
            logs = container.logs(stdout=True, stderr=True).decode()
            container.remove()
            
            print("Logs completos:")
            print(logs)
            
            if exit_code != 0:
                print("O container terminou com erro:", exit_code)
            

        except docker.errors.ContainerError as e:
            print("Erro no container!")
            print("Saída de erro (stderr):")
            print(e.stderr)
        finally:
            if os.path.exists(host_file_path):
                os.remove(host_file_path)
                print(f"Arquivo {host_file_path} removido.")
            for filename in os.listdir(tmpdir):
                if filename.endswith(".out"):
                    file_path = os.path.join(tmpdir, filename)
                    try:
                        os.remove(file_path)
                        print(f"Executável {file_path} removido.")
                    except Exception as e:
                        print(f"Erro ao remover {file_path}: {e}")
    
    return logs
