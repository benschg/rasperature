# Rasperature GCP Infrastructure

This directory contains Terraform configuration for deploying the Rasperature cloud infrastructure on Google Cloud Platform.

## Prerequisites

- [Terraform](https://www.terraform.io/downloads) >= 1.0
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- GCP Project with billing enabled
- Appropriate IAM permissions to create resources

## Architecture

The infrastructure includes:

- **Pub/Sub**: Message ingestion from Raspberry Pi devices
- **BigQuery**: Data warehousing and analytics
- **Cloud Run**: API service for web dashboard
- **IAM**: Service accounts and permissions
- **Monitoring**: Alerts and dashboards

## Quick Start

### 1. Initialize GCP Project

```bash
# Set your project ID
export PROJECT_ID="your-project-id"

# Authenticate with GCP
gcloud auth login
gcloud config set project $PROJECT_ID

# Enable billing (if not already enabled)
# Visit: https://console.cloud.google.com/billing
```

### 2. Configure Terraform

```bash
# Copy example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
vim terraform.tfvars
```

### 3. Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Apply changes
terraform apply
```

### 4. Create Service Account Key for Raspberry Pi

```bash
# Get the service account email from Terraform output
PI_SA_EMAIL=$(terraform output -raw pi_service_account_email)

# Create and download key
gcloud iam service-accounts keys create pi-credentials.json \
  --iam-account=$PI_SA_EMAIL

# Copy to your Raspberry Pi
scp pi-credentials.json pi@raspberrypi:~/rasperature/pi-app/
```

## Configuration

### terraform.tfvars

Create a `terraform.tfvars` file with your specific values:

```hcl
project_id = "your-gcp-project-id"
region     = "us-central1"
environment = "prod"

pubsub_topic_name = "sensor-data-raw"
bigquery_dataset_id = "sensor_data"
bigquery_table_id = "readings"

data_retention_days = 90

# For API deployment (after building Docker image)
cloud_run_api_image = "gcr.io/your-project-id/rasperature-api:latest"
api_max_instances = 10
api_min_instances = 0
```

## Outputs

After applying, Terraform will output:

- `project_id`: Your GCP project ID
- `region`: Deployed region
- `pubsub_topic_name`: Pub/Sub topic for sensor data
- `bigquery_dataset_id`: BigQuery dataset ID
- `bigquery_table_id`: BigQuery table ID
- `pi_service_account_email`: Service account email for Raspberry Pi devices
- `api_service_account_email`: Service account email for API service
- `api_url`: URL of the deployed API (after Cloud Run deployment)

## Cost Estimation

For 100K sensors at 2 readings/second with edge downsampling (60% reduction):

- **Pub/Sub**: ~$1,446/month
- **BigQuery Storage**: ~$2,074/month
- **BigQuery Queries**: ~$3,500/month (varies by usage)
- **Cloud Run**: ~$200-500/month
- **Data Transfer**: ~$462/month

**Total: ~$7,500-8,000/month**

## Monitoring

Access monitoring resources:

- **Dashboard**: Cloud Console → Monitoring → Dashboards → "Rasperature Monitoring"
- **Alerts**: Cloud Console → Monitoring → Alerting
- **Logs**: Cloud Console → Logging

## Maintenance

### Update Infrastructure

```bash
# Pull latest Terraform configurations
git pull

# Plan changes
terraform plan

# Apply updates
terraform apply
```

### View Resources

```bash
# List all resources
terraform state list

# Show specific resource
terraform show google_pubsub_topic.sensor_data
```

### Destroy Infrastructure

⚠️ **WARNING**: This will delete all data!

```bash
terraform destroy
```

## Troubleshooting

### API Quota Errors

If you encounter quota errors, request quota increases in Cloud Console:
- IAM & Admin → Quotas

### Permission Errors

Ensure you have the following roles:
- `roles/editor` or `roles/owner` on the project
- `roles/iam.serviceAccountAdmin`
- `roles/resourcemanager.projectIamAdmin`

### State Lock Issues

If Terraform state is locked:

```bash
terraform force-unlock <LOCK_ID>
```

## Security Best Practices

1. **Use Remote State**: Store Terraform state in GCS bucket
2. **Rotate Keys**: Regularly rotate service account keys
3. **Least Privilege**: Grant minimal necessary permissions
4. **Enable VPC Service Controls**: For production deployments
5. **Use Secret Manager**: For sensitive configuration

## Next Steps

1. Deploy the REST API to Cloud Run (see `cloud-api/` directory)
2. Deploy the web dashboard (see `web-dashboard/` directory)
3. Configure Raspberry Pi devices with service account credentials
4. Set up notification channels for alerts

## Support

For issues or questions:
- Open an issue on GitHub
- Check the main README.md
- Review GCP documentation
