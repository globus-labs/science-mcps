FROM continuumio/miniconda3

EXPOSE 8000/tcp

WORKDIR /science-mcps/mcps/diaspora

COPY mcps/diaspora/diaspora_server.py diaspora_server.py
COPY mcps/diaspora/requirements.txt requirements.txt

RUN conda create -y -n science-mcps python=3.11 && \
    conda run -n science-mcps pip install -r requirements.txt

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "science-mcps", "python", "diaspora_server.py"]
