import docker
client = docker.from_env()

tmpdir = "/home/ubuntu/docker_exec"
container = client.containers.run(
    "python:3.11-slim",
    command=["ls", "-l", "/workspace"],
    volumes={tmpdir: {'bind': '/workspace', 'mode': 'rw'}},
    detach=False,
    auto_remove=True
)
print(container.decode())
