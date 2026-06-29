FROM debezium/connect:latest

USER root
RUN mkdir -p /kafka/connect/confluent-avro

# Copy Avro converter jars from local folder
COPY jars/confluent-avro/*.jar /kafka/connect/confluent-avro/

USER kafka
