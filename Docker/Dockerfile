FROM python:3.12.3-slim

WORKDIR /app

COPY requirements.txt .

RUN python3 -m pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD [ "python3", "server.py" ]