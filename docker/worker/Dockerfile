FROM python:alpine

RUN mkdir -p /usr/local/src
RUN wget https://shibboleth.net/downloads/identity-provider/3.3.2/shibboleth-identity-provider-3.3.2.tar.gz
RUN tar zxvf shibboleth-identity-provider-3.3.2.tar.gz -C /usr/local/src
RUN rm shibboleth-identity-provider-3.3.2.tar.gz

RUN apk add ansible bash openjdk8 openssl  

ENV JAVA_HOME=/usr/lib/jvm/java-1.8-openjdk

RUN mkdir -p /opt/ansible-shibboleth/inventories
RUN mkdir -p /opt/ansible-shibboleth/scripts
RUN mkdir -p /opt/ansible-shibboleth/worker/logs

ADD ansible-shibboleth /opt/ansible-shibboleth
ADD ansible-shibboleth-inventories /opt/ansible-shibboleth/inventories
ADD ans-idpcloud-utility /opt/ansible-shibboleth/scripts
ADD campusidpScripts /opt/ansible-shibboleth/worker

WORKDIR /opt/ansible-shibboleth/worker

RUN pip install -r requirements.txt

CMD ["python", "/opt/ansible-shibboleth/worker/worker.py"]
