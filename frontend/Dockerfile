FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.sh /docker-entrypoint.d/30-cyron-env.sh
RUN chmod +x /docker-entrypoint.d/30-cyron-env.sh

# public/ holds everything served from the web root (env.js, favicons, the
# Cyron logo); index.html and src/ are copied alongside it so the root-
# relative paths in index.html ("/src/...", "/cyron-mark.png") resolve.
COPY public/ /usr/share/nginx/html/
COPY index.html /usr/share/nginx/html/index.html
COPY src/ /usr/share/nginx/html/src/

EXPOSE 80
