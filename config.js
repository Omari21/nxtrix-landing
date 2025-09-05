/**
 * Configuration for NXTRIX Landing Page
 * Switch between development and production environments
 */

const CONFIG = {
  // Environment (development/production)
  // Change this to 'production' when deploying to Netlify
  ENVIRONMENT: 'production', // SWITCHED TO PRODUCTION FOR LIVE DEPLOYMENT
  
  // API Endpoints
  API_BASE_URL: {
    development: 'http://localhost:7000',
    production: 'https://nxtrix.com/api' // Netlify Functions API
  },
  
  // Frontend URLs (must match your actual domains)
  FRONTEND_URL: {
    development: 'http://localhost:8000',
    production: 'https://nxtrix.com' // Updated to custom domain
  },
  
  // CRM URLs (where users access the CRM after payment)
  CRM_URL: {
    development: 'http://localhost:8502',
    production: 'https://nxtrix.streamlit.app' // Updated to Streamlit Cloud deployment
  },
  
  // Stripe Configuration
  STRIPE: {
    // These will be set in the backend, but useful for reference
    publishableKey: {
      development: 'pk_test_...', // Your test key
      production: 'pk_live_...'   // Your live key (set in backend)
    }
  },
  
  // Success/Cancel URLs for Stripe
  getSuccessUrl: function() {
    const baseUrl = this.FRONTEND_URL[this.ENVIRONMENT];
    return `${baseUrl}/success.html`;
  },
  
  getCancelUrl: function() {
    const baseUrl = this.FRONTEND_URL[this.ENVIRONMENT];
    return `${baseUrl}/cancel.html`;
  },
  
  // CRM Access URL (after successful payment)
  getCrmUrl: function() {
    return this.CRM_URL[this.ENVIRONMENT];
  },
  
  // API Endpoints
  getApiUrl: function(endpoint) {
    const baseUrl = this.API_BASE_URL[this.ENVIRONMENT];
    return `${baseUrl}${endpoint}`;
  }
};

// Helper functions for the frontend
window.NXTRIX_CONFIG = CONFIG;

// Export for Node.js if needed
if (typeof module !== 'undefined' && module.exports) {
  module.exports = CONFIG;
}
