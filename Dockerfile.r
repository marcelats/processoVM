FROM rocker/r-ver:4.3.1  # ou a versão que você precisar
WORKDIR /workspace
RUN R -e "install.packages('simmer', repos='https://cloud.r-project.org')"
CMD ["Rscript"]
