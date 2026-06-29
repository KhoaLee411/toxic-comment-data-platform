FROM debezium/connect:latest

USER root
RUN microdnf -y install tar gzip && \
    curl -L -o /tmp/confluent-hub-client.tar.gz http://client.hub.confluent.io/confluent-hub-client-latest.tar.gz && \
    mkdir -p /opt/confluent-hub && \
    tar -xzf /tmp/confluent-hub-client.tar.gz -C /opt/confluent-hub && \
    /opt/confluent-hub/bin/confluent-hub install --no-prompt confluentinc/kafka-connect-avro-converter:7.5.0 --component-dir /kafka/connect && \
    rm /tmp/confluent-hub-client.tar.gz

USER kafka
