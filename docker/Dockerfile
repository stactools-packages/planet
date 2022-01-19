FROM continuumio/miniconda3

RUN conda update conda && conda install pip

COPY environment.yml /tmp/environment.yml
RUN conda env update -f /tmp/environment.yml -n base && rm /tmp/environment.yml

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY . /tmp/stactools-planet
RUN cd /tmp/stactools-planet && pip install . && rm -rf /tmp/stactools-planet

ENTRYPOINT [ "python", "-m", "stactools.cli" ]
