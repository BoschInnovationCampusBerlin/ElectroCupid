# Stage 1: Build the frontend with pnpm
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json pnpm-lock.yaml ./frontend/
WORKDIR /app/frontend
RUN npm install -g pnpm && pnpm install
COPY . .
RUN pnpm build

# Stage 2: Serve with nginx
FROM nginx:alpine
COPY --from=builder /app/frontend/dist /usr/share/nginx/html
# Optional: Copy a custom nginx config if needed
# COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"] 