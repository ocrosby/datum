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


## Path Based Routing

For path-based routing with a URL structure like https://jedi-knights.tech/datum/api associated with your Datum API, you can follow these steps:

### DNS Configuration:

In Amazon Route 53, configure your domain (e.g., "jedi-knights.tech") with the necessary DNS records. Ensure that the domain points to the appropriate resources or load balancers that will handle the incoming requests.

### SSL/TLS Certificate:

Obtain an SSL/TLS certificate for your domain (e.g., "jedi-knights.tech") to enable HTTPS for secure communication.

### Load Balancer:

Set up an AWS Elastic Load Balancer (ELB) or an Application Load Balancer (ALB) to act as a front-end for your API routing.
Configure the load balancer to handle traffic for the domain (e.g., "jedi-knights.tech").
Create listeners and rules to route incoming requests based on the URL path to the appropriate backend services.

### Path-Based Routing:

Configure your load balancer to perform path-based routing. You can define rules that direct traffic based on the URL path.
For example, if you want https://jedi-knights.tech/datum/api to be associated with your Datum API, create a rule that routes requests with a path of /datum/api to the backend service for your Datum API.

### Backend Services:

Set up the backend services for your Datum API. These services can be hosted on Amazon EC2 instances, AWS Elastic Beanstalk, AWS Lambda, or other AWS services.
Ensure that your backend services are properly configured to handle requests with the specified path, in this case, /datum/api.

### Security and Authorization:

Implement security measures and access control for your API using AWS services such as AWS Identity and Access Management (IAM) or Amazon Cognito.

### Testing and Monitoring:

Test your path-based routing configuration to ensure it correctly directs traffic to the desired backend services.
Implement monitoring and logging to track the performance and health of your API.
With this setup, requests to https://jedi-knights.tech/datum/api will be routed to your Datum API, while other paths can be routed to different backend services. Make sure to adjust the routing rules, load balancer configuration, and backend services to match your specific use case and requirements.

