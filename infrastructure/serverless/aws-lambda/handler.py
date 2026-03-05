#!/usr/bin/env python3
"""
Mrki AWS Lambda Handler Template
Supports API Gateway, S3, SQS, SNS, EventBridge triggers
"""

import json
import logging
import os
from typing import Any, Dict
import boto3

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
sqs_client = boto3.client('sqs')
sns_client = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')

# Environment variables
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
DB_HOST = os.environ.get('DB_HOST', '')
REDIS_HOST = os.environ.get('REDIS_HOST', '')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler function
    
    Args:
        event: The event dict from the trigger
        context: Lambda context object
    
    Returns:
        Response dict
    """
    logger.info(f"Received event: {json.dumps(event)}")
    logger.info(f"Lambda context: {context.function_name}")
    
    try:
        # Determine event source and route accordingly
        if 'httpMethod' in event or 'requestContext' in event:
            return handle_api_gateway(event, context)
        elif 'Records' in event:
            record = event['Records'][0]
            if 's3' in record:
                return handle_s3_event(event, context)
            elif 'Sns' in record:
                return handle_sns_event(event, context)
            elif 'eventSource' in record and 'sqs' in record['eventSource']:
                return handle_sqs_event(event, context)
        elif 'source' in event and event['source'] == 'aws.events':
            return handle_scheduled_event(event, context)
        else:
            return handle_custom_event(event, context)
            
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def handle_api_gateway(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle API Gateway events"""
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '/')
    query_params = event.get('queryStringParameters', {}) or {}
    body = json.loads(event.get('body', '{}')) if event.get('body') else {}
    
    logger.info(f"API Gateway request: {http_method} {path}")
    
    # Route to appropriate handler
    if path == '/health':
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'status': 'healthy',
                'environment': ENVIRONMENT,
                'version': '1.0.0'
            })
        }
    
    elif path == '/process':
        result = process_data(body)
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
    
    elif path.startswith('/webhook/'):
        service = path.split('/')[-1]
        return handle_webhook(service, body)
    
    else:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Not found'})
        }


def handle_s3_event(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle S3 trigger events"""
    for record in event.get('Records', []):
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        logger.info(f"S3 event: {bucket}/{key}")
        
        # Process the file
        try:
            response = s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read()
            
            # Process based on file type
            if key.endswith('.json'):
                data = json.loads(content)
                process_json_file(data, bucket, key)
            elif key.endswith('.csv'):
                process_csv_file(content, bucket, key)
            else:
                process_generic_file(content, bucket, key)
                
        except Exception as e:
            logger.error(f"Error processing S3 object {bucket}/{key}: {str(e)}")
            raise
    
    return {'statusCode': 200, 'body': 'S3 event processed'}


def handle_sqs_event(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle SQS trigger events"""
    for record in event.get('Records', []):
        message_id = record['messageId']
        body = json.loads(record['body'])
        
        logger.info(f"SQS message: {message_id}")
        
        try:
            # Process the message
            process_message(body)
            
        except Exception as e:
            logger.error(f"Error processing SQS message {message_id}: {str(e)}")
            # Don't raise - let the message be deleted if partial failure handling is enabled
    
    return {'statusCode': 200, 'body': 'SQS event processed'}


def handle_sns_event(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle SNS trigger events"""
    for record in event.get('Records', []):
        sns_data = record['Sns']
        message_id = sns_data['MessageId']
        message = json.loads(sns_data['Message'])
        subject = sns_data.get('Subject', '')
        
        logger.info(f"SNS message: {message_id} - {subject}")
        
        try:
            # Process the notification
            process_notification(message, subject)
            
        except Exception as e:
            logger.error(f"Error processing SNS message {message_id}: {str(e)}")
            raise
    
    return {'statusCode': 200, 'body': 'SNS event processed'}


def handle_scheduled_event(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle EventBridge scheduled events"""
    logger.info(f"Scheduled event: {event.get('detail-type', 'Unknown')}")
    
    # Perform scheduled tasks
    try:
        run_scheduled_tasks()
        return {'statusCode': 200, 'body': 'Scheduled tasks completed'}
    except Exception as e:
        logger.error(f"Error running scheduled tasks: {str(e)}")
        raise


def handle_custom_event(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Handle custom events"""
    logger.info("Processing custom event")
    
    result = process_data(event)
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }


def handle_webhook(service: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle webhook events from external services"""
    logger.info(f"Webhook from {service}")
    
    if service == 'stripe':
        return handle_stripe_webhook(payload)
    elif service == 'github':
        return handle_github_webhook(payload)
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Unknown webhook service: {service}'})
        }


def handle_stripe_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Stripe webhook events"""
    event_type = payload.get('type')
    
    if event_type == 'payment_intent.succeeded':
        # Handle successful payment
        pass
    elif event_type == 'payment_intent.payment_failed':
        # Handle failed payment
        pass
    
    return {'statusCode': 200, 'body': 'Webhook processed'}


def handle_github_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle GitHub webhook events"""
    event_type = payload.get('action')
    
    # Process GitHub events
    
    return {'statusCode': 200, 'body': 'Webhook processed'}


def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process data and return result"""
    # Implement your data processing logic here
    return {
        'status': 'success',
        'processed': True,
        'data': data
    }


def process_message(message: Dict[str, Any]) -> None:
    """Process an SQS message"""
    # Implement your message processing logic here
    logger.info(f"Processing message: {message}")


def process_notification(message: Dict[str, Any], subject: str) -> None:
    """Process an SNS notification"""
    # Implement your notification processing logic here
    logger.info(f"Processing notification: {subject}")


def process_json_file(data: Dict[str, Any], bucket: str, key: str) -> None:
    """Process a JSON file from S3"""
    logger.info(f"Processing JSON file: {bucket}/{key}")
    # Implement JSON processing logic


def process_csv_file(content: bytes, bucket: str, key: str) -> None:
    """Process a CSV file from S3"""
    logger.info(f"Processing CSV file: {bucket}/{key}")
    # Implement CSV processing logic


def process_generic_file(content: bytes, bucket: str, key: str) -> None:
    """Process a generic file from S3"""
    logger.info(f"Processing generic file: {bucket}/{key}")
    # Implement generic file processing logic


def run_scheduled_tasks() -> None:
    """Run scheduled maintenance tasks"""
    logger.info("Running scheduled tasks")
    
    # Implement scheduled task logic
    # - Cleanup old data
    # - Generate reports
    # - Sync data between systems
    # - Health checks
    
    logger.info("Scheduled tasks completed")


# For local testing
if __name__ == '__main__':
    # Test event
    test_event = {
        'httpMethod': 'GET',
        'path': '/health',
        'queryStringParameters': {},
        'body': None
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
