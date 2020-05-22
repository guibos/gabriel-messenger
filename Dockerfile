FROM ubuntu:latest

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -y python3.8 python3-pip python3.8-dev git pandoc

# Only necessary with pyppeteer. Services aka WhatsApp Web
RUN apt-get install -y gconf-service libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxss1 libxtst6 libappindicator1 libnss3 libasound2 libatk1.0-0 libc6 ca-certificates fonts-liberation lsb-release xdg-utils wget

RUN rm -rf /var/lib/apt/lists/*
RUN apt-get -qyy clean

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

RUN pip3 install pipenv

RUN useradd gabriel --shell /bin/bash --create-home

RUN mkdir /opt/gabriel-messenger
RUN chown gabriel /opt/gabriel-messenger

USER gabriel

RUN git clone https://github.com/guibos/gabriel-messenger.git /opt/gabriel-messenger
WORKDIR /opt/gabriel-messenger

RUN pipenv install

CMD ["pipenv", "run", "run"]
