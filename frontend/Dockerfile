FROM node:22-slim

WORKDIR /app

COPY frontend/package.json /app/package.json
RUN npm install

COPY frontend/index.html frontend/tsconfig.json frontend/vite.config.ts /app/
COPY frontend/src /app/src

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
