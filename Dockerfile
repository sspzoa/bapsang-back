FROM python:3.12.5-alpine

WORKDIR /code
COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

ARG OPENAI_API_KEY

ENV OPENAI_API_KEY=${OPENAI_API_KEY}

CMD ["fastapi", "run", "app/main.py", "--port", "8000"]