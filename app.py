import docker
import os

app = docker.from_env()  # corrigido de 'app'

tmpdir = os.path.abspath("/home/ubuntu/docker_exec")

output = app.containers.run(
    "python:3.11-slim",
    command=["ls", "-l", "/workspace"],
    volumes={tmpdir: {'bind': '/workspace', 'mode': 'rw'}},
    detach=False,
    auto_remove=True
)

print(output.decode())
