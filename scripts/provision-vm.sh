#!/bin/bash
# MedSearch GCE VM Provisioning Script
# Usage: ./scripts/provision-vm.sh [PROJECT_ID] [ZONE]

set -e

PROJECT_ID=${1:-"medsearch-ai"}
ZONE=${2:-"us-central1-a"}
VM_NAME="medsearch-vm"
MACHINE_TYPE="e2-standard-2"
DISK_SIZE="50"

echo "========================================="
echo "MedSearch VM Provisioning"
echo "========================================="
echo "Project ID: $PROJECT_ID"
echo "Zone: $ZONE"
echo "VM Name: $VM_NAME"
echo "Machine Type: $MACHINE_TYPE"
echo "========================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed"
    echo "Please install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
echo "📋 Setting GCP project..."
gcloud config set project $PROJECT_ID

# Create VM instance
echo "🚀 Creating VM instance..."
gcloud compute instances create $VM_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --service-account=default \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --create-disk=auto-delete=yes,boot=yes,device-name=$VM_NAME,image=projects/ubuntu-os-cloud/global/images/ubuntu-2204-jammy-v20241004,mode=rw,size=$DISK_SIZE,type=projects/$PROJECT_ID/zones/$ZONE/diskTypes/pd-standard \
    --no-shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --labels=environment=production,project=medsearch \
    --tags=http-server,https-server \
    --reservation-affinity=any

echo "⏳ Waiting for VM to be ready..."
sleep 30

# Create firewall rules
echo "🔥 Creating firewall rules..."
gcloud compute firewall-rules create allow-http \
    --project=$PROJECT_ID \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:80 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=http-server \
    2>/dev/null || echo "Firewall rule 'allow-http' already exists"

gcloud compute firewall-rules create allow-https \
    --project=$PROJECT_ID \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:443 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=https-server \
    2>/dev/null || echo "Firewall rule 'allow-https' already exists"

# Install Docker and dependencies
echo "🐳 Installing Docker and dependencies..."
gcloud compute ssh $VM_NAME --zone=$ZONE --project=$PROJECT_ID --command="
    set -e
    
    # Update system
    sudo apt-get update
    sudo apt-get upgrade -y
    
    # Install Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    rm get-docker.sh
    
    # Add user to docker group
    sudo usermod -aG docker \$USER
    
    # Install Docker Compose
    sudo curl -L 'https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-linux-x86_64' -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    # Create application directory
    mkdir -p ~/medsearch/{logs,data,backups}
    
    # Setup log rotation
    sudo tee /etc/logrotate.d/medsearch > /dev/null <<EOF
/home/\$USER/medsearch/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 \$USER \$USER
}
EOF
    
    # Enable automatic security updates
    sudo apt-get install -y unattended-upgrades
    sudo dpkg-reconfigure --priority=low unattended-upgrades
    
    # Verify installations
    docker --version
    docker-compose --version
    
    echo '✅ VM setup complete!'
"

# Get VM external IP
VM_IP=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo ""
echo "========================================="
echo "✅ VM Provisioning Complete!"
echo "========================================="
echo "VM Name: $VM_NAME"
echo "External IP: $VM_IP"
echo "Zone: $ZONE"
echo ""
echo "Next Steps:"
echo "1. SSH into VM: gcloud compute ssh $VM_NAME --zone=$ZONE"
echo "2. Copy service account key to ~/medsearch/medsearch-key.json"
echo "3. Create .env.production file in ~/medsearch/"
echo "4. Deploy application using GitHub Actions"
echo ""
echo "Application URLs (after deployment):"
echo "  Frontend: http://$VM_IP"
echo "  API: http://$VM_IP/api/v1"
echo "  API Docs: http://$VM_IP/docs"
echo "  Health: http://$VM_IP/health"
echo "========================================="

