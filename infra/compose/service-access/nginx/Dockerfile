FROM nginx:mainline

COPY default.conf /etc/nginx/conf.d/default.conf
COPY generate-self-signed-cert.sh /docker-entrypoint.d/20-generate-self-signed-cert.sh
RUN chmod +x /docker-entrypoint.d/20-generate-self-signed-cert.sh
