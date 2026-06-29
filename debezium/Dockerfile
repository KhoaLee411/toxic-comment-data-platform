FROM debezium/connect:latest

USER root
RUN microdnf install -y unzip zip && microdnf clean all

USER kafka
RUN mkdir -p /kafka/connect/confluent-avro && \
    curl -sSL -o /tmp/confluent-avro.zip https://d1i4a15mxbxib1.cloudfront.net/api/plugins/confluentinc/kafka-connect-avro-converter/versions/7.5.0/confluentinc-kafka-connect-avro-converter-7.5.0.zip && \
    unzip /tmp/confluent-avro.zip -d /tmp/ && \
    cp /tmp/confluentinc-kafka-connect-avro-converter-*/lib/*.jar /kafka/connect/confluent-avro/ && \
    rm -rf /tmp/confluent-avro.zip /tmp/confluentinc-kafka-connect-avro-converter-*
