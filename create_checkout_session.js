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
    const { setup_intent_id, payment_method_id } = JSON.parse(event.body);

    if (!setup_intent_id || !payment_method_id) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ error: 'Missing setup_intent_id or payment_method_id' })
      };
    }

    // Initialize Supabase
    const supabase = createClient(
      process.env.SUPABASE_URL,
      process.env.SUPABASE_ANON_KEY
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

    // Define pricing
    const pricing = {
      'Essential': { amount: 5900, interval: 'month' }, // $59
      'Professional': { amount: 8900, interval: 'month' }, // $89
      'Enterprise': { amount: 14900, interval: 'month' } // $149
    };

    const priceData = pricing[tier];
    if (!priceData) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ error: 'Invalid tier' })
      };
    }

    // Create subscription with trial period
    const subscription = await stripe.subscriptions.create({
      customer: customer.id,
      items: [{
        price_data: {
          currency: 'usd',
          product_data: {
            name: `NXTRIX ${tier} Plan`,
            description: `${tier} subscription for NXTRIX CRM`
          },
          unit_amount: priceData.amount,
          recurring: {
            interval: priceData.interval
          }
        }
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
      body: JSON.stringify({ error: 'Internal server error' })
    };
  }
};
