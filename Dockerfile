FROM pypy:3.10-slim

WORKDIR /code

RUN apt-get update && apt-get install -y \
    gcc \
    libc-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /code/requirements.txt

COPY ./app /code/app

ARG OPENAI_API_KEY
ARG ACCESS_TOKEN

ENV OPENAI_API_KEY=${OPENAI_API_KEY}
ENV ACCESS_TOKEN=${ACCESS_TOKEN}

RUN adduser --disabled-password --gecos '' appuser
USER appuser

CMD ["pypy", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]