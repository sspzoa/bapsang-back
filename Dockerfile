FROM python:3.12.5-alpine

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

RUN mkdir /code/uploads

ARG OPENAI_API_KEY
ENV OPENAI_API_KEY=${OPENAI_API_KEY}

RUN chmod 777 /code/uploads

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]