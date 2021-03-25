FROM node:12.21.0

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt-get update && apt-get install yarn -y

COPY . /server

WORKDIR /server/deep_app/static
RUN yarn install
RUN npm install -g browserify swagger-ui-express@4.1.2
RUN yarn run build

WORKDIR /server
RUN npm install
 
CMD ["node", "server.js"]


EXPOSE 8000

