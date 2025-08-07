#!/bin/bash

# NCAA Soccer ETL Deployment Script
# This script packages and deploys the Lambda functions

set -e

# Configuration
PROJECT_NAME="ncaa-soccer-etl"
REGION="us-east-1"
LAMBDA_DIR="lambda"
BUILD_DIR="build"
TERRAFORM_DIR="infrastructure/terraform"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting deployment of NCAA Soccer ETL system...${NC}"

# Create build directory
echo -e "${YELLOW}Creating build directory...${NC}"
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR

# Function to package Lambda function
package_lambda() {
    local function_name=$1
    local source_dir=$2
    
    echo -e "${YELLOW}Packaging $function_name...${NC}"
    
    # Create function directory
    mkdir -p $BUILD_DIR/$function_name
    
    # Copy source files
    cp $source_dir/*.py $BUILD_DIR/$function_name/
    
    # Install dependencies
    if [ -f "$source_dir/requirements.txt" ]; then
        pip install -r $source_dir/requirements.txt -t $BUILD_DIR/$function_name/ --no-deps
    else
        # Install common dependencies
        pip install requests beautifulsoup4 boto3 -t $BUILD_DIR/$function_name/ --no-deps
    fi
    
    # Create ZIP file
    cd $BUILD_DIR/$function_name
    zip -r ../${function_name}.zip .
    cd ../..
    
    echo -e "${GREEN}Packaged $function_name successfully${NC}"
}

# Package all Lambda functions
echo -e "${YELLOW}Packaging Lambda functions...${NC}"

# Match Collector
package_lambda "match_collector" "$LAMBDA_DIR"

# RPI Calculator
package_lambda "rpi_calculator" "$LAMBDA_DIR"

# Gist Publisher
package_lambda "gist_publisher" "$LAMBDA_DIR"

# Deploy with Terraform
echo -e "${YELLOW}Deploying infrastructure with Terraform...${NC}"

cd $TERRAFORM_DIR

# Initialize Terraform
terraform init

# Plan deployment
echo -e "${YELLOW}Planning Terraform deployment...${NC}"
terraform plan -out=tfplan

# Apply deployment
echo -e "${YELLOW}Applying Terraform deployment...${NC}"
terraform apply tfplan

# Get outputs
echo -e "${YELLOW}Deployment outputs:${NC}"
terraform output

cd ../..

echo -e "${GREEN}Deployment completed successfully!${NC}"

# Clean up
echo -e "${YELLOW}Cleaning up build artifacts...${NC}"
rm -rf $BUILD_DIR

echo -e "${GREEN}All done! Your NCAA Soccer ETL system is now deployed.${NC}" 