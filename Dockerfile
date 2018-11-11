FROM jupyter/base-notebook
VOLUME /app
COPY --chown=jovyan:1000 ./jupyter /app
COPY requirements.txt /tmp
WORKDIR /app
EXPOSE 8888:8888
RUN pip install -r /tmp/requirements.txt && \
    fix-permissions $CONDA_USER && \
    fix-permissions /home/$NB_USER
ENTRYPOINT ["jupyter", "lab"]