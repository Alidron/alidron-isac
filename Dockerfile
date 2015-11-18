FROM alidron/alidron-base-python:2
MAINTAINER Axel Voitier <axel.voitier@gmail.com>

#RUN pip install prospector

COPY . /usr/src/alidron-isac/isac
#WORKDIR /usr/src/alidron-isac

#ENV PYTHONPATH=/usr/src/alidron-isac

CMD ["python", "-m", "isac_cmd"]
