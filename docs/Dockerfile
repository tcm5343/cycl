FROM python:3.11-slim

WORKDIR /work

COPY requirements-docs.txt requirements-docs.txt 
COPY requirements-docs.txt requirements-docs.txt 
RUN pip install -r requirements-docs.txt -e .

ENV PYTHONPATH="${PYTHONPATH}:/work/src"
