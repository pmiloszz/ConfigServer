# Frontend image: NGINX serving static assets and proxying API calls
# to the backend Service inside Kubernetes.

FROM nginx:1.27-alpine

# Copy the prebuilt static assets from the repo.
COPY static/ /usr/share/nginx/html/static/

# Replace default server config.
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

