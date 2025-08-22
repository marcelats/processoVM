from fastapi import FastAPI, Request, UploadFile, File, Form
import docker
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
    logging.basicConfig(level=logging.INFO)
    contents = await code.read()

    with tempfile.TemporaryDirectory() as tmpdir:
        if lang == 'Python':
            tmpdir2 = "/tmp/docker_exec"
            os.makedirs(tmpdir2, exist_ok=True)
            os.chmod(tmpdir2, 0o777)

            file_path = os.path.join(tmpdir2, 'code.py')
            with open(file_path, 'wb') as f:
                f.write(contents)

            container = client.containers.run(
                "python:3.11",              # imagem base
                command=f"python /tmp/docker_exec/{os.path.basename(file_path)}",
                volumes={tmpdir: {"bind": "/tmp", "mode": "rw"}},  # monta arquivo
                detach=True,
                auto_remove=False            # o container é removido após terminar
            )

            result = container.wait(timeout=10)
            logs = container.logs()  # agora funciona
            container.remove()
            stdout = logs.decode()
            
        elif lang == 'Java':
            jar_path = os.path.join(os.path.dirname(__file__), 'javasim-2.3.jar')
            if not os.path.exists(jar_path):
                raise FileNotFoundError(f"Arquivo .jar não encontrado: {jar_path}")
            else:
                logging.info(f"JAR localizado: {jar_path}")

            zip_path = os.path.join(tmpdir, 'codigo.zip')
            contents.save(zip_path)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
            java_files = glob.glob(os.path.join(tmpdir, "*.java"))    
            if not java_files:
                logging.error("Nenhum arquivo .java encontrado!")
            else:
                logging.info("Compilando arquivos: %s", java_files)

                compile_cmd = ['javac', '-cp', jar_path] + java_files
                compile_proc = subprocess.run(compile_cmd, capture_output=True, text=True)

                if compile_proc.returncode != 0:
                    logging.error("Erro na compilação:")
                    logging.error("STDERR:\n%s", compile_proc.stderr.strip())
                    logging.error("STDOUT:\n%s", compile_proc.stdout.strip())
                else:
                    logging.info("Compilação bem-sucedida!")

        # Executar a Main
                    run_cmd = ['java', '-cp', f'{tmpdir}:{jar_path}', 'Main']
                    proc = subprocess.run(run_cmd, capture_output=True, text=True)

                    logging.info("Saída da execução:")
                    logging.info("STDOUT:\n%s", proc.stdout.strip())
                    logging.info("STDERR:\n%s", proc.stderr.strip())
                    
        elif lang == 'C SMPL':
            file_path = os.path.join(tmpdir, 'code.c')
            with open(file_path, 'wb') as f:
                f.write(contents)

            # Ajuste para onde está instalada sua biblioteca SMPL
            smpl_include_path = '/usr/local/include'  # Ou onde estiver o smpl.h
            smpl_lib_path = '/usr/local/lib'          # Ou onde estiver libsmpl.a/.so

            output_binary = os.path.join(tmpdir, 'code_exec')

            compile_cmd = [
                'gcc',
                file_path,
                '-I', smpl_include_path,
                '-L', smpl_lib_path,
                '-lsmpl',
                '-o', output_binary
            ]

            compile_proc = subprocess.run(compile_cmd, capture_output=True, text=True)

            if compile_proc.returncode != 0:
                logging.error("Erro na compilação C SMPL:")
                logging.error("STDERR:\n%s", compile_proc.stderr.strip())
                logging.error("STDOUT:\n%s", compile_proc.stdout.strip())
                return jsonify({
                    'stdout': compile_proc.stdout,
                    'stderr': compile_proc.stderr,
                    'returncode': compile_proc.returncode
                })

            # Executar o binário
            proc = subprocess.run([output_binary], capture_output=True, text=True, timeout=10)
        
        else:
            file_path = os.path.join(tmpdir, 'code.R')
            with open(file_path, 'wb') as f:
                f.write(contents)
            cmd = ['Rscript', file_path]

            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        return {
            "status": "finished",
            "returncode": result.get("StatusCode", -1),
            "output": stdout
        }
