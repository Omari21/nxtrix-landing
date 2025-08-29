import json
import os
import stripe
from supabase import create_client, Client

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
        
        # Initialize Supabase
        url = os.environ.get('SUPABASE_URL')
        key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        supabase: Client = create_client(url, key)
        
        # Parse request data
        data = json.loads(event['body'])
        email = data.get('email')
        name = data.get('name', '')
        company = data.get('company', '')
        investor_type = data.get('investor_type', '')
        experience = data.get('experience', '')
        plan = data.get('plan', 'team')  # Default to team plan
        billing = data.get('billing', 'monthly')
        
        # Price mapping
        price_mapping = {
            'solo': {
                'monthly': os.environ.get('STRIPE_SOLO_MONTHLY'),
                'annual': os.environ.get('STRIPE_SOLO_ANNUAL')
            },
            'team': {
                'monthly': os.environ.get('STRIPE_TEAM_MONTHLY'),
                'annual': os.environ.get('STRIPE_TEAM_ANNUAL')
            },
            'business': {
                'monthly': os.environ.get('STRIPE_BUSINESS_MONTHLY'),
                'annual': os.environ.get('STRIPE_BUSINESS_ANNUAL')
            }
        }
        
        price_id = price_mapping.get(plan, {}).get(billing)
        if not price_id:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid plan or billing cycle'})
            }
        
        # Check for existing email
        existing = supabase.table('founder_customers').select('*').eq('email', email).execute()
        
        if existing.data:
            return {
                'statusCode': 409,
                'headers': headers,
                'body': json.dumps({'error': 'Email already registered'})
            }
        
        # Create Stripe customer
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata={
                'company': company,
                'investor_type': investor_type,
                'experience': experience
            }
        )
        
        # Create setup intent for saving payment method
        setup_intent = stripe.SetupIntent.create(
            customer=customer.id,
            payment_method_types=['card'],
            usage='off_session'
        )
        
        # Store in database
        founder_data = {
            'email': email,
            'name': name,
            'company': company,
            'investor_type': investor_type,
            'experience': experience,
            'plan': plan,
            'billing_cycle': billing,
            'stripe_customer_id': customer.id,
            'setup_intent_id': setup_intent.id,
            'status': 'pending_payment',
            'price_id': price_id
        }
        
        supabase.table('founder_customers').insert(founder_data).execute()
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'message': 'Founders spot reserved successfully!',
                'customer_id': customer.id,
                'client_secret': setup_intent.client_secret,
                'redirect_url': f'https://nxtrix.com/success.html?type=founders&tier={plan}&billing={billing}'
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
