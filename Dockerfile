FROM alpine:3.6
LABEL maintainer="Napat Chuangchunsong <https://github.com/napat>"
LABEL Name="Cerv2.0"
LABEL Version="2.0"

WORKDIR /opt/certbot
ENV PATH /opt/certbot/venv/bin:$PATH
ENV CERTBOT_RELEASE "0.32.0"

#RUN apk -U upgrade && apk add curl
#RUN curl -L https://github.com/certbot/certbot/archive/v${CERTBOT_RELEASE}.tar.gz -o /opt/master.tar.gz

RUN export BUILD_DEPS="curl \
                build-base \
                libffi-dev \
                linux-headers \
                py-pip \
                python-dev" \
    && apk -U upgrade \
    && apk add dialog \
                python \
                openssl-dev \
		augeas-libs \
                ${BUILD_DEPS} \

    && pip --no-cache-dir install virtualenv
RUN curl -L https://github.com/certbot/certbot/archive/v${CERTBOT_RELEASE}.tar.gz | tar -xz -C /opt/certbot \
    && mv /opt/certbot/certbot-${CERTBOT_RELEASE} /opt/certbot/src \
    && virtualenv --no-site-packages -p python2 /opt/certbot/venv
RUN /opt/certbot/venv/bin/pip install \
        -e /opt/certbot/src/acme \
        -e /opt/certbot/src \
        -e /opt/certbot/src/certbot-apache \
        -e /opt/certbot/src/certbot-nginx \
        -e /opt/certbot/src/certbot-dns-cloudflare \
        -e /opt/certbot/src/certbot-dns-google \
        -e /opt/certbot/src/certbot-dns-route53 \
    && /opt/certbot/venv/bin/pip install schedule redis \
    && apk del ${BUILD_DEPS} \
    && rm -rf /var/cache/apk/*


VOLUME ["/etc/letsencrypt", "/usr/src/python"]

COPY main.py /usr/src/
COPY example /usr/src/python/

CMD [ "python", "-u", "/usr/src/main.py" ]
