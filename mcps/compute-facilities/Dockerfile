FROM continuumio/miniconda3

EXPOSE 8000/tcp

WORKDIR /science-mcps/mcps/compute-facilities

COPY mcps/compute-facilities/alcf_server.py alcf_server.py
COPY mcps/compute-facilities/nersc_server.py nersc_server.py
COPY mcps/compute-facilities/requirements.txt requirements.txt

RUN conda create -y -n science-mcps python=3.11 && \
    conda run -n science-mcps pip install -r requirements.txt

COPY mcps/compute-facilities/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]
