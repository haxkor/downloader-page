FROM alpine

RUN apk upgrade && apk add pip tini python3
RUN pip install -r requirements.txt

COPY src /usr/bin/downloader-page

ENTRYPOINT ["/sbin/tini", "--", "python3", "/usr/bin/downloader-page/app.py"]
