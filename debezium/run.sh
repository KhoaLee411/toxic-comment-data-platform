#!/bin/bash
set -euo pipefail

# Tìm thư mục gốc dự án để load .env (đảm bảo script chạy đúng dù bạn ở thư mục nào)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -f "$PROJECT_ROOT/.env" ]]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

KAFKA_CONNECT_URL=${KAFKA_CONNECT_URL:-"http://localhost:8083"}

usage() {
    echo "Usage: ./run.sh <command> <arguments>"
    echo "Available commands:"
    echo " register_connector          register a new Kafka connector"
    echo " list_connectors             list all active connectors"
    echo " status_connector            get status of a connector"
    echo " delete_connector            delete a connector"
    echo "Available arguments:"
    echo " [connector config path]     path to connector config, for command register_connector only"
}

if [[ $# -eq 0 ]]; then
    echo "Missing command"
    usage
    exit 1
fi

cmd=$1

case $cmd in
    register_connector)
        if [[ -z "${2:-}" ]]; then
            echo "Missing connector config path"
            usage
            exit 1
        fi
        
        config_path="$2"
        if [[ ! -f "$config_path" ]]; then
            echo "Error: Config file '$config_path' not found!"
            exit 1
        fi
        
        echo "Registering connector from $config_path"
        envsubst < "$config_path" | curl -i -X POST -H "Accept:application/json" -H "Content-Type: application/json" \
            "${KAFKA_CONNECT_URL}/connectors" -d @-
        echo
        ;;
    list_connectors)
        curl -s "${KAFKA_CONNECT_URL}/connectors"
        echo
        ;;
    status_connector)
        if [[ -z "${2:-}" ]]; then
            echo "Missing connector name"
            exit 1
        fi
        curl -s "${KAFKA_CONNECT_URL}/connectors/$2/status"
        echo
        ;;
    delete_connector)
        if [[ -z "${2:-}" ]]; then
            echo "Missing connector name"
            exit 1
        fi
        curl -i -X DELETE "${KAFKA_CONNECT_URL}/connectors/$2"
        echo
        ;;
    *)
        echo "Unknown command: $cmd"
        usage
        exit 1
        ;;
esac
