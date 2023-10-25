FROM node:18

# Create app directory

WORKDIR /usr/src/app


# Install app dependencies
COPY package*.json ./

# This installs all of the dependencies of the project, including the dev dependencies.
# RUN npm install

# If you are building your code for production
# RUN npm ci --only=production
# or
RUN npm ci --omit=dev

# Bundle app source
COPY . .

# Your app binds to port 8080 so you'll use the EXPOSE instruction to have it mapped by the docker daemon
EXPOSE 8080

# Last but not least, define the command to run your app using CMD which defines your runtime.

CMD [ "node", "server.js" ]
