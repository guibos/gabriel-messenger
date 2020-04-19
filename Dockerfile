FROM ubuntu:latest
RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install python3.8 python3-pip python3.8-dev git pandoc -y

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

#RUN git clone https://github.com/guibos/gabriel-messenger.git /opt/gabriel-messenger
COPY ./ /opt/gabriel-messenger
WORKDIR /opt/gabriel-messenger

RUN pip3 install pipenv
RUN pipenv install

ENTRYPOINT ["pipenv", "run", "run"]
