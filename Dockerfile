
FROM python:3.10-alpine as base
FROM base as builder

COPY requirements.txt requirements.txt
RUN apk update
RUN apk add --virtual .pynacl_deps build-base python3-dev libffi-dev
RUN pip install --user -r requirements.txt

FROM base

WORKDIR /src

RUN apk add ffmpeg
COPY --from=builder /root/.local /root/.local
COPY ./record ./record
COPY ./.env .

ENV PATH=/root/.local:$PATH

CMD [ "python", "-m", "record" ]
