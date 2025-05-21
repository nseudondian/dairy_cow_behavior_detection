FROM node:18
WORKDIR /app
RUN npm install -g npm@10.2.5
COPY . /app/
RUN npm install
EXPOSE 3000
#RUN npm run build
CMD ["npm", "run", "dev"]