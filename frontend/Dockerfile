# Static frontend served by nginx, which also proxies /api/ to the backend
FROM nginx:1.27-alpine

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY interface /usr/share/nginx/html
# Same-origin API path instead of http://<host>:5000
COPY docker/config.js /usr/share/nginx/html/config.js

EXPOSE 80
