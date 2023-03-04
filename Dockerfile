FROM python:3.9.5
USER root

RUN apt-get update
RUN apt-get -y install locales && \
    localedef -f UTF-8 -i ja_JP ja_JP.UTF-8
RUN apt-get install -y vim less

ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL js_JP.UTF-8
ENV TZ JST-9
ENV TERM xterm

RUN mkdir -p /root/mytrade
COPY requirements.txt /root/mytrade
COPY create_table.sql /root/mytrade
COPY create_orders.sql /root/mytrade
COPY alter_table.sql /root/mytrade
COPY Auto-trade.db /root/mytrade
COPY api-key.txt /root/mytrade
COPY .setenv /root/mytrade
COPY auto-start.sh /root/mytrade
WORKDIR /root/mytrade
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install -r requirements.txt

