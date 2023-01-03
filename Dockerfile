FROM python:3.11.1-alpine3.17

ENV WORKDIR /app
WORKDIR $WORKDIR

RUN apk update && apk add cargo

RUN pip install pdm==2.1.3
RUN pdm config python.use_venv False

COPY pyproject.toml .
COPY pdm.lock .

RUN pdm sync --no-self -v

ENV PYTHONPATH "${WORKDIR}/__pypackages__/3.11/lib"
ENV PATH "${WORKDIR}/__pypackages__/3.11/bin:${PATH}"

COPY main.py .
COPY aiocronjob_ui aiocronjob_ui

EXPOSE 8550

CMD ["pdm", "run", "flet", "--web", "--port", "8550", "main.py"]
