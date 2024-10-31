FROM python:3.12.3-slim

WORKDIR /app

COPY . .

RUN python3 -m pip install -r ./requirements.txt

EXPOSE 8000

CMD [ "python3","server.py"]