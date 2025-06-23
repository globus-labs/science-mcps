FROM continuumio/miniconda3

EXPOSE 8000/tcp

WORKDIR /science-mcps/mcps/diaspora

COPY mcps/diaspora/diaspora_server.py diaspora_server.py
COPY mcps/diaspora/requirements.txt requirements.txt

RUN conda create -y -n science-mcps python=3.11 && \
    conda run -n science-mcps pip install -r requirements.txt

COPY mcps/diaspora/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]
