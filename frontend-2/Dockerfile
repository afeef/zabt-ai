FROM node:20-alpine

WORKDIR /app

# Copy lockfile as well for npm ci
COPY package*.json ./

RUN npm ci

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
