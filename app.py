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
            #exit_code = container.wait()
            #logs = container.logs(stdout=True, stderr=True)
            #print("Exit code:", exit_code)
            #print(logs.decode("utf-8"))
            #container.remove()
            # Depois, roda a classe principal
            run_cmd = [
                "java",
                "-cp", "/workspace/out:/workspace/javasim-2.3.jar",
                "com.javasim.teste.basic.Main"
            ]
            output = client.containers.run(
                "java-17-slim",
                command=run_cmd,
                volumes = {
                    project_path: {"bind": "/workspace", "mode": "rw"},
                },
                working_dir="/workspace",
                detach=True,
                auto_remove=False
            )
            result = container.wait()   # retorna dict com {"StatusCode": ...}
            exit_code = result["StatusCode"]
            # Captura os logs (stdout + stderr)
            logs = container.logs(stdout=True, stderr=True).decode("utf-8")
            # Remove o container depois de pegar os logs
            container.remove()
            return {"status": "finished", "output": output.decode("utf-8"),"logs": logs}
        finally:
            # Limpeza
            #import shutil
            shutil.rmtree(project_path)
    else:
#with tempfile.TemporaryDirectory() as tmpdir:
    # Gera nome único para o arquivo
        contents = await code.read()
        print("contents:")
        print(contents[:100])
        tmpdir = os.path.abspath("/tmp/docker_exec")
        #os.makedirs(tmpdir, exist_ok=True)
        #os.chmod(tmpdir, 0o777)
        #print("tmpdir:")
        #print(tmpdir)
        if lang.lower() == "python":
            file_name = "code.py"
        elif lang.lower() == "c smpl":
            file_name = "code.c"
        else:
            file_name = "code.r"
        host_file_path = os.path.join(tmpdir, file_name)
        #print("file_name:")
        #print(file_name)
        #host_file_path = os.path.join(tmpdir, "code.py")
        #print("host_file_path:")
        #print(host_file_path)
        # Grava o código do cliente
        #with open(host_file_path, "wb") as f:
        #    f.write(contents)
        #    print("f:")
        #    print(f)
        #with open(host_file_path, "rb") as f:
        #    print("dentro de f:")
        #    print(f.read(100))
        #print("Arquivos em tmpdir:", os.listdir(tmpdir))
        #for filename in os.listdir(tmpdir):
        #    file_path = os.path.join(tmpdir, filename)
            # verifica se é um arquivo regular (não diretório)
        #    if os.path.isfile(file_path):
        #        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        #            content = f.read(100)  # lê os primeiros 100 caracteres
        #        print(f"Arquivo: {filename}")
        #        print(f"Conteúdo (100 primeiros caracteres):\n{content}")
        #        print("-" * 40)
        container_file_path = f"/workspace/{file_name}"
        #print("container_file_path")
        #print(container_file_path)
        try:
            # Cria o container (não auto_remove)]
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
            #output = client.containers.run(
            #    image,
            #    command,
            #    volumes,
            #    detach=False,  # bloqueia até terminar
            #    auto_remove=True
            #)
            #print(output.decode())
            # Agora você pode executar comandos dentro do container
            #exit_code, output = container.exec_run("ls -l /workspace")
            #print(output.decode())
            #exit_code, output = container.exec_run(f"cat workspace/code.py")
            #print(output.decode())
            #container.exec_run("python /workspace/code.py")
            # Depois finalize o container
            #logs = container.decode("utf-8")
            #container.stop()
            #container.remove()
        finally:
        # Apaga o arquivo enviado pelo cliente para não encher a VM
            if os.path.exists(host_file_path):
                os.remove(host_file_path)
                print(f"Arquivo {host_file_path} removido.")
