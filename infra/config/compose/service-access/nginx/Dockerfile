FROM nginx:mainline-alpine

RUN apk add --no-cache libcap openssl \
    && sed -i 's#pid[[:space:]]\+/run/nginx.pid;#pid /tmp/nginx.pid;#' /etc/nginx/nginx.conf \
    && setcap 'cap_net_bind_service=+ep' /usr/sbin/nginx \
    && mkdir -p /etc/nginx/tls \
    && chown -R nginx:nginx /var/cache/nginx /var/run /var/log/nginx /etc/nginx/conf.d /etc/nginx/tls

COPY --chown=nginx:nginx default.conf /etc/nginx/conf.d/default.conf
COPY --chown=nginx:nginx generate-self-signed-cert.sh /docker-entrypoint.d/20-generate-self-signed-cert.sh
RUN chmod +x /docker-entrypoint.d/20-generate-self-signed-cert.sh

USER nginx
