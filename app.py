from fastapi import FastAPI, Request
import docker

app = FastAPI()
client = docker.from_env()

@app.post("/execute")
async def execute(request: Request):
    data = await request.json()
    image = data.get("image", "python:3.11")
    command = data.get("command", "echo hello")

    container = client.containers.run(
        image,
        command,
        detach=True,
        remove=True
    )

    return {"status": "started", "id": container.short_id}
