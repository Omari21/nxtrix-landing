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
    // Parse request body
    const requestData = JSON.parse(event.body);
    
    // Extract required fields
    const { email, name, tier } = requestData;

    // Validate required fields
    if (!email || !name || !tier) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ 
          error: 'FRESH FUNCTION: Missing required fields',
          received: { email, name, tier },
          allData: requestData
        })
      };
    }

    // Initialize Supabase with SERVICE_ROLE_KEY
    const supabase = createClient(
      process.env.SUPABASE_URL,
      process.env.SUPABASE_SERVICE_ROLE_KEY
    );

    // Check if user already exists
    const { data: existingUser } = await supabase
      .from('founder_customers')
      .select('*')
      .eq('email', email)
      .single();

    if (existingUser) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({ error: 'Email already registered' })
      };
    }

    // Create Stripe setup intent
    const setupIntent = await stripe.setupIntents.create({
      customer: undefined,
      payment_method_types: ['card'],
      usage: 'off_session',
      metadata: { email, name, tier }
    });

    // Save to Supabase
    const { data, error } = await supabase
      .from('founder_customers')
      .insert([{
        email: email,
        name: name,
        tier: tier,
        setup_intent_id: setupIntent.id,
        payment_status: 'pending',
        created_at: new Date().toISOString()
      }]);

    if (error) {
      return {
        statusCode: 500,
        headers,
        body: JSON.stringify({ error: 'Database error', details: error.message })
      };
    }

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        client_secret: setupIntent.client_secret,
        setup_intent_id: setupIntent.id,
        message: 'FRESH FUNCTION SUCCESS: Founder signup completed!'
      })
    };

  } catch (error) {
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ 
        error: 'FRESH FUNCTION ERROR', 
        details: error.message 
      })
    };
  }
};
