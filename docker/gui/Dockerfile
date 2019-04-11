FROM node:8

RUN mkdir /app
WORKDIR /app
ADD ClientCampusIdP /app

RUN npm install

CMD [ "/usr/local/bin/npm", "start" ]
