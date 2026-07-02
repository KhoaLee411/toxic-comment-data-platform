FROM quay.io/debezium/connect:2.7.0.Final

USER root
RUN mkdir -p /kafka/connect/confluent-avro

# Copy Avro converter jars from local folder
COPY jars/confluent-avro/*.jar /kafka/connect/confluent-avro/

USER kafka
