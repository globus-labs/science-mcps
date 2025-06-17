FROM continuumio/miniconda3

RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 8000/tcp

WORKDIR /science-mcps/mcps/compute_facilities

COPY mcps/compute_facilities/alcf_server.py alcf_server.py
COPY mcps/compute_facilities/nersc_server.py nersc_server.py
COPY mcps/compute_facilities/requirements.txt requirements.txt

RUN conda create -y -n science-mcps python=3.11 && \
    conda run -n science-mcps pip install -r requirements.txt

COPY mcps/compute_facilities/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]
