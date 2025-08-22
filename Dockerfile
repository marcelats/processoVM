FROM python:3.11-slim
RUN pip install simpy
WORKDIR /workspace

FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    default-jdk \
    r-base \
    r-base-core \
    && apt-get clean


RUN pip install flask simpy
RUN pip install requests

# Instala a biblioteca 'simmer' do R
RUN R -e "install.packages('simmer', repos='https://cloud.r-project.org')"

FROM ubuntu:22.04  # ou outra base

# Instala R
RUN apt-get update && apt-get install -y r-base

# Instala Java (se precisar também)
RUN apt-get install -y openjdk-11-jdk

# Instala C (build tools)
RUN apt-get install -y build-essential

# Instala Python
RUN apt-get install -y python3 python3-pip

# Limpeza de cache
RUN apt-get clean && rm -rf /var/lib/apt/lists/*


CMD ["python", "app.py"]

