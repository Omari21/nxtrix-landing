# NxTrix CRM

A modern real estate investment management platform built with Streamlit and Supabase, featuring AI-powered tools, advanced deal analysis, and comprehensive pipeline management.

## 🚀 Key Features

- **🏠 Advanced Lead Management**: Track seller and buyer leads with intelligent scoring
- **💰 Deal Analysis Engine**: Comprehensive ROI calculations with 15+ investment metrics
- **🏗️ Visual Pipeline Management**: Drag-and-drop deal tracking through stages
- **🤖 AI-Powered Tools**: Email automation, sentiment analysis, and smart matching
- **📊 Real-time Analytics**: Interactive dashboards with performance insights
- **🎯 Onboarding Wizard**: Guided setup with sample data and feature walkthrough
- **📱 PWA Support**: Mobile app experience with offline capabilities
- **🔐 Secure Authentication**: Enterprise-level security with Supabase

## 🎯 New User Experience

### Onboarding Wizard
New users are automatically guided through a comprehensive onboarding process:

1. **Welcome & Setup**: System overview and preference configuration
2. **Sample Data**: Pre-loaded realistic deals and buyers for immediate value demonstration
3. **Feature Walkthrough**: Interactive tour of all major capabilities
4. **Quick Start Guide**: 30-day success checklist and pro tips

### Sample Data Includes:
- **3 Seller Leads**: Complete property details with financial analysis
- **3 Buyer Leads**: Investment preferences and matching criteria
- **Pre-filled Analytics**: Meaningful metrics and performance indicators
- **Pipeline Data**: Deals in various stages showing workflow

## 🛠️ Tech Stack

- **Frontend**: Streamlit with custom components
- **Backend**: Supabase (PostgreSQL) with real-time subscriptions
- **AI Integration**: OpenAI GPT models for intelligent features
- **Authentication**: Supabase Auth with profile management
- **Analytics**: Plotly for interactive visualizations
- **Deployment**: Production-ready with PWA support

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd nexora_crm
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Copy `.env.example` to `.env` and fill in your credentials:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon key
- `OPENAI_API_KEY`: Your OpenAI API key

4. Run the application:
```bash
streamlit run app.py
```

## 📁 Project Structure

```
NxTrix CRM/
├── app.py                           # Main application with onboarding detection
├── requirements.txt                 # Python dependencies
├── .env                            # Environment configuration
│
├── pages/                          # Streamlit pages
│   ├── 1_Dashboard.py              # Performance overview and metrics
│   ├── leads.py                    # Advanced lead management
│   ├── pipeline_management.py      # Visual deal tracking
│   ├── ai_tools_hub.py            # AI-powered automation
│   ├── Analytics.py               # Business intelligence
│   ├── investor_clients.py        # Investor relationship management
│   ├── onboarding_wizard.py       # 🆕 Guided setup wizard
│   ├── quick_start_guide.py       # 🆕 Success checklist and tutorials
│   └── 11_Settings.py             # System configuration
│
├── services/                       # Core business logic
│   ├── supabase_client.py          # Database connectivity
│   ├── auth.py                     # Authentication and profiles
│   ├── deal_analyzer.py            # Financial analysis engine
│   ├── ai_tools.py                 # OpenAI integration
│   ├── pipeline_manager.py         # Deal workflow management
│   ├── notifications.py            # User feedback system
│   ├── error_handler.py            # Centralized error management
│   ├── clean_ui.py                 # Native Streamlit components
│   ├── sample_data_generator.py    # 🆕 Realistic sample data
│   ├── onboarding_analytics.py     # 🆕 Demo analytics
│   └── system_maintenance.py       # Production monitoring
│
├── assets/                         # Static resources
│   ├── logo.png                    # Brand assets
│   ├── style.css                   # Custom styling
│   └── config.md                   # Configuration docs
│
├── database_setup_*.sql            # Database migrations
├── demo_data_loader.py             # 🆕 Sample data utility
├── manifest.json                   # PWA configuration
└── sw.js                          # Service worker for PWA
```

## 🔧 Installation & Setup

1. **Clone the repository:**
```bash
git clone <your-repo-url>
cd NxTrix-CRM
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**
Create `.env` file with your credentials:
```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
OPENAI_API_KEY=your_openai_api_key
DEBUG=False
```

4. **Set up database:**
```bash
# Run database migrations
python -c "
from services.supabase_client import supabase
# Execute SQL files in order
"
```

5. **Launch the application:**
```bash
streamlit run app.py
```

## 🎯 First Time User Experience

### Automatic Onboarding
- New users are automatically detected and redirected to onboarding
- Existing users can re-run onboarding from settings
- Sample data is generated for immediate value demonstration

### Sample Data Includes:
- **Seller Leads**: 3 realistic properties with complete financial analysis
- **Buyer Leads**: 3 investor profiles with matching criteria
- **Analytics**: 6 months of performance data and trends
- **Pipeline**: Deals in various stages showing workflow

## 📊 Configuration

### Supabase Setup
1. Create a new Supabase project
2. Set up your database tables
3. Configure authentication settings
4. Get your project URL and anon key

### OpenAI Setup
1. Get an API key from OpenAI
2. Add it to your `.env` file

## Usage

1. Start the application with `streamlit run app.py`
2. Navigate to the login page
3. Create an account or sign in
4. Access the CRM features through the sidebar navigation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
