# AWS Lambda Layer for OpenSearch and Requests

This guide explains how to create an AWS Lambda layer containing the `opensearch-py` and `requests` Python packages using AWS CloudShell, with cross-region layer deployment.

## Prerequisites

- AWS Account with appropriate permissions
- Access to AWS CloudShell
- AWS CLI configured in your computer

## Step-by-Step Instructions

### 1. Prepare Working Directory

Open AWS CloudShell (in a supported region like N. Virginia) and create a working directory:

```bash
mkdir lambda-layer
cd lambda-layer
```

### 2. Create Layer Directory Structure

Create the required directory structure for Python packages:

```bash
mkdir -p python/lib/python3.9/site-packages
```

### 3. Set Up Python Virtual Environment

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Required Packages

Install the packages into the layer directory:

```bash
ppip3 install opensearchpy requests -t python/lib/python3.9/site-packages --platform manylinux2014_x86_64 --python-version 3.9 --only-binary=:all:
```

### 5. Create ZIP Archive

Create a ZIP file containing the layer contents:

```bash
cd python
zip -r ../lambda-layer.zip .
cd ..
```

### 6. Publish Lambda Layer in N. Virginia (us-east-1)

Publish the layer using AWS CLI:

```bash
aws lambda publish-layer-version \
    --layer-name opensearch-requests-layer \
    --description "Layer for OpenSearch and Requests packages" \
    --license-info "MIT" \
    --zip-file fileb://lambda-layer.zip \
    --compatible-runtimes python3.9 \
    --compatible-architectures "x86_64"
```

### 7. Cross-Region Layer Deployment

Since CloudShell is not available in the TLV (Israel) region, follow these steps to publish the layer in TLV:

#### Download Layer ZIP

1. Use the AWS Management Console to download the `lambda-layer.zip` file.

#### Publish Layer in TLV Region

2. Publish the layer in TLV region - via AWS CLI in your computer:

```bash
# Use the same command as in step 6, but specify TLV region
aws lambda publish-layer-version \
    --layer-name opensearch-requests-layer \
    --description "Layer for OpenSearch and Requests packages" \
    --license-info "MIT" \
    --zip-file fileb://lambda-layer.zip \
    --compatible-runtimes python3.9 \
    --compatible-architectures "x86_64" \
    --region il-central-1
```

#### Verify Layer Deployment

3. List layers in TLV region to confirm:

```bash
aws lambda list-layers --region il-central-1
```

## Notes

- The example uses Python 3.9. Adjust the version according to your needs
- Layer version number ( :1 in the ARN) may vary if you've published multiple versions
- Ensure you're in the correct AWS region
- The total unzipped size of the layer must be under 250 MB
- When switching between regions, always specify the `--region` flag or use AWS CLI profiles

## Troubleshooting

If you encounter permission issues:
- Ensure you have the necessary IAM permissions to create Lambda layers
- Verify you're in the correct AWS region
- Check AWS CLI configuration and credentials
- Confirm that you have the same IAM roles and permissions in both source and target regions