FROM node:22.8.0-alpine

WORKDIR /app

COPY . /app/

RUN npm install
RUN npm run build

EXPOSE 8080
CMD ["npm", "run", "preview"]