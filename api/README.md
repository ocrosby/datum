# Server

This server is an express based API.

## Getting started

Building the Docker image

```bash
docker build . -t jedi-knights/datum-api
```

Listing the docker images

```bash
docker images
```

Run the generated image

```bash
docker run -p 49160:8080 -d jedi-knights/datum-api
```

In this scenario port 49160 on the host machine will be mapped to port 8080 within the container.

Print the output of your app

```bash
# Get container ID
docker ps

# Print app output
docker logs <container id>

# Example
Running on http://localhost:8080
```

Getting inside the container

```bash
docker exec -it <container id> /bin/bash
```
Test the API using curl Test

```bash
curl -i localhost:49160
```

Shut down the image

```bash
# Kill our running container
docker kill <container id>

# Confirm that the app has stopped
curl -i localhost:49160
```