FROM ubuntu:18.04
RUN cat /etc/os-release

RUN apt update
RUN apt install -y python3-dev python3-pip python3-venv python3-wheel git
RUN pip3 -q install pip  wheel setuptools --upgrade
RUN python3 --version
RUN echo 'alias python3.6=python3' >> ~/.bashrc
RUN alias python3.6=python3
RUN python3.6 --version
ADD Makefile .
# add python requirements.
ADD requirements.txt .
# Add some product networks. This requires the sum-product network to exist. See
# Makefile (make docker).
ADD sum-product-dsl/ ./sum-product-dsl/
# Add iql-viz
ADD iql-viz/ ./iql-viz
RUN make install

CMD make notebook
