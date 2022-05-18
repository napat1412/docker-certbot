FROM alpine:3.14
LABEL maintainer="Napat Chuangchunsong <https://github.com/napat1412>"
LABEL Name="Certbot"
LABEL Version="1.27.0"

WORKDIR /opt/certbot

#RUN apk -U upgrade
RUN apk add --update --no-cache linux-headers curl python3 py-pip

### alpine 3.14.6 install certbot-dns-google
RUN apk add --update --no-cache gcc musl-dev python3-dev libffi-dev openssl-dev cargo augeas-libs
RUN pip3 --no-cache-dir install certbot certbot-dns-google certbot-dns-route53

### Install python2 for run main.py
RUN apk add --update --no-cache python2
RUN curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py && python get-pip.py
RUN pip2 install redis
RUN pip2 cache purge

### Install SSH Server
RUN apk add --update --no-cache openssh 
#RUN echo 'PasswordAuthentication yes' >> /etc/ssh/sshd_config
RUN adduser -h /home/certbot -s /bin/sh -D certbot
#RUN echo -n 'certbot:certbot' | chpasswd

VOLUME ["/etc/letsencrypt", "/usr/src/python"]

COPY main.py /usr/src/
#COPY example /usr/src/python/

CMD [ "python", "-u", "/usr/src/main.py" ]
