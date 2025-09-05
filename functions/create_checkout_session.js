const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);
const { createClient } = require('@supabase/supabase-js');

exports.handler = async (event, context) => {
  // CORS headers
  const headers = {
    'Access-Control-Allow-Origin': 'https://nxtrix.com',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Credentials': 'true',
    'Content-Type': 'application/json'
  };

  // Handle preflight OPTIONS request
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers,
      body: ''
    };
  }

  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers,
      body: JSON.stringify({ error: 'Method not allowed' })
    };
  }

  try {
    // Handle both flow types: setup intent flow and direct checkout flow
    const requestData = JSON.parse(event.body);
    
    // Check if this is the direct checkout flow (from frontend)
    if (requestData.customer_email && requestData.tier) {
      const { 
        customer_email, 
        customer_name, 
        tier, 
        billing, 
        success_url, 
        cancel_url 
      } = requestData;

      // Create a unique Stripe customer for this user to ensure data isolation
      const customer = await stripe.customers.create({
        email: customer_email,
        name: customer_name || '',
        metadata: {
          tier,
          billing: billing || 'monthly',
          flow: 'founders_signup',
          signup_timestamp: new Date().toISOString()
        }
      });

      // Create Stripe Checkout Session for subscription setup with isolated customer
      const session = await stripe.checkout.sessions.create({
        mode: 'setup',
        currency: 'usd',
        customer: customer.id,  // Use specific customer ID instead of just email
        payment_method_types: ['card'], // ONLY allow credit/debit cards
        success_url: success_url,
        cancel_url: cancel_url,
        metadata: {
          customer_email,
          customer_name: customer_name || '',
          tier,
          billing: billing || 'monthly',
          flow: 'founders_signup',
          stripe_customer_id: customer.id
        }
      });

      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
          url: session.url,
          session_id: session.id,
          customer_id: customer.id,
          message: 'Checkout session created successfully with isolated customer'
        })
      };
    }
    
    // Original setup intent flow (for webhook processing)
    const { setup_intent_id, payment_method_id } = requestData;

    if (!setup_intent_id || !payment_method_id) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ error: 'Missing required parameters for setup intent flow' })
      };
    }

    // Initialize Supabase
    const supabase = createClient(
      process.env.SUPABASE_URL,
      process.env.SUPABASE_SERVICE_ROLE_KEY
    );

    // Get user details from setup intent
    const setupIntent = await stripe.setupIntents.retrieve(setup_intent_id);
    const { email, name, tier } = setupIntent.metadata;

    // Create Stripe customer
    const customer = await stripe.customers.create({
      email: email,
      name: name,
      metadata: { tier: tier }
    });

    // Attach payment method to customer
    await stripe.paymentMethods.attach(payment_method_id, {
      customer: customer.id
    });

    // Set as default payment method
    await stripe.customers.update(customer.id, {
      invoice_settings: {
        default_payment_method: payment_method_id
      }
    });

    // Define your live Stripe Price IDs
    const PRICE_IDS = {
      // Founders Monthly Pricing
      'solo_monthly_founders': 'price_1S3keCQKteQzHnR4M4Lleuno',    // $59/month
      'team_monthly_founders': 'price_1S3kiMQKteQzHnR4psOrdYPz',    // $89/month
      'business_monthly_founders': 'price_1S3kjfQKteQzHnR47U9ojgC6', // $149/month
      
      // Founders Annual Pricing
      'solo_annual_founders': 'price_1S3kpeQKteQzHnR4wFLbvoXa',     // $708/year
      'team_annual_founders': 'price_1S3kr9QKteQzHnR4RrUnGLxe',     // $1068/year
      'business_annual_founders': 'price_1S3ks4QKteQzHnR402bRiT3h', // $1788/year
      
      // Regular Monthly Pricing
      'solo_monthly_regular': 'price_1S3kl2QKteQzHnR4hmhwybas',     // $79/month
      'team_monthly_regular': 'price_1S3kmzQKteQzHnR43ljQQHhe',     // $119/month
      'business_monthly_regular': 'price_1S3koBQKteQzHnR4f49cvae1', // $219/month
      
      // Regular Annual Pricing
      'solo_annual_regular': 'price_1S3ktIQKteQzHnR4HCA0Rzry',      // $948/year
      'team_annual_regular': 'price_1S3kuVQKteQzHnR4VbfOBg20',      // $1428/year
      'business_annual_regular': 'price_1S3kvRQKteQzHnR4hUGGCx3o'   // $2628/year
    };

    // Get the correct price ID based on tier and billing
    const priceKey = `${tier}_${billing}_founders`; // Default to founders pricing
    const priceId = PRICE_IDS[priceKey];
    
    if (!priceId) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ error: `Invalid tier/billing combination: ${priceKey}` })
      };
    }

    // Create subscription with trial period
    const subscription = await stripe.subscriptions.create({
      customer: customer.id,
      items: [{
        price: priceId  // Use the actual Stripe Price ID
      }],
      payment_behavior: 'default_incomplete',
      trial_end: Math.floor(Date.now() / 1000) + (30 * 24 * 60 * 60), // 30 days trial
      expand: ['latest_invoice.payment_intent']
    });

    // Update Supabase record
    const { error: updateError } = await supabase
      .from('founder_customers')
      .update({
        stripe_customer_id: customer.id,
        subscription_id: subscription.id,
        payment_method_id: payment_method_id,
        payment_status: 'trial',
        trial_end: new Date(Date.now() + (30 * 24 * 60 * 60 * 1000)).toISOString()
      })
      .eq('setup_intent_id', setup_intent_id);

    if (updateError) {
      console.error('Supabase update error:', updateError);
      return {
        statusCode: 500,
        headers,
        body: JSON.stringify({ error: 'Database update error' })
      };
    }

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        message: 'Subscription created successfully',
        customer_id: customer.id,
        subscription_id: subscription.id,
        trial_end: new Date(Date.now() + (30 * 24 * 60 * 60 * 1000)).toISOString()
      })
    };

  } catch (error) {
    console.error('Function error:', error);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ 
        error: 'Internal server error',
        details: error.message,
        stack: error.stack,
        timestamp: new Date().toISOString()
      })
    };
  }
};
