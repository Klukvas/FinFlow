#!/bin/bash
set -e

echo "=========================================="
echo "  Hetzner Infrastructure Deployment"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if secrets.tfvars exists
if [ ! -f "secrets.tfvars" ]; then
    echo -e "${RED}Error: secrets.tfvars not found!${NC}"
    echo "Please create secrets.tfvars with your Hetzner API token and configuration."
    exit 1
fi

# Initialize Terraform
echo -e "${YELLOW}Step 1/4: Initializing Terraform...${NC}"
terraform init

# Validate configuration
echo -e "${YELLOW}Step 2/4: Validating configuration...${NC}"
terraform validate

if [ $? -ne 0 ]; then
    echo -e "${RED}Validation failed!${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Configuration is valid${NC}"
echo ""

# Plan
echo -e "${YELLOW}Step 3/4: Planning infrastructure changes...${NC}"
terraform plan -var-file=secrets.tfvars -out=tfplan

echo ""
echo -e "${YELLOW}Step 4/4: Apply infrastructure changes${NC}"
echo -e "${YELLOW}Please review the plan above.${NC}"
read -p "Do you want to apply these changes? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${YELLOW}Deployment cancelled.${NC}"
    rm -f tfplan
    exit 0
fi

# Apply
echo -e "${GREEN}Applying changes...${NC}"
terraform apply tfplan

# Clean up plan file
rm -f tfplan

echo ""
echo -e "${GREEN}=========================================="
echo "  Deployment Complete!"
echo "==========================================${NC}"
echo ""

# Get outputs
echo -e "${GREEN}Connection Details:${NC}"
echo ""
terraform output app_server_public_ipv4
terraform output db_host
terraform output db_user
terraform output db_name
echo ""

echo -e "${YELLOW}Important:${NC}"
echo "1. SSH commands are available via 'terraform output ssh_command_app'"
echo "2. Database password: terraform output -raw db_password"
echo "3. Full connection string: terraform output -raw connection_string"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo "1. SSH to the app server: \$(terraform output -raw ssh_command_app)"
echo "2. Wait for cloud-init to complete: sudo tail -f /var/log/cloud-init-output.log"
echo "3. Copy your docker-compose setup to ~/app/ on the server"
echo "4. Create .env file with database credentials"
echo "5. Start services: cd ~/app && docker compose up -d"
echo ""

