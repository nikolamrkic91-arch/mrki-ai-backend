"""
Mrki Azure Functions Template
Supports HTTP, Queue, Blob, Timer, Event Grid triggers
"""

import azure.functions as func
import logging
import json
import os
from typing import Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
STORAGE_CONNECTION = os.environ.get('AzureWebJobsStorage', '')

# Initialize Function App
app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


# =============================================================================
# HTTP Trigger Functions
# =============================================================================
@app.function_name(name="HttpHealth")
@app.route(route="health", methods=["GET"])
def http_health(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint"""
    logger.info('Health check request received')
    
    return func.HttpResponse(
        json.dumps({
            'status': 'healthy',
            'environment': ENVIRONMENT,
            'timestamp': datetime.utcnow().isoformat()
        }),
        status_code=200,
        mimetype='application/json'
    )


@app.function_name(name="HttpProcess")
@app.route(route="process", methods=["POST"])
def http_process(req: func.HttpRequest) -> func.HttpResponse:
    """Process data endpoint"""
    logger.info('Process request received')
    
    try:
        # Parse request body
        body = req.get_json()
        logger.info(f'Request body: {body}')
        
        # Process the data
        result = process_data(body)
        
        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f'Error processing request: {str(e)}')
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            status_code=500,
            mimetype='application/json'
        )


@app.function_name(name="HttpWebhook")
@app.route(route="webhook/{service}", methods=["POST"])
def http_webhook(req: func.HttpRequest) -> func.HttpResponse:
    """Webhook endpoint for external services"""
    service = req.route_params.get('service')
    logger.info(f'Webhook received from {service}')
    
    try:
        body = req.get_json()
        
        if service == 'stripe':
            result = handle_stripe_webhook(body)
        elif service == 'github':
            result = handle_github_webhook(body)
        else:
            return func.HttpResponse(
                json.dumps({'error': f'Unknown service: {service}'}),
                status_code=400,
                mimetype='application/json'
            )
        
        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            mimetype='application/json'
        )
        
    except Exception as e:
        logger.error(f'Error handling webhook: {str(e)}')
        return func.HttpResponse(
            json.dumps({'error': str(e)}),
            status_code=500,
            mimetype='application/json'
        )


# =============================================================================
# Queue Trigger Functions
# =============================================================================
@app.function_name(name="QueueProcessor")
@app.queue_trigger(arg_name="msg", queue_name="mrki-events", connection="AzureWebJobsStorage")
def queue_processor(msg: func.QueueMessage) -> None:
    """Process messages from the queue"""
    logger.info(f'Queue message received: {msg.id}')
    
    try:
        # Parse message
        message_body = msg.get_body().decode('utf-8')
        payload = json.loads(message_body)
        
        logger.info(f'Message payload: {payload}')
        
        # Process the message
        process_message(payload)
        
        logger.info('Message processed successfully')
        
    except Exception as e:
        logger.error(f'Error processing queue message: {str(e)}')
        raise  # Re-raise to trigger retry


@app.function_name(name="QueuePoison")
@app.queue_trigger(arg_name="msg", queue_name="mrki-events-poison", connection="AzureWebJobsStorage")
def queue_poison(msg: func.QueueMessage) -> None:
    """Handle poison queue messages (failed after max retries)"""
    logger.error(f'Poison message received: {msg.id}')
    
    # Log the failed message for manual investigation
    message_body = msg.get_body().decode('utf-8')
    logger.error(f'Poison message content: {message_body}')
    
    # Optionally: Send alert, save to dead letter table, etc.


# =============================================================================
# Blob Trigger Functions
# =============================================================================
@app.function_name(name="BlobProcessor")
@app.blob_trigger(arg_name="blob", path="mrki-data/{name}", connection="AzureWebJobsStorage")
def blob_processor(blob: func.InputStream) -> None:
    """Process uploaded files"""
    logger.info(f'Blob uploaded: {blob.name}')
    
    try:
        # Read blob content
        content = blob.read()
        
        logger.info(f'Blob size: {len(content)} bytes')
        
        # Process based on file type
        if blob.name.endswith('.json'):
            process_json_file(content, blob.name)
        elif blob.name.endswith('.csv'):
            process_csv_file(content, blob.name)
        else:
            process_generic_file(content, blob.name)
        
        logger.info('Blob processed successfully')
        
    except Exception as e:
        logger.error(f'Error processing blob: {str(e)}')
        raise


# =============================================================================
# Timer Trigger Functions
# =============================================================================
@app.function_name(name="ScheduledTask")
@app.timer_trigger(schedule="0 */5 * * * *", arg_name="timer")
def scheduled_task(timer: func.TimerRequest) -> None:
    """Run scheduled tasks every 5 minutes"""
    logger.info('Scheduled task triggered')
    
    try:
        if timer.past_due:
            logger.warning('Timer is past due')
        
        # Run scheduled tasks
        run_scheduled_tasks()
        
        logger.info('Scheduled tasks completed')
        
    except Exception as e:
        logger.error(f'Error running scheduled tasks: {str(e)}')
        raise


@app.function_name(name="DailyCleanup")
@app.timer_trigger(schedule="0 0 3 * * *", arg_name="timer")
def daily_cleanup(timer: func.TimerRequest) -> None:
    """Run daily cleanup tasks at 3 AM"""
    logger.info('Daily cleanup task triggered')
    
    try:
        # Run cleanup tasks
        cleanup_old_data()
        
        logger.info('Daily cleanup completed')
        
    except Exception as e:
        logger.error(f'Error running daily cleanup: {str(e)}')
        raise


# =============================================================================
# Event Grid Trigger Functions
# =============================================================================
@app.function_name(name="EventGridHandler")
@app.event_grid_trigger(arg_name="event")
def event_grid_handler(event: func.EventGridEvent) -> None:
    """Handle Event Grid events"""
    logger.info(f'Event Grid event received: {event.id}')
    
    try:
        logger.info(f'Event type: {event.event_type}')
        logger.info(f'Event data: {event.get_json()}')
        
        # Process the event based on type
        process_event_grid_event(event)
        
        logger.info('Event processed successfully')
        
    except Exception as e:
        logger.error(f'Error processing Event Grid event: {str(e)}')
        raise


# =============================================================================
# Helper Functions
# =============================================================================

def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process data and return result"""
    logger.info(f'Processing data: {data}')
    
    # Implement your data processing logic
    return {
        'status': 'success',
        'processed': True,
        'timestamp': datetime.utcnow().isoformat(),
        'data': data
    }


def process_message(payload: Dict[str, Any]) -> None:
    """Process a queue message"""
    logger.info(f'Processing message: {payload}')
    
    # Implement your message processing logic
    # Example: Save to database, call external API, etc.


def process_json_file(content: bytes, filename: str) -> None:
    """Process a JSON file"""
    logger.info(f'Processing JSON file: {filename}')
    
    try:
        data = json.loads(content)
        logger.info(f'JSON data: {data}')
        
        # Implement JSON processing logic
        
    except json.JSONDecodeError as e:
        logger.error(f'Invalid JSON in file {filename}: {str(e)}')
        raise


def process_csv_file(content: bytes, filename: str) -> None:
    """Process a CSV file"""
    logger.info(f'Processing CSV file: {filename}')
    
    # Implement CSV processing logic
    # Example: Parse CSV, validate data, save to database


def process_generic_file(content: bytes, filename: str) -> None:
    """Process a generic file"""
    logger.info(f'Processing generic file: {filename}')
    
    # Implement generic file processing logic


def process_event_grid_event(event: func.EventGridEvent) -> None:
    """Process Event Grid events"""
    event_type = event.event_type
    
    if 'Microsoft.Storage.BlobCreated' in event_type:
        logger.info('Blob created event')
        # Handle blob creation
        
    elif 'Microsoft.Storage.BlobDeleted' in event_type:
        logger.info('Blob deleted event')
        # Handle blob deletion
        
    else:
        logger.info(f'Unhandled event type: {event_type}')


def run_scheduled_tasks() -> None:
    """Run scheduled maintenance tasks"""
    logger.info('Running scheduled tasks')
    
    # Implement scheduled task logic
    # Examples:
    # - Health checks
    # - Data synchronization
    # - Report generation
    # - Cache warming


def cleanup_old_data() -> None:
    """Clean up old data"""
    logger.info('Cleaning up old data')
    
    # Implement cleanup logic
    # Examples:
    # - Delete old log files
    # - Archive old data
    # - Clean up temporary files


def handle_stripe_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Stripe webhook events"""
    event_type = payload.get('type')
    
    logger.info(f'Stripe event: {event_type}')
    
    if event_type == 'payment_intent.succeeded':
        # Handle successful payment
        logger.info(f'Payment succeeded: {payload.get("data", {}).get("object", {}).get("id")}')
        
    elif event_type == 'payment_intent.payment_failed':
        # Handle failed payment
        logger.info(f'Payment failed: {payload.get("data", {}).get("object", {}).get("id")}')
        
    return {'received': True}


def handle_github_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle GitHub webhook events"""
    event_type = payload.get('action')
    
    logger.info(f'GitHub event: {event_type}')
    
    # Implement GitHub webhook handling
    
    return {'received': True}


# For local testing
if __name__ == '__main__':
    # Test the functions locally
    print("Azure Functions app loaded successfully")
