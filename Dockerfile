FROM jupyter/minimal-notebook
# Check OS version
RUN cat /etc/os-release

# Get source into image.
ADD src/ ./src/
ADD README.md .
ADD setup.py .
ADD Makefile .
# add python requirements.
ADD requirements.txt .
# Add iql-viz
ADD iql-viz/ ./iql-viz

USER root
RUN python -m pip install -r requirements.txt
RUN python -m pip install .

# Ensure the latest version of configurable-http-proxy. Addresses a
# vulnerability from upstream images.
RUN npm install -g configurable-http-proxy@latest --save

USER $NB_USER
ADD tests/ ./tests
RUN python -m pytest tests/ -vvv
CMD ["start-notebook.sh", "--NotebookApp.custom_display_url=http://localhost:8888"]
