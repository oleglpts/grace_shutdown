FROM alpine:3.12

WORKDIR /app
RUN adduser -h /home/receiver -s sh -D receiver
# install python & pip
ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip && pip3 install --no-cache --upgrade pip setuptools
# install packages for requirements
RUN apk add gcc python3-dev musl-dev
# install requirements
COPY requirements.txt /app/requirements.txt
RUN pip3 install -r requirements.txt
COPY . /app
RUN chmod 755 /app/receiver.py && chown -R receiver:receiver /app
USER receiver
CMD ["/app/receiver.py"]
