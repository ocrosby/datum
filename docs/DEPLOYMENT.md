# NCAA Soccer RPI Dashboard - Deployment Guide

This guide covers deploying the complete NCAA Soccer RPI Dashboard system, including the serverless ETL backend, React frontend, and Express.js API.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React App     │    │   Express API   │    │  AWS Lambda     │
│   (Frontend)    │◄──►│   (Backend)     │◄──►│  (ETL System)   │
│   Port: 3000    │    │   Port: 3001    │    │  (Serverless)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebSocket     │    │   DynamoDB      │    │   S3 Storage    │
│   Real-time     │    │   (Database)    │    │   (Data Lake)   │
│   Updates       │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Prerequisites

### Required Software
- **Node.js** (v16 or higher)
- **npm** or **yarn**
- **Terraform** (v1.0 or higher)
- **AWS CLI** configured with appropriate permissions
- **Git**

### Required AWS Services
- **Lambda** (for ETL functions)
- **DynamoDB** (for data storage)
- **S3** (for data lake)
- **EventBridge** (for scheduling)
- **CloudWatch** (for monitoring)
- **IAM** (for permissions)

### Required Accounts
- **AWS Account** with billing enabled
- **GitHub Account** (for gist publishing)

## Step 1: Infrastructure Deployment

### 1.1 Configure AWS Credentials
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter your default region (e.g., us-east-1)
```

### 1.2 Deploy Infrastructure
```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Create terraform.tfvars file
cat > terraform.tfvars << EOF
aws_region = "us-east-1"
project_name = "ncaa-soccer-etl"
github_token = "your-github-token-here"
alert_emails = ["your-email@example.com"]
EOF

# Plan the deployment
terraform plan

# Apply the infrastructure
terraform apply

# Note the outputs
terraform output
```

### 1.3 Verify Infrastructure
```bash
# Check Lambda functions
aws lambda list-functions --query 'Functions[?contains(FunctionName, `ncaa-soccer-etl`)]'

# Check DynamoDB tables
aws dynamodb list-tables --query 'TableNames[?contains(@, `ncaa-soccer-etl`)]'

# Check S3 buckets
aws s3 ls | grep ncaa-soccer-etl
```

## Step 2: Backend API Deployment

### 2.1 Setup Backend Environment
```bash
cd backend

# Install dependencies
npm install

# Create environment file
cat > .env << EOF
NODE_ENV=production
PORT=3001
AWS_REGION=us-east-1
RPI_TABLE=ncaa-soccer-etl-rpi-calculations
MATCHES_TABLE=ncaa-soccer-etl-matches
FRONTEND_URL=http://localhost:3000
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-jwt-secret-here
EOF
```

### 2.2 Deploy Backend (Choose one option)

#### Option A: Local Development
```bash
# Start the backend server
npm run dev
```

#### Option B: Docker Deployment
```bash
# Create Dockerfile
cat > Dockerfile << EOF
FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3001
CMD ["npm", "start"]
EOF

# Build and run
docker build -t ncaa-soccer-api .
docker run -p 3001:3001 --env-file .env ncaa-soccer-api
```

#### Option C: AWS ECS/Fargate
```bash
# Create ECS task definition and deploy
# (Detailed ECS deployment steps would go here)
```

## Step 3: Frontend Deployment

### 3.1 Setup Frontend Environment
```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cat > .env << EOF
REACT_APP_API_URL=http://localhost:3001/api
REACT_APP_WS_URL=ws://localhost:3001/ws
REACT_APP_ENVIRONMENT=development
EOF
```

### 3.2 Deploy Frontend (Choose one option)

#### Option A: Local Development
```bash
# Start the React development server
npm start
```

#### Option B: Production Build
```bash
# Build for production
npm run build

# Serve with a static server
npm install -g serve
serve -s build -l 3000
```

#### Option C: AWS S3 + CloudFront
```bash
# Build the app
npm run build

# Upload to S3
aws s3 sync build/ s3://your-frontend-bucket --delete

# Configure CloudFront distribution
# (Detailed CloudFront setup would go here)
```

## Step 4: ETL System Deployment

### 4.1 Package Lambda Functions
```bash
cd lambda

# Create deployment packages
./package.sh

# Verify packages were created
ls -la *.zip
```

### 4.2 Deploy Lambda Functions
```bash
# The Lambda functions should already be deployed via Terraform
# Verify they're working:

# Test match collector
aws lambda invoke \
  --function-name ncaa-soccer-etl-match-collector \
  --payload '{"start_date":"2024-01-01","end_date":"2024-01-07"}' \
  response.json

# Test RPI calculator
aws lambda invoke \
  --function-name ncaa-soccer-etl-rpi-calculator \
  --payload '{"start_date":"2024-01-01","end_date":"2024-01-31"}' \
  response.json
```

## Step 5: Configuration and Testing

### 5.1 Configure GitHub Token
```bash
# Set GitHub token in AWS Systems Manager
aws ssm put-parameter \
  --name "/ncaa-soccer-etl/github-token" \
  --value "your-github-token" \
  --type "SecureString"
```

### 5.2 Test the Complete System
```bash
# 1. Test API endpoints
curl http://localhost:3001/api/rpi/rankings

# 2. Test WebSocket connection
# Use a WebSocket client to connect to ws://localhost:3001/ws

# 3. Test frontend
# Open http://localhost:3000 in your browser
```

### 5.3 Monitor the System
```bash
# Check CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/ncaa-soccer-etl"

# Check DynamoDB data
aws dynamodb scan --table-name ncaa-soccer-etl-rpi-calculations --limit 5

# Check S3 data
aws s3 ls s3://ncaa-soccer-etl-processed-data/rpi_results/
```

## Step 6: Production Considerations

### 6.1 Security
- [ ] Enable HTTPS for all endpoints
- [ ] Configure CORS properly
- [ ] Set up proper IAM roles
- [ ] Enable CloudTrail logging
- [ ] Configure WAF if needed

### 6.2 Monitoring
- [ ] Set up CloudWatch alarms
- [ ] Configure SNS notifications
- [ ] Set up custom dashboards
- [ ] Enable X-Ray tracing

### 6.3 Scaling
- [ ] Configure auto-scaling for the API
- [ ] Set up CDN for frontend
- [ ] Configure DynamoDB auto-scaling
- [ ] Set up read replicas if needed

### 6.4 Backup and Recovery
- [ ] Enable DynamoDB point-in-time recovery
- [ ] Set up S3 versioning
- [ ] Configure cross-region replication
- [ ] Test disaster recovery procedures

## Troubleshooting

### Common Issues

#### 1. Lambda Function Errors
```bash
# Check Lambda logs
aws logs tail /aws/lambda/ncaa-soccer-etl-match-collector --follow

# Test function directly
aws lambda invoke --function-name ncaa-soccer-etl-match-collector --payload '{}' response.json
```

#### 2. DynamoDB Connection Issues
```bash
# Check table exists
aws dynamodb describe-table --table-name ncaa-soccer-etl-rpi-calculations

# Check permissions
aws iam get-role --role-name ncaa-soccer-etl-lambda-role
```

#### 3. API Connection Issues
```bash
# Check if API is running
curl http://localhost:3001/health

# Check logs
docker logs <container-id>  # if using Docker
```

#### 4. Frontend Issues
```bash
# Check build
npm run build

# Check environment variables
echo $REACT_APP_API_URL

# Clear cache
rm -rf node_modules/.cache
```

## Cost Optimization

### Estimated Monthly Costs
- **Lambda**: $5-20 (depending on usage)
- **DynamoDB**: $10-30 (on-demand)
- **S3**: $5-15 (storage + requests)
- **CloudWatch**: $5-10 (logs + metrics)
- **API Gateway**: $5-15 (if using)
- **CloudFront**: $10-20 (if using)

### Cost Optimization Tips
1. **Use DynamoDB on-demand billing** initially
2. **Set up CloudWatch alarms** for cost monitoring
3. **Use S3 lifecycle policies** for old data
4. **Optimize Lambda memory** settings
5. **Use CloudFront** for static content

## Maintenance

### Regular Tasks
- [ ] Monitor CloudWatch metrics daily
- [ ] Check Lambda function logs weekly
- [ ] Review DynamoDB costs monthly
- [ ] Update dependencies quarterly
- [ ] Test disaster recovery annually

### Updates
```bash
# Update Lambda functions
./scripts/deploy.sh

# Update backend
cd backend && npm update

# Update frontend
cd frontend && npm update
```

## Support

For issues or questions:
1. Check the CloudWatch logs first
2. Review the troubleshooting section
3. Check AWS service status
4. Contact the development team

## Next Steps

After successful deployment:
1. **Set up monitoring dashboards**
2. **Configure alerting**
3. **Train users on the system**
4. **Document operational procedures**
5. **Plan for scaling**

This deployment guide provides a comprehensive approach to deploying the NCAA Soccer RPI Dashboard system. Follow each step carefully and test thoroughly before going to production. 