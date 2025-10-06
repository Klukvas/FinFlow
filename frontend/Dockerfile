FROM nginx:alpine

# Copy built frontend assets
COPY dist/ /usr/share/nginx/html/

# Default Nginx config serves static files
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]


