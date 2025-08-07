# NCAA Soccer ETL System Architecture

## Overview

The NCAA Soccer ETL system is a serverless, event-driven architecture designed to collect NCAA soccer match data, calculate RPI (Rating Percentage Index) values, and publish results via GitHub gists. The system is built for scalability, reliability, and cost-effectiveness.

## Architecture Components

### 1. Data Flow

```
NCAA Website → Match Collector Lambda → DynamoDB → RPI Calculator Lambda → S3 → Gist Publisher Lambda → GitHub Gist
```

### 2. Infrastructure Components

#### **Storage Layer**
- **S3 Buckets**:
  - `raw-data-*`: Stores raw match data for audit and backup
  - `processed-data-*`: Stores processed RPI results and metadata

- **DynamoDB Tables**:
  - `matches`: Stores match data with date-based indexing
  - `rpi-calculations`: Stores RPI calculation results

#### **Compute Layer**
- **Lambda Functions**:
  - `match-collector`: Scrapes NCAA match data
  - `rpi-calculator`: Calculates RPI values for all teams
  - `gist-publisher`: Creates GitHub gists with results

#### **Event Layer**
- **EventBridge Rules**:
  - Daily RPI calculation (6 AM UTC)
  - Match data collection (every 4 hours)

#### **Monitoring Layer**
- **CloudWatch**:
  - Log groups for each Lambda function
  - Alarms for errors and performance
  - Dashboard for system metrics
- **SNS**: Alert notifications

## Detailed Component Descriptions

### Match Collector Lambda

**Purpose**: Scrapes NCAA soccer match data from the official website

**Input**: EventBridge scheduled trigger or manual invocation

**Process**:
1. Determines date range (default: last 7 days)
2. Scrapes NCAA scoreboard pages
3. Parses match data (teams, scores, dates)
4. Stores in DynamoDB with unique match IDs
5. Backs up raw data to S3
6. Triggers RPI calculation if new completed matches found

**Output**: Match data stored in DynamoDB and S3

### RPI Calculator Lambda

**Purpose**: Calculates RPI values for all NCAA teams

**Input**: Triggered by match collector or scheduled daily

**Process**:
1. Loads match data from DynamoDB for specified date range
2. Calculates team records (wins, losses, ties)
3. Computes RPI components:
   - WP (Winning Percentage)
   - OWP (Opponents' Winning Percentage)
   - OOWP (Opponents' Opponents' Winning Percentage)
4. Applies RPI formula: `RPI = (0.25 × WP) + (0.50 × OWP) + (0.25 × OOWP)`
5. Sorts teams by RPI (descending)
6. Stores results in DynamoDB and S3
7. Triggers gist publisher

**Output**: RPI rankings stored in DynamoDB and S3

### Gist Publisher Lambda

**Purpose**: Creates GitHub gists with RPI data

**Input**: Triggered by RPI calculator

**Process**:
1. Retrieves RPI results from S3
2. Creates formatted files (JSON, CSV, summary)
3. Generates descriptive text with top teams
4. Creates public GitHub gist
5. Stores gist metadata in S3

**Output**: Public GitHub gist with RPI data

## Data Models

### Match Data (DynamoDB)
```json
{
  "match_id": "2024-10-15_Stanford_UC_Berkeley",
  "date": "2024-10-15",
  "home_team": "Stanford",
  "away_team": "UC Berkeley",
  "home_score": 2,
  "away_score": 1,
  "status": "completed",
  "timestamp": "2024-10-15T18:30:00Z"
}
```

### RPI Results (DynamoDB)
```json
{
  "calculation_date": "2024-10-15",
  "team_id": "Stanford",
  "rank": 1,
  "rpi": 0.8234,
  "wp": 0.8500,
  "owp": 0.7200,
  "oowp": 0.6500,
  "wins": 15,
  "losses": 2,
  "ties": 1,
  "total_games": 18,
  "win_percentage": 0.8611,
  "timestamp": "2024-10-15T06:00:00Z"
}
```

## Scalability Features

### **Auto-scaling**
- Lambda functions scale automatically based on demand
- DynamoDB uses on-demand billing (no capacity planning)
- S3 scales infinitely

### **Event-driven**
- Functions triggered only when needed
- No idle resources
- Parallel processing capabilities

### **Cost Optimization**
- Pay-per-use pricing model
- No idle server costs
- Automatic scaling down

## Reliability Features

### **Error Handling**
- Comprehensive try-catch blocks
- CloudWatch logging for debugging
- SNS alerts for failures

### **Data Durability**
- S3 versioning enabled
- DynamoDB automatic backups
- Multiple storage locations

### **Retry Logic**
- Lambda automatic retries
- Dead letter queues for failed events
- Manual retry capabilities

## Security

### **IAM Roles**
- Least privilege access
- Function-specific permissions
- No hardcoded credentials

### **Data Protection**
- All data encrypted at rest
- HTTPS for all API calls
- GitHub token stored as environment variable

## Monitoring and Alerting

### **CloudWatch Metrics**
- Lambda invocations, errors, duration
- DynamoDB read/write capacity
- S3 request metrics

### **Alarms**
- Error rate thresholds
- Performance degradation alerts
- Cost monitoring

### **Dashboard**
- Real-time system overview
- Historical trends
- Custom metrics

## Deployment

### **Infrastructure as Code**
- Terraform for all AWS resources
- Version controlled configuration
- Reproducible deployments

### **CI/CD Pipeline**
- Automated testing
- Staging environment
- Blue-green deployments

## Cost Estimation

### **Monthly Costs (estimated)**
- Lambda: $5-20 (depending on usage)
- DynamoDB: $10-30 (on-demand)
- S3: $5-15 (storage + requests)
- CloudWatch: $5-10 (logs + metrics)
- **Total**: $25-75/month

## Future Enhancements

### **Planned Features**
1. **API Gateway**: REST API for data access
2. **Step Functions**: Orchestrate complex workflows
3. **Athena**: SQL queries on S3 data
4. **QuickSight**: Data visualization
5. **Machine Learning**: Predictive analytics

### **Scalability Improvements**
1. **Parallel Processing**: Multiple Lambda instances
2. **Caching**: ElastiCache for frequently accessed data
3. **CDN**: CloudFront for gist distribution
4. **Database Optimization**: DynamoDB DAX for read caching

## Troubleshooting

### **Common Issues**
1. **Lambda Timeouts**: Increase timeout or optimize code
2. **DynamoDB Throttling**: Use on-demand billing
3. **S3 Errors**: Check IAM permissions
4. **GitHub API Limits**: Implement rate limiting

### **Debugging Tools**
1. **CloudWatch Logs**: Detailed function logs
2. **X-Ray**: Request tracing
3. **CloudTrail**: API call auditing
4. **Custom Metrics**: Business-specific monitoring

## Getting Started

1. **Prerequisites**:
   - AWS account with appropriate permissions
   - GitHub personal access token
   - Terraform installed

2. **Deployment**:
   ```bash
   chmod +x scripts/deploy.sh
   ./scripts/deploy.sh
   ```

3. **Configuration**:
   - Set GitHub token in Terraform variables
   - Configure alert email addresses
   - Adjust scheduling as needed

4. **Monitoring**:
   - Check CloudWatch dashboard
   - Review Lambda logs
   - Monitor SNS alerts

This architecture provides a robust, scalable foundation for NCAA soccer data processing with room for future enhancements and optimizations. 