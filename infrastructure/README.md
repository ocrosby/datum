# Infrastructure Setup with Terraform

This directory contains Terraform configurations for managing AWS infrastructure for the Datum project.

## Prerequisites

### Installing Terraform on macOS

#### Option 1: Using Homebrew (Recommended)
```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Terraform
brew install terraform

# Verify installation
terraform --version
```

#### Option 2: Manual Installation
```bash
# Download the latest version for macOS
curl -O https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_darwin_amd64.zip

# Unzip and move to /usr/local/bin
unzip terraform_1.6.0_darwin_amd64.zip
sudo mv terraform /usr/local/bin/

# Verify installation
terraform --version
```

### Setting up AWS Credentials

#### Option 1: AWS CLI Configuration
```bash
# Install AWS CLI
brew install awscli

# Configure AWS credentials
aws configure

# You'll be prompted for:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (e.g., us-east-1)
# - Default output format (json)
```

**Checking AWS CLI Configuration:**
```bash
# Check if AWS CLI is installed
aws --version

# Check current AWS identity
aws sts get-caller-identity

# List configured profiles
aws configure list-profiles

# Check default profile configuration
aws configure list

# Test with a simple AWS command
aws s3 ls
```

#### Option 2: Environment Variables
```bash
# Set environment variables in your shell profile (~/.zshrc or ~/.bash_profile)
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_DEFAULT_REGION="us-east-1"

# Reload your shell profile
source ~/.zshrc
```

#### Option 3: AWS Profiles
```bash
# Create a named profile
aws configure --profile datum

# Use the profile with Terraform
export AWS_PROFILE=datum
```

## Project Structure

```
infrastructure/
├── terraform/
│   ├── main.tf          # Main Terraform configuration
│   └── monitoring.tf    # Monitoring and logging resources
└── README.md           # This file
```

## Getting Started

### 1. Initialize Terraform
```bash
cd infrastructure/terraform
terraform init
```

### 2. Review the Plan
```bash
terraform plan
```

### 3. Apply the Configuration
```bash
terraform apply
```

### 4. Destroy Resources (when needed)
```bash
terraform destroy
```

## Terraform Commands Reference

### Basic Commands
- `terraform init` - Initialize a Terraform working directory
- `terraform plan` - Generate and show an execution plan
- `terraform apply` - Build or change infrastructure
- `terraform destroy` - Destroy Terraform-managed infrastructure
- `terraform validate` - Check whether the configuration is valid
- `terraform fmt` - Rewrite configuration files to canonical format

### State Management
- `terraform state list` - List resources in the state
- `terraform state show <resource>` - Show details of a resource
- `terraform state rm <resource>` - Remove a resource from the state
- `terraform import <resource> <id>` - Import existing infrastructure

### Output and Variables
- `terraform output` - Show output values
- `terraform output <name>` - Show specific output value
- `terraform refresh` - Update state file against real resources

## Example Usage

### Creating a Simple EC2 Instance

```hcl
# main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_instance" "example" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  tags = {
    Name = "ExampleInstance"
  }
}
```

### Using Variables

```hcl
# variables.tf
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "development"
}

# main.tf
resource "aws_instance" "example" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = var.instance_type

  tags = {
    Name        = "ExampleInstance"
    Environment = var.environment
  }
}
```

### Using Outputs

```hcl
# outputs.tf
output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.example.id
}

output "public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.example.public_ip
}
```

## Best Practices

### 1. State Management
- Use remote state storage (S3 + DynamoDB) for team environments
- Never commit `.tfstate` files to version control
- Use workspaces for different environments

### 2. Security
- Use IAM roles and policies with least privilege
- Store sensitive values in AWS Secrets Manager or Parameter Store
- Use data sources instead of hardcoded values

### 3. Organization
- Use modules for reusable components
- Separate environments with different state files
- Use consistent naming conventions

### 4. Cost Management
- Use `terraform plan` before applying changes
- Tag resources appropriately for cost tracking
- Use spot instances where appropriate

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```bash
   # Verify AWS credentials
   aws sts get-caller-identity
   ```

2. **State Lock Issues**
   ```bash
   # Force unlock (use with caution)
   terraform force-unlock <lock_id>
   ```

3. **Provider Version Conflicts**
   ```bash
   # Update provider versions
   terraform init -upgrade
   ```

### Getting Help
- [Terraform Documentation](https://www.terraform.io/docs)
- [AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform Community](https://discuss.hashicorp.com/)

## Next Steps

1. Review the existing Terraform configurations in the `terraform/` directory
2. Customize the configurations for your specific needs
3. Set up remote state storage for team collaboration
4. Implement CI/CD pipelines for infrastructure deployment
5. Set up monitoring and alerting for your infrastructure
