FROM python:3.11

WORKDIR /bot

COPY ./requirements.txt /bot
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get -y update
RUN apt-get -y upgrade

COPY ./src /bot/src

CMD ["python", "src/bot.py"]
