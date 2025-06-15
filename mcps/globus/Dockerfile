FROM continuumio/miniconda3

EXPOSE 8000/tcp

WORKDIR /science-mcps/mcps/globus

COPY mcps/globus/compute_server.py compute_server.py
COPY mcps/globus/transfer_server.py transfer_server.py
COPY mcps/globus/requirements.txt requirements.txt

RUN conda create -y -n science-mcps python=3.11 && \
    conda run -n science-mcps pip install -r requirements.txt

COPY mcps/globus/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]