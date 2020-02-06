FROM node:lts

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - \
echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt-get update && apt-get install yarn -y

COPY . /server

WORKDIR /server/deep_app/static
RUN yarn install

WORKDIR /server
RUN npm install
# RUN npm install zeromq

CMD ["node", "server.js"]


EXPOSE 8000

