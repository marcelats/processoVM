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


CMD ["python", "app.py"]

