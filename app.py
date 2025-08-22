import docker, tempfile, os

client = docker.from_env()

with tempfile.TemporaryDirectory() as tmpdir:
    host_file_path = os.path.join(tmpdir, "code.py")
    with open(host_file_path, "w") as f:
        f.write("print('hello from container')\n")

    container_file_path = "/workspace/code.py"

    container = client.containers.run(
        "python:3.11-slim",
        command=["python", container_file_path],
        volumes={tmpdir: {"bind": "/workspace", "mode": "rw"}},
        detach=True,
        auto_remove=False
    )

    container.wait()
    logs = container.logs()
    print(logs.decode())
    container.remove()
