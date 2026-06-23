FROM nginx:mainline-alpine

RUN apk add --no-cache libcap \
    && setcap 'cap_net_bind_service=+ep' /usr/sbin/nginx \
    && chown -R nginx:nginx /var/cache/nginx /var/run /var/log/nginx /usr/share/nginx/html

COPY --chown=nginx:nginx index.html /usr/share/nginx/html/index.html

USER nginx
