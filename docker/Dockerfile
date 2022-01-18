FROM continuumio/miniconda3

RUN conda update conda && conda install pip

COPY environment.yml /tmp/environment.yml
RUN conda env update -f /tmp/environment.yml -n base && rm /tmp/environment.yml

COPY . /tmp/stactools-planet
RUN pip install -r /tmp/stactools-planet/requirements-dev.txt
RUN cd /tmp/stactools-planet && pip install . && rm -rf /tmp/stactools-planet

ENTRYPOINT [ "python", "-m", "stactools.cli" ]
