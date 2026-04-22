FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm i -g pnpm && pnpm install
COPY . .
EXPOSE 3000
CMD ["pnpm", "run", "dev"]
