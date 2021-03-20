ARG PYVER
FROM ${PYVER}

WORKDIR /code

COPY README.rst setup.py requirements.txt /code/
COPY rest_witchcraft/__version__.py /code/rest_witchcraft/

RUN apt update && \
 apt install -y postgresql-client && \
 pip install -r requirements.txt
