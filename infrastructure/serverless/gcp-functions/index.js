/**
 * Mrki GCP Cloud Functions Template
 * Supports HTTP, Pub/Sub, Cloud Storage, Firestore triggers
 */

const { PubSub } = require('@google-cloud/pubsub');
const { Storage } = require('@google-cloud/storage');
const { Firestore } = require('@google-cloud/firestore');
const functions = require('@google-cloud/functions-framework');

// Initialize clients
const pubsub = new PubSub();
const storage = new Storage();
const firestore = new Firestore();

// Environment variables
const ENVIRONMENT = process.env.ENVIRONMENT || 'development';
const PROJECT_ID = process.env.GCP_PROJECT_ID || 'mrki-project';

/**
 * HTTP Cloud Function
 * Triggered by HTTP requests
 */
functions.http('mrkiHttpHandler', async (req, res) => {
  console.log('Received HTTP request:', {
    method: req.method,
    path: req.path,
    query: req.query,
    body: req.body
  });

  try {
    // Set CORS headers
    res.set('Access-Control-Allow-Origin', '*');
    res.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    // Handle preflight
    if (req.method === 'OPTIONS') {
      res.status(204).send('');
      return;
    }

    // Route requests
    const path = req.path || '/';
    
    switch (path) {
      case '/health':
        res.status(200).json({
          status: 'healthy',
          environment: ENVIRONMENT,
          timestamp: new Date().toISOString()
        });
        break;

      case '/process':
        const result = await processData(req.body);
        res.status(200).json(result);
        break;

      case '/webhook/stripe':
        const stripeResult = await handleStripeWebhook(req.body);
        res.status(200).json(stripeResult);
        break;

      default:
        res.status(404).json({ error: 'Not found' });
    }
  } catch (error) {
    console.error('Error handling request:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      message: error.message 
    });
  }
});

/**
 * Pub/Sub Cloud Function
 * Triggered by Pub/Sub messages
 */
functions.cloudEvent('mrkiPubSubHandler', async (cloudEvent) => {
  console.log('Received Pub/Sub message:', {
    id: cloudEvent.id,
    source: cloudEvent.source,
    type: cloudEvent.type
  });

  try {
    // Decode message data
    const messageData = cloudEvent.data?.message?.data;
    if (!messageData) {
      console.log('No message data');
      return;
    }

    const payload = JSON.parse(Buffer.from(messageData, 'base64').toString());
    console.log('Message payload:', payload);

    // Process the message
    await processMessage(payload);

    console.log('Message processed successfully');
  } catch (error) {
    console.error('Error processing Pub/Sub message:', error);
    throw error; // Re-throw to trigger retry
  }
});

/**
 * Cloud Storage Cloud Function
 * Triggered by file uploads
 */
functions.cloudEvent('mrkiStorageHandler', async (cloudEvent) => {
  console.log('Received Cloud Storage event:', {
    id: cloudEvent.id,
    bucket: cloudEvent.data?.bucket,
    name: cloudEvent.data?.name
  });

  try {
    const file = cloudEvent.data;
    const bucketName = file.bucket;
    const fileName = file.name;

    console.log(`Processing file: ${bucketName}/${fileName}`);

    // Process based on file type
    if (fileName.endsWith('.json')) {
      await processJsonFile(bucketName, fileName);
    } else if (fileName.endsWith('.csv')) {
      await processCsvFile(bucketName, fileName);
    } else {
      await processGenericFile(bucketName, fileName);
    }

    console.log('File processed successfully');
  } catch (error) {
    console.error('Error processing Cloud Storage event:', error);
    throw error;
  }
});

/**
 * Firestore Cloud Function
 * Triggered by Firestore document changes
 */
functions.cloudEvent('mrkiFirestoreHandler', async (cloudEvent) => {
  console.log('Received Firestore event:', {
    id: cloudEvent.id,
    document: cloudEvent.data?.value?.name
  });

  try {
    const oldValue = cloudEvent.data?.oldValue?.fields || {};
    const newValue = cloudEvent.data?.value?.fields || {};

    console.log('Document change:', {
      oldValue,
      newValue
    });

    // Process the document change
    await processDocumentChange(oldValue, newValue);

    console.log('Document change processed successfully');
  } catch (error) {
    console.error('Error processing Firestore event:', error);
    throw error;
  }
});

/**
 * Scheduled Cloud Function
 * Triggered by Cloud Scheduler
 */
functions.cloudEvent('mrkiScheduledHandler', async (cloudEvent) => {
  console.log('Received scheduled event:', {
    id: cloudEvent.id,
    timestamp: new Date().toISOString()
  });

  try {
    // Run scheduled tasks
    await runScheduledTasks();

    console.log('Scheduled tasks completed successfully');
  } catch (error) {
    console.error('Error running scheduled tasks:', error);
    throw error;
  }
});

// =============================================================================
// Helper Functions
// =============================================================================

async function processData(data) {
  console.log('Processing data:', data);
  
  // Implement your data processing logic
  return {
    status: 'success',
    processed: true,
    timestamp: new Date().toISOString(),
    data
  };
}

async function processMessage(message) {
  console.log('Processing message:', message);
  
  // Implement your message processing logic
  // Example: Save to Firestore
  const docRef = firestore.collection('messages').doc();
  await docRef.set({
    ...message,
    processedAt: Firestore.FieldValue.serverTimestamp()
  });
}

async function processJsonFile(bucketName, fileName) {
  console.log(`Processing JSON file: ${bucketName}/${fileName}`);
  
  // Download and parse JSON file
  const [content] = await storage.bucket(bucketName).file(fileName).download();
  const data = JSON.parse(content.toString());
  
  // Process the data
  console.log('JSON data:', data);
}

async function processCsvFile(bucketName, fileName) {
  console.log(`Processing CSV file: ${bucketName}/${fileName}`);
  
  // Download and process CSV file
  const [content] = await storage.bucket(bucketName).file(fileName).download();
  
  // Process the CSV data
  console.log('CSV content length:', content.length);
}

async function processGenericFile(bucketName, fileName) {
  console.log(`Processing generic file: ${bucketName}/${fileName}`);
  
  // Get file metadata
  const [metadata] = await storage.bucket(bucketName).file(fileName).getMetadata();
  console.log('File metadata:', metadata);
}

async function processDocumentChange(oldValue, newValue) {
  console.log('Processing document change');
  
  // Implement your document change processing logic
  // Example: Send notification, update related documents, etc.
}

async function runScheduledTasks() {
  console.log('Running scheduled tasks');
  
  // Implement your scheduled task logic
  // Examples:
  // - Cleanup old data
  // - Generate reports
  // - Sync data between systems
  // - Send notifications
  
  // Example: Cleanup old Firestore documents
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - 30);
  
  const oldDocs = await firestore
    .collection('events')
    .where('timestamp', '<', cutoffDate)
    .limit(100)
    .get();
  
  const batch = firestore.batch();
  oldDocs.docs.forEach(doc => {
    batch.delete(doc.ref);
  });
  
  await batch.commit();
  console.log(`Cleaned up ${oldDocs.size} old documents`);
}

async function handleStripeWebhook(payload) {
  console.log('Handling Stripe webhook:', payload);
  
  const eventType = payload.type;
  
  switch (eventType) {
    case 'payment_intent.succeeded':
      // Handle successful payment
      console.log('Payment succeeded:', payload.data.object.id);
      break;
      
    case 'payment_intent.payment_failed':
      // Handle failed payment
      console.log('Payment failed:', payload.data.object.id);
      break;
      
    default:
      console.log('Unhandled event type:', eventType);
  }
  
  return { received: true };
}

// Export for testing
module.exports = {
  processData,
  processMessage,
  processJsonFile,
  processCsvFile,
  processGenericFile,
  processDocumentChange,
  runScheduledTasks,
  handleStripeWebhook
};
