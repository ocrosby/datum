# Datum

This is an example application providing a simple API and a UI for interacting data from a database.

## Pre-requisites

This project utilizes [Docker Community Edition](https://docs.docker.com/get-docker/).  Please install Docker before continuing.

## Getting started

To start up your full stack application you can now simply do this:

```bash
npm run docker:up
```

When running if you want to shut it down from the terminal just enter `CTRL+C` and then run:

```bash
npm run docker:down
```


I've created a separate docker compose file to spin up only the PostgreSQL database and the pgAdmin client.  This is useful if you want to connect to the database and run queries or view the data in the tables.

Startup the database and pgAdmin client:

```bash
docker-compose -f docker-compose-api.yml up -d
```


## Domain Association 

To associate multiple applications with your domain "jedi-knights.tech" on AWS and have different subdomains or paths for each application, you can use Amazon Web Services (AWS) services like Amazon API Gateway, Amazon S3, and AWS Elastic Beanstalk (or AWS Lambda for serverless) in combination with Amazon Route 53 for DNS management. Here's a high-level overview of how you can achieve this:

### Amazon Route 53:

Purchase and register the domain "jedi-knights.tech" using Amazon Route 53. You can do this through the AWS Management Console.
Set up DNS records (A or CNAME records) for your domain to point to your AWS resources, such as an Elastic Load Balancer, S3 bucket, or API Gateway.

### AWS Elastic Beanstalk:

Deploy your Datum web application as an Elastic Beanstalk environment. This can be used for hosting the web application.
Configure the Elastic Beanstalk environment to use your custom domain by associating it with a load balancer or an Application Load Balancer (ALB).

### Amazon S3:

Host your Datum web application (static files) on an Amazon S3 bucket. You can use Amazon S3 to serve the front-end assets.
Configure your S3 bucket for static website hosting.

### Amazon API Gateway:

Create an API in Amazon API Gateway for your Datum API.
Configure custom domain names for your API Gateway.
Use API Gateway to create API methods, endpoints, and integrate with your APIs back end.

### Path and Subdomain Routing:

To associate different applications or services with subdomains, you can set up subdomains in Route 53 and point them to the corresponding resources.
For path-based routing, you can use a combination of Amazon API Gateway and AWS Lambda to route requests based on the paths to the appropriate backend services.

### SSL/TLS Certificates:

If you want to secure your applications with SSL/TLS, you can use AWS Certificate Manager to issue SSL/TLS certificates and associate them with your domains and subdomains.

### Authentication and Authorization:

Implement authentication and authorization mechanisms as needed for your applications. AWS Cognito and Amazon Identity and Access Management (IAM) are commonly used for this purpose.

### Monitoring and Logging:

Set up monitoring, logging, and alerting for your applications using AWS CloudWatch, AWS X-Ray, and other monitoring tools to ensure the health and performance of your applications.

### Deployment and Scaling:

Configure auto-scaling and load balancing for your applications to handle varying levels of traffic.

### Testing:

Thoroughly test your setup to ensure that each application and subdomain/path routing works as expected.

## References

- [REST API Tutorial](https://www.restapitutorial.com/)
- [Versioning REST API routes in Express.js](https://medium.com/@jamsesso/versioning-rest-api-routes-in-express-js-f7287e1c8886)
- [CRUD REST API with Node.js, Express, and PostgreSQL](https://blog.logrocket.com/crud-rest-api-node-js-express-postgresql/)
- [How to Run PostgreSQL and pgAdmin Using Docker](https://towardsdatascience.com/how-to-run-postgresql-and-pgadmin-using-docker-3a6a8ae918b5)
