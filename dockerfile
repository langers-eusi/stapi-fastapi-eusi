FROM python:3.12

EXPOSE 8000

WORKDIR /app

# Install dependencies
COPY . .

RUN pip3 install poetry 
RUN poetry config virtualenvs.create false
RUN poetry install --with dev

# Run your app

CMD ["gunicorn","application:app", "--chdir","eusi", "--bind","0.0.0.0:80","--workers","4","--worker-class","uvicorn.workers.UvicornWorker","--timeout","120"]

