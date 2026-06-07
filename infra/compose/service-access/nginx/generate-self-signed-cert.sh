#!/usr/bin/env sh
set -eu

certificate_dir="${TSW_SERVICE_ACCESS_TLS_DIR:-/etc/nginx/tls}"
certificate_file="${certificate_dir}/vaultwarden.crt"
key_file="${certificate_dir}/vaultwarden.key"
certificate_subject="${TSW_SERVICE_ACCESS_TLS_SUBJECT:-/CN=localhost}"
subject_alt_names="${TSW_SERVICE_ACCESS_TLS_SAN:-DNS:localhost,IP:127.0.0.1}"

if [ -s "$certificate_file" ] && [ -s "$key_file" ]; then
  exit 0
fi

mkdir -p "$certificate_dir"
umask 077

openssl req \
  -x509 \
  -nodes \
  -newkey rsa:2048 \
  -days "${TSW_SERVICE_ACCESS_TLS_DAYS:-365}" \
  -subj "$certificate_subject" \
  -addext "subjectAltName=${subject_alt_names}" \
  -keyout "$key_file" \
  -out "$certificate_file"
