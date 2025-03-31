import json
import os
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests.auth import HTTPBasicAuth

def create_opensearch_client():
    """Create OpenSearch client with basic auth"""
    host = os.environ['OPENSEARCH_ENDPOINT']
    username = os.environ['OPENSEARCH_USERNAME']
    password = os.environ['OPENSEARCH_PASSWORD']
    
    return OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=(username, password),
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )

def create_index_if_not_exists(client, index_name):
    """Create index with mapping if it doesn't exist"""
    try:
        if not client.indices.exists(index=index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "content": {
                            "type": "text",
                            "analyzer": "standard"
                        },
                        "source": {
                            "properties": {
                                "bucket": {"type": "keyword"},
                                "key": {"type": "keyword"},
                                "last_modified": {"type": "date", "ignore_malformed": True},
                                "size": {"type": "long"}
                            }
                        }
                    }
                }
            }
            client.indices.create(index=index_name, body=mapping)
            print(f"Created index {index_name}")
    except Exception as e:
        print(f"Error creating index: {str(e)}")
        raise

def process_file(s3_client, bucket, key):
    """Process the TXT file from S3"""
    try:
        # Get the file from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        file_content = response['Body'].read().decode('utf-8')
        
        # Create document data
        document_data = {
            'content': file_content,
            'source': {
                'bucket': bucket,
                'key': key,
                'last_modified': str(response['LastModified']),
                'size': response['ContentLength']
            }
        }
        
        return document_data
    except Exception as e:
        print(f"Error processing file {key}: {str(e)}")
        raise

def handler(event, context):
    """Lambda handler"""
    try:
        s3_client = boto3.client('s3')
        opensearch_client = create_opensearch_client()
        index_name = os.environ.get('OPENSEARCH_INDEX', 'txt-documents')
        
        # Ensure index exists
        create_index_if_not_exists(opensearch_client, index_name)
        
        # Process each record
        processed_records = []
        failed_records = []
        
        for record in event['Records']:
            try:
                # Parse SQS message to get S3 event
                body = json.loads(record['body'])
                s3_record = body['Records'][0]
                bucket = s3_record['s3']['bucket']['name']
                key = s3_record['s3']['object']['key']
                
                # Only process TXT files
                if not key.lower().endswith('.txt'):
                    print(f"Skipping non-TXT file: {key}")
                    continue
                
                # Process the file
                document_data = process_file(s3_client, bucket, key)
                
                # Index the document
                response = opensearch_client.index(
                    index=index_name,
                    body=document_data,
                    id=f"{bucket}/{key}",  # Use S3 location as document ID
                    refresh=True
                )
                
                print(f"Successfully indexed document {key}: {response}")
                processed_records.append(key)
                
            except Exception as e:
                print(f"Error processing record: {str(e)}")
                failed_records.append(key)
                continue
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'processed': processed_records,
                'failed': failed_records
            })
        }
        
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        raise