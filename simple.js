exports.handler = async (event, context) => {
  // Simple CORS headers
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Content-Type': 'application/json'
  };

  // Handle OPTIONS preflight
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers: headers,
      body: ''
    };
  }

  // Simple response
  return {
    statusCode: 200,
    headers: headers,
    body: JSON.stringify({
      message: 'SIMPLE FUNCTION WORKS!',
      method: event.httpMethod,
      time: new Date().toISOString()
    })
  };
};
