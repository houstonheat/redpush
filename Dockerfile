FROM comptel/docker-alpine-python:alpine3.7-3.6

ARG DESTDIR="/opt/redpush"

ADD setup.py ${DESTDIR}/
ADD redpush ${DESTDIR}/redpush/

RUN apk add --no-cache build-base \
    && pip install -e ${DESTDIR}

ENTRYPOINT ["redpush"]