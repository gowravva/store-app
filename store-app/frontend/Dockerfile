# ---- Store frontend: React + Vite, served as static files by nginx ----

# Stage 1: build the static site.
FROM node:20-alpine AS build
WORKDIR /app

# The browser (not the container) calls the Store backend, so this URL must be
# reachable from the user's machine. It is baked in at build time.
#   - local docker:  http://localhost:8001
#   - production:     http://<your-server-ip>:8001
ARG VITE_API_URL=http://localhost:8001
ENV VITE_API_URL=$VITE_API_URL

COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: serve the built files with a tiny nginx image.
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
