FROM ubuntu:18.04
RUN cat /etc/os-release

RUN apt update
RUN apt install -y python3-dev python3-pip python3-venv python3-wheel git graphviz libgraphviz-dev pkg-config
RUN pip3 -q install pip  wheel setuptools --upgrade
RUN python3 --version
RUN echo 'alias python3.6=python3' >> ~/.bashrc
RUN alias python3.6=python3
RUN python3.6 --version

RUN mkdir auto
ADD src/ ./auto/src/
ADD README.md ./auto/
ADD setup.py ./auto/
ADD Makefile ./auto/
# add python requirements.
ADD requirements.txt ./auto/
# Add iql-viz
ADD iql-viz/ ./iql-viz

WORKDIR auto
RUN ls
RUN make install

CMD make notebook
