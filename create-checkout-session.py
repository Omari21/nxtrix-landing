import json
import os
import stripe

def handler(event, context):
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': 'https://nxtrix.com',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Credentials': 'true'
    }
    
    # Handle preflight OPTIONS request
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        # Initialize Stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        # Parse request data
        data = json.loads(event['body'])
        payment_method_id = data.get('payment_method_id')
        customer_id = data.get('customer_id')
        price_id = data.get('price_id')
        
        # Attach payment method to customer
        stripe.PaymentMethod.attach(
            payment_method_id,
            customer=customer_id
        )
        
        # Set as default payment method
        stripe.Customer.modify(
            customer_id,
            invoice_settings={'default_payment_method': payment_method_id}
        )
        
        # Create subscription (will be activated on launch day)
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{'price': price_id}],
            trial_end=1735689600,  # January 1, 2025 (launch day)
            expand=['latest_invoice.payment_intent']
        )
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'subscription_id': subscription.id,
                'status': subscription.status
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
