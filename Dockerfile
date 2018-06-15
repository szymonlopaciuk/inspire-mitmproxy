FROM mitmproxy/mitmproxy:3.0.3
EXPOSE 8081
COPY ./ /code
COPY ./mitmproxy-ca.pem /root/.mitmproxy/mitmproxy-ca.pem
RUN apk add --update py3-pip python3-dev gcc musl-dev
WORKDIR /code
RUN pip3 install ".[all]"
CMD mitmweb -s /code/entrypoint.py --web-iface 0.0.0.0 --ssl-insecure
