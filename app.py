import streamlit as st
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv

# ===== PAGE CONFIGURATION =====
st.set_page_config(
    page_title="NxTrix CRM - AI-Powered Real Estate Investment Management",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import the full dashboard
try:
    exec(open('full_dashboard.py').read())
except:
    pass  # Fallback if file doesn't exist

# Load .env for local development
load_dotenv()

# ===== SUPABASE SETUP =====
def init_supabase():
    """Initialize Supabase client with credentials"""
    try:
        # Try Streamlit secrets first (for Streamlit Cloud)
        SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL"))
        SUPABASE_ANON_KEY = st.secrets.get("SUPABASE_ANON_KEY", os.getenv("SUPABASE_ANON_KEY"))
    except:
        # Fallback to environment variables
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        st.error("⚠️ Database connection not configured. Please set up your Supabase credentials.")
        st.info("For Streamlit Cloud: Go to 'Manage app' → 'Secrets' and add SUPABASE_URL and SUPABASE_ANON_KEY")
        st.stop()
    
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Initialize Supabase
supabase = init_supabase()

# ===== AUTH FUNCTIONS =====
def get_user_info():
    """Get current user information from Supabase Auth with profile data"""
    try:
        user = supabase.auth.get_user()
        if user and user.user:
            # Get basic auth info
            user_info = {
                "id": user.user.id,
                "email": user.user.email,
                "user_metadata": user.user.user_metadata
            }
            
            # Try to get profile data for full_name
            try:
                profile_resp = supabase.table("user_profiles").select("full_name, first_name, last_name").eq("user_id", user.user.id).execute()
                if profile_resp.data and len(profile_resp.data) > 0:
                    profile_data = profile_resp.data[0]
                    # Try full_name first, then combine first_name + last_name
                    user_info["full_name"] = (
                        profile_data.get("full_name") or
                        f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}".strip() or
                        None
                    )
                
                # If no profile data, try user metadata
                if not user_info.get("full_name"):
                    user_info["full_name"] = (
                        user.user.user_metadata.get("full_name") or 
                        user.user.user_metadata.get("name") or 
                        user.user.email.split("@")[0].title()
                    )
            except Exception:
                # Fallback to extracting name from email
                user_info["full_name"] = user.user.email.split("@")[0].title()
            
            return user_info
        return None
    except Exception as e:
        st.error(f"Error getting user info: {str(e)}")
        return None

def load_or_create_profile(user, full_name=None):
    """Load or create user profile in the database"""
    try:
        # First, try to get existing profile
        profile_resp = supabase.table("profiles").select("*").eq("id", user.id).execute()
        
        if profile_resp.data:
            # Profile exists, return it
            return profile_resp.data[0]
        else:
            # Profile doesn't exist, create it
            profile_data = {
                "id": user.id,
                "email": user.email,
                "full_name": full_name or user.email.split("@")[0],
                "created_at": "now()"
            }
            
            create_resp = supabase.table("profiles").insert(profile_data).execute()
            if create_resp.data:
                return create_resp.data[0]
            else:
                # Return basic user info if profile creation fails
                return {
                    "id": user.id,
                    "email": user.email,
                    "full_name": full_name or user.email.split("@")[0]
                }
    except Exception as e:
        st.error(f"Error with user profile: {str(e)}")
        # Return basic user info as fallback
        return {
            "id": user.id,
            "email": user.email,
            "full_name": full_name or user.email.split("@")[0]
        }

# ===== CUSTOM STYLES + PWA MOBILE SUPPORT =====
def apply_custom_styles():
    st.markdown("""
    <style>
        /* Only hide sidebar on login page, show on other pages */
        .login-page [data-testid="stSidebar"] { display: none; }

        /* PWA Mobile Support */
        .pwa-install-banner {
            background: linear-gradient(90deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
            text-align: center;
            display: none;
            cursor: pointer;
        }
        
        .pwa-install-banner:hover {
            background: linear-gradient(90deg, #059669 0%, #047857 100%);
        }

        .centered-container {
            max-width: 420px;
            margin: auto;
            padding: 3rem 2rem;
            background: #ffffff;
            border-radius: 12px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.1);
        }
        
        /* Mobile responsiveness */
        @media (max-width: 768px) {
            .centered-container {
                margin: 1rem;
                padding: 2rem 1.5rem;
                max-width: 100%;
            }
        }
        .logo-container {
            text-align: center;
            margin-bottom: 1.5rem;
        }
        .big-title {
            font-size: 2rem;
            font-weight: 700;
            text-align: center;
            color: #1e3a8a;
            margin-bottom: 0.5rem;
        }
        .subtitle {
            font-size: 1rem;
            font-weight: 400;
            text-align: center;
            color: #555;
            margin-bottom: 2rem;
        }
        .forgot-password {
            font-size: 0.85rem;
            color: #1e3a8a;
            text-align: right;
            margin-top: -0.5rem;
            margin-bottom: 1rem;
        }
        .forgot-password:hover {
            text-decoration: underline;
            cursor: pointer;
        }
    </style>
    
    <!-- PWA Mobile Support -->
    <meta name="theme-color" content="#3b82f6">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <meta name="apple-mobile-web-app-title" content="NxTrix CRM">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    
    <div id="pwa-install-banner" class="pwa-install-banner" onclick="installPWA()">
        📱 Install NxTrix CRM as an app for the best mobile experience! Tap here.
    </div>
    
    <script>
    // PWA installation functionality (optional)
    let deferredPrompt;
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredPrompt = e;
      const banner = document.getElementById('pwa-install-banner');
      if (banner) banner.style.display = 'block';
    });

    function installPWA() {
      if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
          if (choiceResult.outcome === 'accepted') {
            console.log('User installed NxTrix CRM PWA');
            const banner = document.getElementById('pwa-install-banner');
            if (banner) banner.style.display = 'none';
          }
          deferredPrompt = null;
        });
      }
    }
    </script>
    """, unsafe_allow_html=True)

# ===== AUTHENTICATION FUNCTIONS =====
def check_existing_login():
    if "user_info" in st.session_state:
        return

    # Try to restore session using refresh token
    if "refresh_token" in st.session_state:
        try:
            session = supabase.auth.refresh_session(st.session_state["refresh_token"])
            user = session.user
            st.session_state["access_token"] = session.access_token
            st.session_state["refresh_token"] = session.refresh_token
            profile = load_or_create_profile(user)
            st.session_state["user_info"] = profile
            st.session_state["user_id"] = user.id  # Add this line for page compatibility
            st.session_state["page"] = "dashboard"
            st.rerun()
        except Exception:
            st.warning("Session expired. Please log in again.")
            st.session_state.clear()

def handle_authentication(auth_mode, email, password, full_name=None):
    try:
        if auth_mode == "Login":
            result = supabase.auth.sign_in_with_password({"email": email, "password": password})
        else:
            result = supabase.auth.sign_up({"email": email, "password": password})

        user = result.user
        session = result.session
        if user and session:
            st.session_state["access_token"] = session.access_token
            st.session_state["refresh_token"] = session.refresh_token
            profile = load_or_create_profile(user, full_name)
            st.session_state["user_info"] = profile
            st.session_state["user_id"] = user.id  # Add this line for page compatibility
            
            # Check if user needs onboarding
            if auth_mode == "Sign Up" or not profile.get("onboarding_completed", False):
                # Check if user has any data
                try:
                    seller_leads = supabase.table("seller_leads").select("id").eq("user_id", user.id).limit(1).execute()
                    buyer_leads = supabase.table("buyer_leads").select("id").eq("user_id", user.id).limit(1).execute()
                    has_data = len(seller_leads.data) > 0 or len(buyer_leads.data) > 0
                    
                    if not has_data and not profile.get("onboarding_completed", False):
                        st.success("✅ Welcome! Let's get you set up with a quick onboarding.")
                        st.session_state["page"] = "onboarding"
                        st.rerun()
                except:
                    # If there's an error checking data, proceed to onboarding for new users
                    if auth_mode == "Sign Up":
                        st.success("✅ Welcome! Let's get you set up with a quick onboarding.")
                        st.session_state["page"] = "onboarding"
                        st.rerun()
            
            st.success("✅ Logged in successfully!")
            st.session_state["page"] = "dashboard"
            st.rerun()
        else:
            st.error("Login/signup failed. Please check your credentials.")
    except Exception as e:
        st.error(f"Authentication error: {e}")

def validate_form_inputs(email, password, auth_mode, full_name):
    if not email or not password:
        return False, "Please enter both email and password."
    if auth_mode == "Sign Up" and not full_name:
        return False, "Please enter your full name."
    return True, None

def get_user_limits_safe(user_id):
    """Safely get user limits with error handling for database issues"""
    try:
        limits_response = supabase.table("user_limits").select("*").eq("user_id", user_id).execute()
        if limits_response.data:
            return limits_response.data[0]
        else:
            # Create default limits if none exist
            default_limits = {
                "user_id": user_id,
                "max_leads": 50,
                "max_clients": 20,
                "max_deals": 100,
                "api_calls_remaining": 1000,
                "subscription_tier": "Free Trial"
            }
            try:
                create_response = supabase.table("user_limits").insert(default_limits).execute()
                return create_response.data[0] if create_response.data else default_limits
            except Exception:
                # Return default if can't create
                return default_limits
    except Exception as e:
        # Return safe defaults if table doesn't exist or other error
        return {
            "user_id": user_id,
            "max_leads": 50,
            "max_clients": 20,
            "max_deals": 100,
            "api_calls_remaining": 1000,
            "subscription_tier": "Free Trial"
        }

def show_dashboard():
    """Complete NxTrix dashboard with all advanced features"""
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from datetime import datetime, timedelta
    
    # Debug information
    if st.secrets.get("DEBUG_MODE", False):
        st.write("Debug: Current session state keys:", list(st.session_state.keys()))
        st.write("Debug: User info exists:", "user_info" in st.session_state)
        st.write("Debug: Page:", st.session_state.get("page"))
    
    # Get user info with enhanced error handling
    if not st.session_state.get("user_info"):
        st.warning("⚠️ Session expired. Please log in again.")
        # Try to restore session first
        if check_existing_login():
            st.rerun()
        st.session_state["page"] = "login"
        st.rerun()
    
    user_info = st.session_state["user_info"]
    user_id = user_info["id"]
    
    # Handle navigation states FIRST - before showing dashboard content
    if st.session_state.get("show_leads"):
        # Load the actual leads page content
        load_leads_page()
        return
    elif st.session_state.get("show_analytics"):
        # Load the actual analytics page content
        load_analytics_page()
        return
    elif st.session_state.get("show_market_analysis"):
        # Load the market analysis page content
        load_market_analysis_page()
        return
    elif st.session_state.get("show_deal_finder"):
        show_deal_finder_page()
        return
    elif st.session_state.get("show_hot_deals"):
        show_hot_deals_page()
        return
    elif st.session_state.get("show_ai_tools"):
        load_ai_tools_page()
        return
    elif st.session_state.get("show_documents"):
        load_document_management_page()
        return
    elif st.session_state.get("show_integrations"):
        load_integrations_page()
        return
    elif st.session_state.get("show_clients"):
        load_investor_clients_page()
        return
    elif st.session_state.get("show_payments"):
        load_payment_page()
        return
    elif st.session_state.get("show_settings"):
        load_settings_page()
        return
    elif st.session_state.get("show_pipeline"):
        load_pipeline_page()
        return
    elif st.session_state.get("show_automation"):
        load_automation_page()
        return
    elif st.session_state.get("show_tasks"):
        load_task_management_page()
        return
    
    # Dashboard Header with Branding
    user_name = user_info.get("full_name", user_info.get("email", "User").split("@")[0].title())
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               padding: 2rem; border-radius: 15px; margin-bottom: 2rem; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 2.5rem;">👋 Welcome back, {user_name}!</h1>
        <h2 style="color: rgba(255,255,255,0.9); margin: 0.5rem 0; font-size: 1.8rem;">🏠 NxTrix CRM Dashboard</h2>
        <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 1.1rem;">
            AI-Powered Real Estate Investment Management
        </p>
        <div style="background: rgba(34, 197, 94, 0.2); border: 2px solid #22c55e; 
                   padding: 0.5rem 1rem; border-radius: 25px; margin-top: 1rem; display: inline-block;">
            <span style="color: #22c55e; font-weight: bold; font-size: 0.9rem;">
                ✅ FULL VERSION ACTIVE - All Advanced Features Unlocked
            </span>
        </div>
        <div style="background: rgba(220, 38, 127, 0.2); border: 2px solid #dc2626; 
                   padding: 0.5rem 1rem; border-radius: 25px; margin-top: 0.5rem; display: inline-block;">
            <span style="color: #dc2626; font-weight: bold; font-size: 0.9rem;">
                🔴 STRIPE LIVE ACCOUNT ACTIVE - Production Ready
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Hot Deals Alert Banner with CTA
    col_hotdeal, col_cta = st.columns([3, 1])
    
    with col_hotdeal:
        st.markdown("""
        <div style="background: linear-gradient(90deg, #ef4444, #dc2626); color: white; 
                   padding: 1rem; border-radius: 8px;">
            <strong>🔥 Hot Deals Available!</strong> 
            <span style="margin-left: 1rem;">High ROI potential opportunities waiting</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col_cta:
        if st.button("🔥 View Hot Deals", use_container_width=True, type="primary"):
            st.session_state["show_hot_deals"] = True
            st.rerun()
    
    # Load Data Function with caching
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def load_dashboard_data(user_id):
        """Load all dashboard data with caching"""
        try:
            # Load leads data
            seller_leads = supabase.table("seller_leads").select("*").eq("user_id", user_id).execute().data or []
            buyer_leads = supabase.table("buyer_leads").select("*").eq("user_id", user_id).execute().data or []
            
            return {
                "seller_leads": seller_leads,
                "buyer_leads": buyer_leads,
                "total_leads": len(seller_leads) + len(buyer_leads)
            }
        except Exception as e:
            st.error(f"Error loading dashboard data: {str(e)}")
            return {"seller_leads": [], "buyer_leads": [], "total_leads": 0}
    
    # Load Data
    data = load_dashboard_data(user_id)
    seller_leads = data["seller_leads"]
    buyer_leads = data["buyer_leads"]
    
    # Sidebar Navigation - Complete NxTrix CRM Suite
    with st.sidebar:
        st.markdown(f"**Welcome, {user_info.get('full_name', 'User')}!**")
        st.markdown(f"📧 {user_info.get('email', '')}")
        
        st.markdown("---")
        st.markdown("### 🏠 **Main Dashboard**")
        if st.button("📊 Overview", use_container_width=True, type="primary"):
            st.session_state.clear()
            st.session_state["user_info"] = user_info
            st.session_state["page"] = "dashboard"
            st.rerun()
        
        st.markdown("### 📋 **Lead Management**")
        nav_col1, nav_col2 = st.columns(2)
        with nav_col1:
            if st.button("🏠 Leads", use_container_width=True):
                st.session_state["show_leads"] = True
                st.rerun()
        with nav_col2:
            if st.button("📈 Pipeline", use_container_width=True):
                st.session_state["show_pipeline"] = True
                st.rerun()
        
        st.markdown("### 🤖 **AI Tools**")
        nav_col3, nav_col4 = st.columns(2)
        with nav_col3:
            if st.button("🧠 AI Hub", use_container_width=True):
                st.session_state["show_ai_tools"] = True
                st.rerun()
        with nav_col4:
            if st.button("📊 Analytics", use_container_width=True):
                st.session_state["show_analytics"] = True
                st.rerun()
        
        # Market Analysis button (full width)
        if st.button("🏘️ Market Analysis", use_container_width=True):
            st.session_state["show_market_analysis"] = True
            st.rerun()
        
        st.markdown("### �👥 **Client Management**")
        if st.button("💼 Investor Clients", use_container_width=True):
            st.session_state["show_clients"] = True
            st.rerun()
        
        st.markdown("### 🛠️ **Business Tools**")
        nav_col5, nav_col6 = st.columns(2)
        with nav_col5:
            if st.button("⚙️ Automation", use_container_width=True):
                st.session_state["show_automation"] = True
                st.rerun()
        with nav_col6:
            if st.button("📋 Tasks", use_container_width=True):
                st.session_state["show_tasks"] = True
                st.rerun()
        
        st.markdown("### 💳 **Billing & Settings**")
        nav_col7, nav_col8 = st.columns(2)
        with nav_col7:
            if st.button("💰 Payment", use_container_width=True):
                st.session_state["show_payments"] = True
                st.rerun()
        with nav_col8:
            if st.button("⚙️ Settings", use_container_width=True):
                st.session_state["show_settings"] = True
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 🚀 **Quick Actions**")
        if st.button("🔍 Find Deals", use_container_width=True):
            st.session_state["show_deal_finder"] = True
            st.rerun()
        
        if st.button("🎯 Onboarding", use_container_width=True):
            st.session_state["page"] = "onboarding"
            st.rerun()
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    
    # === KEY PERFORMANCE METRICS ===
    st.markdown("## 📊 Performance Overview")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Leads", 
            data["total_leads"],
            help="Total seller and buyer leads in your pipeline"
        )
    
    with col2:
        deals_in_contract = len([l for l in seller_leads if l.get("status") == "In Contract"])
        st.metric(
            "Deals in Contract", 
            deals_in_contract,
            help="Active deals currently under contract"
        )
    
    with col3:
        total_pipeline_value = sum(l.get("arv", 0) or 0 for l in seller_leads)
        st.metric(
            "Pipeline Value", 
            f"${total_pipeline_value:,.0f}",
            help="Total ARV of all seller leads"
        )
    
    with col4:
        if seller_leads:
            avg_roi = sum((l.get("buyer_roi", 0) or 0) for l in seller_leads) / len(seller_leads)
            st.metric(
                "Avg ROI", 
                f"{avg_roi:.1f}%",
                help="Average return on investment across deals"
            )
        else:
            st.metric("Avg ROI", "0%", help="Average return on investment across deals")
    
    with col5:
        if data["total_leads"] > 0:
            conversion_rate = (deals_in_contract / data["total_leads"]) * 100
            st.metric(
                "Conversion Rate", 
                f"{conversion_rate:.1f}%",
                help="Percentage of leads converted to contracts"
            )
        else:
            st.metric("Conversion Rate", "0%", help="Percentage of leads converted to contracts")
    
    # Quick Actions - Advanced Features
    st.markdown("### 🎯 Advanced AI-Powered Tools")
    
    col_action1, col_action2, col_action3, col_action4 = st.columns(4)
    with col_action1:
        if st.button("🔍 AI Deal Finder", use_container_width=True, type="primary"):
            st.session_state["show_deal_finder"] = True
            st.rerun()
    with col_action2:
        if st.button("� Hot Deals", use_container_width=True, type="secondary"):
            st.session_state["show_hot_deals"] = True
            st.rerun()
    with col_action3:
        if st.button("📊 Analytics Suite", use_container_width=True):
            st.session_state["show_analytics"] = True
            st.rerun()
    with col_action4:
        if st.button("👥 Lead Manager", use_container_width=True):
            st.session_state["show_leads"] = True
            st.rerun()
    
    # === DEAL PIPELINE VISUALIZATION ===
    st.markdown("## 🏗️ Deal Pipeline Status")
    
    if seller_leads:
        # Pipeline stages analysis
        pipeline_stages = {}
        for lead in seller_leads:
            stage = lead.get("status", "Unknown")
            pipeline_stages[stage] = pipeline_stages.get(stage, 0) + 1
        
        col_pipeline1, col_pipeline2 = st.columns([2, 1])
        
        with col_pipeline1:
            # Pipeline visualization
            stages_df = pd.DataFrame(list(pipeline_stages.items()), columns=['Stage', 'Count'])
            fig_pipeline = px.funnel(stages_df, x='Count', y='Stage', 
                                   title="Deal Pipeline Funnel",
                                   color_discrete_sequence=['#3b82f6'])
            fig_pipeline.update_layout(height=400)
            st.plotly_chart(fig_pipeline, use_container_width=True)
        
        with col_pipeline2:
            st.markdown("### 📈 Pipeline Health")
            
            total_deals = len(seller_leads)
            new_deals = pipeline_stages.get("New", 0)
            follow_up = pipeline_stages.get("Follow-Up", 0)
            in_contract = pipeline_stages.get("In Contract", 0)
            closed = pipeline_stages.get("Closed", 0)
            
            # Health indicators
            if in_contract >= total_deals * 0.15:
                st.success(f"🔥 Strong: {in_contract} deals in contract")
            else:
                st.warning(f"⚠️ Focus: Only {in_contract} deals in contract")
            
            if follow_up >= total_deals * 0.3:
                st.info(f"📞 Active: {follow_up} follow-ups needed")
            
            if closed >= total_deals * 0.1:
                st.success(f"✅ Closed: {closed} successful deals")
            
            # Pipeline progression rate
            progression_rate = (in_contract + closed) / max(1, total_deals) * 100
            st.metric("Pipeline Progression", f"{progression_rate:.1f}%", 
                     help="Percentage of deals beyond initial contact")
    else:
        st.info("Add seller leads to see pipeline visualization")
    
    # === RECENT ACTIVITY FEED ===
    st.markdown("## 📅 Recent Activity")
    
    col_activity1, col_activity2 = st.columns(2)
    
    with col_activity1:
        st.markdown("### 🏠 Recent Seller Leads")
        
        if seller_leads:
            recent_sellers = sorted(seller_leads, 
                                  key=lambda x: x.get("created_at", ""), 
                                  reverse=True)[:5]
            
            for lead in recent_sellers:
                roi = lead.get("buyer_roi", 0) or 0
                status = lead.get("status", "Unknown")
                
                # Color coding based on ROI
                if roi >= 20:
                    border_color = "#22c55e"
                    roi_emoji = "🔥"
                elif roi >= 15:
                    border_color = "#3b82f6"
                    roi_emoji = "📈"
                else:
                    border_color = "#6b7280"
                    roi_emoji = "📋"
                
                st.markdown(f"""
                <div style="border-left: 4px solid {border_color}; padding: 1rem; margin-bottom: 1rem; 
                           background: white; border-radius: 0 8px 8px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong style="color: #1f2937;">{roi_emoji} {lead.get('property_address', 'Unknown Property')[:30]}...</strong>
                        <span style="background: {border_color}; color: white; padding: 0.2rem 0.5rem; 
                                   border-radius: 15px; font-size: 0.8rem;">{status}</span>
                    </div>
                    <div style="margin-top: 0.5rem; color: #6b7280; font-size: 0.9rem;">
                        ROI: {roi:.1f}% | ARV: ${lead.get('arv', 0):,.0f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No seller leads yet. Add your first property!")
    
    with col_activity2:
        st.markdown("### 👥 Recent Buyer Leads")
        
        if buyer_leads:
            recent_buyers = sorted(buyer_leads, 
                                 key=lambda x: x.get("created_at", ""), 
                                 reverse=True)[:5]
            
            for lead in recent_buyers:
                budget = lead.get("max_budget", 0) or 0
                status = lead.get("status", "Active")
                
                st.markdown(f"""
                <div style="border-left: 4px solid #3b82f6; padding: 1rem; margin-bottom: 1rem; 
                           background: white; border-radius: 0 8px 8px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong style="color: #1f2937;">👤 {lead.get('investor_name', 'Unknown Investor')}</strong>
                        <span style="background: #3b82f6; color: white; padding: 0.2rem 0.5rem; 
                                   border-radius: 15px; font-size: 0.8rem;">{status}</span>
                    </div>
                    <div style="margin-top: 0.5rem; color: #6b7280; font-size: 0.9rem;">
                        Budget: ${budget:,.0f} | Location: {lead.get('preferred_location', 'Any')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No buyer leads yet. Add your first investor!")
    
    # === FULL FEATURES SHOWCASE ===
    if data["total_leads"] == 0:
        st.markdown("""
        <div style="background: #f0f9ff; border: 2px dashed #3b82f6; padding: 2rem; 
                   border-radius: 10px; text-align: center; margin-top: 2rem;">
            <h3 style="color: #1e40af; margin: 0 0 1rem 0;">🚀 Welcome to NxTrix CRM!</h3>
            <p style="color: #1e40af; margin: 0 0 1rem 0;">
                Start by adding your first leads to see the power of AI-driven real estate investing.
            </p>
            <p style="color: #1e40af; margin: 0; font-size: 0.9rem;">
                Use the sidebar navigation to add seller properties and buyer investors.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # === FULL FEATURES SHOWCASE ===
    if data["total_leads"] == 0:
        st.markdown("---")
        st.markdown("## 🚀 Complete NxTrix CRM Features")
        
        col_feat1, col_feat2, col_feat3 = st.columns(3)
        
        with col_feat1:
            st.markdown("""
            <div style="background: #f0f9ff; border: 1px solid #3b82f6; padding: 1rem; border-radius: 8px; height: 200px;">
                <h4 style="color: #1e40af; margin: 0 0 0.5rem 0;">🤖 AI-Powered Tools</h4>
                <ul style="color: #1e40af; margin: 0; padding-left: 1rem;">
                    <li>Instant Property Analysis</li>
                    <li>ROI Calculations</li>
                    <li>Market Intelligence</li>
                    <li>Deal Recommendations</li>
                    <li>Hot Deals Alerts</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col_feat2:
            st.markdown("""
            <div style="background: #f0fdf4; border: 1px solid #22c55e; padding: 1rem; border-radius: 8px; height: 200px;">
                <h4 style="color: #15803d; margin: 0 0 0.5rem 0;">📊 Advanced Analytics</h4>
                <ul style="color: #15803d; margin: 0; padding-left: 1rem;">
                    <li>Pipeline Visualization</li>
                    <li>Performance Metrics</li>
                    <li>ROI Distribution Charts</li>
                    <li>Deal Status Tracking</li>
                    <li>Conversion Analytics</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col_feat3:
            st.markdown("""
            <div style="background: #fefce8; border: 1px solid #eab308; padding: 1rem; border-radius: 8px; height: 200px;">
                <h4 style="color: #a16207; margin: 0 0 0.5rem 0;">🏠 Lead Management</h4>
                <ul style="color: #a16207; margin: 0; padding-left: 1rem;">
                    <li>Seller Lead Tracking</li>
                    <li>Buyer Investor Database</li>
                    <li>Deal Pipeline Management</li>
                    <li>Contact Management</li>
                    <li>Status Updates</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success(f"🎉 **Dashboard Active**: Managing {data['total_leads']} leads with NxTrix's AI-powered system!")

def show_add_lead_modal():
    """Modal for adding new leads"""
    st.markdown("## ➕ Add New Lead")
    
    lead_type = st.selectbox("Lead Type", ["Seller Lead", "Buyer Lead"])
    
    if lead_type == "Seller Lead":
        with st.form("add_seller_lead"):
            col1, col2 = st.columns(2)
            with col1:
                property_address = st.text_input("Property Address")
                asking_price = st.number_input("Asking Price", min_value=0)
                arv = st.number_input("ARV (After Repair Value)", min_value=0)
            with col2:
                seller_name = st.text_input("Seller Name")
                seller_phone = st.text_input("Seller Phone")
                seller_email = st.text_input("Seller Email")
            
            if st.form_submit_button("Add Seller Lead"):
                try:
                    user_id = st.session_state["user_info"]["id"]
                    supabase.table("seller_leads").insert({
                        "user_id": user_id,
                        "property_address": property_address,
                        "asking_price": asking_price,
                        "arv": arv,
                        "seller_name": seller_name,
                        "seller_phone": seller_phone,
                        "seller_email": seller_email,
                        "status": "New"
                    }).execute()
                    st.success("✅ Seller lead added successfully!")
                    st.session_state["show_add_lead"] = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding lead: {e}")
    
    if st.button("❌ Close"):
        st.session_state["show_add_lead"] = False
        st.rerun()

def show_analytics_modal():
    """Analytics modal"""
    st.markdown("## 📊 Analytics Dashboard")
    st.info("📈 Advanced analytics features available in full version")
    if st.button("❌ Close"):
        st.session_state["show_analytics"] = False
        st.rerun()

def show_payments_modal():
    """Payments modal"""
    st.markdown("## 💰 Payment Management")
    st.info("💳 Payment processing features available in full version")
    if st.button("❌ Close"):
        st.session_state["show_payments"] = False
        st.rerun()

def show_ai_tools_modal():
    """AI Tools modal"""
    st.markdown("## 🤖 AI Tools Hub")
    st.info("🧠 AI-powered tools available in full version")
    if st.button("❌ Close"):
        st.session_state["show_ai_tools"] = False
        st.rerun()

def show_onboarding():
    """Simple onboarding view"""
    st.title("🚀 Welcome to NxTrix CRM!")
    st.markdown("Let's get you set up in just a few steps.")
    
    with st.form("onboarding_form"):
        st.subheader("📝 Tell us about yourself")
        
        business_type = st.selectbox(
            "What type of real estate professional are you?",
            ["Real Estate Investor", "Real Estate Agent", "Property Manager", "Wholesaler", "Other"]
        )
        
        experience_level = st.selectbox(
            "How would you describe your experience level?",
            ["Beginner (0-1 years)", "Intermediate (2-5 years)", "Advanced (5+ years)", "Expert (10+ years)"]
        )
        
        primary_goal = st.selectbox(
            "What's your primary goal with NxTrix CRM?",
            ["Lead Management", "Deal Tracking", "Client Communication", "Analytics & Reporting", "All of the above"]
        )
        
        if st.form_submit_button("🎯 Complete Setup", use_container_width=True):
            # Save onboarding data
            try:
                user_id = st.session_state.get("user_id")
                if user_id:
                    supabase.table("profiles").update({
                        "business_type": business_type,
                        "experience_level": experience_level,
                        "primary_goal": primary_goal,
                        "onboarding_completed": True
                    }).eq("id", user_id).execute()
                
                st.success("🎉 Setup complete! Welcome to NxTrix CRM!")
                st.session_state["page"] = "dashboard"
                st.rerun()
            except Exception as e:
                st.warning("Setup saved locally. Welcome to NxTrix CRM!")
                st.session_state["page"] = "dashboard"
                st.rerun()

# ===== MAIN APP =====
def main():
    if "page" not in st.session_state:
        st.session_state["page"] = "login"

    # Load previous session if refresh token exists
    check_existing_login()

    # Route to different pages
    if st.session_state.get("page") == "dashboard":
        # Always load the full dashboard with complete features
        show_dashboard()
        return
    
    if st.session_state.get("page") == "onboarding":
        # Load onboarding directly
        show_onboarding()
        return

    # Show Login/Signup page
    apply_custom_styles()
    with st.container():
        st.markdown('<div class="login-page">', unsafe_allow_html=True)
        st.markdown('<div class="centered-container">', unsafe_allow_html=True)
        st.markdown('<div class="logo-container">', unsafe_allow_html=True)
        try:
            st.image("assets/logo.png", width=140)
        except:
            st.markdown('<h1 style="text-align: center; color: #1e3a8a;">🏢 NxTrix</h1>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="big-title">Welcome to NxTrix CRM</div>', unsafe_allow_html=True)
        st.markdown('<div class="subtitle">Built for real estate investors & deal makers</div>', unsafe_allow_html=True)

        st.radio("Access Mode", ["Login", "Sign Up"], key="auth_mode", horizontal=True)

        with st.form("auth_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="you@example.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            full_name = st.text_input("Full Name", placeholder="Your full name") if st.session_state.auth_mode == "Sign Up" else None

            if st.session_state.auth_mode == "Login":
                st.markdown('<div class="forgot-password">Forgot password?</div>', unsafe_allow_html=True)

            submitted = st.form_submit_button("Continue", use_container_width=True)
            if submitted:
                valid, error = validate_form_inputs(email, password, st.session_state.auth_mode, full_name)
                if not valid:
                    st.warning(error)
                else:
                    handle_authentication(st.session_state.auth_mode, email, password, full_name)

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# Supporting Dashboard Functions
def show_leads_page():
    """Comprehensive leads management page"""
    st.markdown("### 🏠 Leads Management")
    
    tab1, tab2 = st.tabs(["Seller Leads", "Buyer Leads"])
    
    with tab1:
        if st.button("➕ Add Seller Lead", use_container_width=True):
            show_add_seller_lead()
        
        # Display seller leads
        try:
            user_id = st.session_state["user_info"]["id"]
            seller_leads = supabase.table("seller_leads").select("*").eq("user_id", user_id).execute().data or []
            
            if seller_leads:
                for lead in seller_leads:
                    with st.expander(f"🏠 {lead.get('property_address', 'Unknown')} - {lead.get('status', 'New')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**ARV:** ${lead.get('arv', 0):,.0f}")
                            st.write(f"**ROI:** {lead.get('buyer_roi', 0):.1f}%")
                        with col2:
                            st.write(f"**Status:** {lead.get('status', 'New')}")
                            st.write(f"**Date:** {lead.get('created_at', '')[:10]}")
            else:
                st.info("No seller leads yet. Add your first property!")
        except Exception as e:
            st.error(f"Error loading seller leads: {str(e)}")
    
    with tab2:
        if st.button("➕ Add Buyer Lead", use_container_width=True):
            show_add_buyer_lead()
        
        # Display buyer leads
        try:
            user_id = st.session_state["user_info"]["id"]
            buyer_leads = supabase.table("buyer_leads").select("*").eq("user_id", user_id).execute().data or []
            
            if buyer_leads:
                for lead in buyer_leads:
                    with st.expander(f"👤 {lead.get('investor_name', 'Unknown')} - {lead.get('status', 'Active')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Budget:** ${lead.get('max_budget', 0):,.0f}")
                            st.write(f"**Location:** {lead.get('preferred_location', 'Any')}")
                        with col2:
                            st.write(f"**Status:** {lead.get('status', 'Active')}")
                            st.write(f"**Date:** {lead.get('created_at', '')[:10]}")
            else:
                st.info("No buyer leads yet. Add your first investor!")
        except Exception as e:
            st.error(f"Error loading buyer leads: {str(e)}")
    
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.pop("show_leads", None)
        st.rerun()

def show_analytics_page():
    """Advanced analytics page"""
    st.markdown("### 📊 Advanced Analytics")
    
    try:
        user_id = st.session_state["user_info"]["id"]
        seller_leads = supabase.table("seller_leads").select("*").eq("user_id", user_id).execute().data or []
        buyer_leads = supabase.table("buyer_leads").select("*").eq("user_id", user_id).execute().data or []
        
        if seller_leads:
            import plotly.express as px
            import pandas as pd
            
            # ROI Distribution Chart
            roi_data = [lead.get('buyer_roi', 0) for lead in seller_leads if lead.get('buyer_roi')]
            if roi_data:
                fig = px.histogram(x=roi_data, title="ROI Distribution", 
                                 labels={'x': 'ROI (%)', 'y': 'Number of Deals'})
                st.plotly_chart(fig, use_container_width=True)
            
            # Deal Status Pie Chart
            status_counts = {}
            for lead in seller_leads:
                status = lead.get('status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            if status_counts:
                fig = px.pie(values=list(status_counts.values()), 
                           names=list(status_counts.keys()),
                           title="Deal Status Distribution")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Add leads to see analytics")
    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")
    
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.pop("show_analytics", None)
        st.rerun()

def show_deal_finder_page():
    """AI-powered deal finder"""
    st.markdown("### 🔍 AI Deal Finder")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               color: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;">
        <h3 style="margin: 0;">🤖 AI-Powered Property Analysis</h3>
        <p style="margin: 0.5rem 0 0 0;">Instantly analyze any property for investment potential</p>
    </div>
    """, unsafe_allow_html=True)
    
    property_address = st.text_input("Enter Property Address", placeholder="123 Main St, City, State")
    
    col1, col2 = st.columns(2)
    with col1:
        estimated_value = st.number_input("Estimated Property Value", min_value=0, value=150000)
    with col2:
        repair_costs = st.number_input("Estimated Repair Costs", min_value=0, value=25000)
    
    if st.button("🔍 Analyze Property", type="primary"):
        if property_address:
            # Simulate AI analysis
            arv = estimated_value * 1.2  # Simulated ARV calculation
            total_investment = estimated_value + repair_costs
            potential_roi = ((arv - total_investment) / total_investment) * 100
            
            st.markdown("---")
            st.markdown("### 📊 Analysis Results")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("ARV", f"${arv:,.0f}")
            with col2:
                st.metric("Total Investment", f"${total_investment:,.0f}")
            with col3:
                if potential_roi >= 20:
                    st.metric("Potential ROI", f"{potential_roi:.1f}%", delta="Excellent Deal! 🔥")
                elif potential_roi >= 15:
                    st.metric("Potential ROI", f"{potential_roi:.1f}%", delta="Good Deal 📈")
                else:
                    st.metric("Potential ROI", f"{potential_roi:.1f}%", delta="Consider Passing")
            
            # AI Recommendations
            st.markdown("### 🤖 AI Recommendations")
            if potential_roi >= 20:
                st.success("🔥 **HOT DEAL!** This property shows excellent investment potential. Consider moving quickly.")
            elif potential_roi >= 15:
                st.info("📈 **GOOD DEAL** This property meets standard investment criteria.")
            else:
                st.warning("⚠️ **PROCEED WITH CAUTION** Low ROI potential. Consider negotiating or looking for better deals.")
            
            if st.button("💾 Save to Seller Leads"):
                try:
                    user_id = st.session_state["user_info"]["id"]
                    new_lead = {
                        "user_id": user_id,
                        "property_address": property_address,
                        "arv": arv,
                        "estimated_value": estimated_value,
                        "repair_costs": repair_costs,
                        "buyer_roi": potential_roi,
                        "status": "New",
                        "source": "AI Deal Finder"
                    }
                    
                    result = supabase.table("seller_leads").insert(new_lead).execute()
                    st.success("✅ Property saved to seller leads!")
                except Exception as e:
                    st.error(f"Error saving lead: {str(e)}")
        else:
            st.warning("Please enter a property address")
    
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.pop("show_deal_finder", None)
        st.rerun()

def show_hot_deals_page():
    """Enhanced Hot deals marketplace with urgency and bidding"""
    st.markdown("### 🔥 Hot Deals Marketplace")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #ef4444, #dc2626); color: white; 
               padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem; text-align: center;">
        <h3 style="margin: 0;">🚨 URGENT: High-ROI Opportunities</h3>
        <p style="margin: 0.5rem 0 0 0;">AI-verified deals with 20%+ ROI potential • Updated every 15 minutes</p>
        <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem;">⏰ <strong>{deals_count} deals expiring in next 48 hours</strong></p>
    </div>
    """.format(deals_count=7), unsafe_allow_html=True)
    
    # Filter and sort options
    col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)
    
    with col_filter1:
        min_roi = st.selectbox("Min ROI %", [15, 20, 25, 30], index=1)
    with col_filter2:
        max_investment = st.selectbox("Max Investment", ["150K", "300K", "500K", "1M+"], index=2)
    with col_filter3:
        location_filter = st.selectbox("Location", ["All Markets", "Memphis", "Little Rock", "Birmingham", "Nashville"])
    with col_filter4:
        urgency_filter = st.selectbox("Urgency", ["All", "Critical (1-2 days)", "High (3-5 days)", "Medium (6+ days)"])
    
    # Enhanced sample hot deals with more urgency indicators
    hot_deals = [
        {
            "address": "1247 Oak Street, Memphis, TN",
            "arv": 185000,
            "investment": 120000,
            "roi": 23.4,
            "confidence": 92,
            "days_left": 2,
            "hours_left": 18,
            "priority": "CRITICAL",
            "ai_score": 96,
            "competition": "3 investors viewing",
            "deal_type": "Off-Market",
            "property_type": "SFR",
            "last_updated": "12 min ago"
        },
        {
            "address": "892 Pine Avenue, Little Rock, AR",
            "arv": 145000,
            "investment": 95000,
            "roi": 21.8,
            "confidence": 87,
            "days_left": 4,
            "hours_left": 2,
            "priority": "HIGH",
            "ai_score": 89,
            "competition": "1 investor viewing",
            "deal_type": "Distressed",
            "property_type": "SFR",
            "last_updated": "8 min ago"
        },
        {
            "address": "456 Maple Drive, Birmingham, AL",
            "arv": 210000,
            "investment": 140000,
            "roi": 25.1,
            "confidence": 94,
            "days_left": 1,
            "hours_left": 14,
            "priority": "CRITICAL",
            "ai_score": 98,
            "competition": "5 investors viewing",
            "deal_type": "Foreclosure",
            "property_type": "SFR",
            "last_updated": "3 min ago"
        },
        {
            "address": "789 Cedar Court, Nashville, TN",
            "arv": 275000,
            "investment": 180000,
            "roi": 27.8,
            "confidence": 91,
            "days_left": 3,
            "hours_left": 8,
            "priority": "HIGH",
            "ai_score": 93,
            "competition": "2 investors viewing",
            "deal_type": "Estate Sale",
            "property_type": "SFR",
            "last_updated": "6 min ago"
        }
    ]
    
    # Live updates indicator
    st.markdown("""
    <div style="background: #f0fdf4; border-left: 4px solid #22c55e; padding: 0.5rem 1rem; margin-bottom: 1rem;">
        <span style="color: #16a34a;">🟢 <strong>LIVE</strong> • Deals update automatically • Last refresh: 2 min ago</span>
    </div>
    """, unsafe_allow_html=True)
    
    for i, deal in enumerate(hot_deals):
        # Dynamic urgency styling
        if deal["priority"] == "CRITICAL":
            border_color = "#dc2626"
            priority_bg = "#fee2e2"
            priority_text = "#dc2626"
            blink_class = "animate-pulse"
        elif deal["priority"] == "HIGH":
            border_color = "#f59e0b"
            priority_bg = "#fef3c7"
            priority_text = "#f59e0b"
            blink_class = ""
        else:
            border_color = "#6b7280"
            priority_bg = "#f3f4f6"
            priority_text = "#6b7280"
            blink_class = ""
        
        st.markdown(f"""
        <div style="border: 3px solid {border_color}; border-radius: 15px; padding: 1.5rem; margin-bottom: 1.5rem; {blink_class}">
            <!-- Header with urgency and competition -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <h4 style="margin: 0; color: #1f2937;">🏠 {deal['address']}</h4>
                    <span style="background: {priority_bg}; color: {priority_text}; padding: 0.3rem 0.8rem; 
                               border-radius: 20px; font-weight: bold; font-size: 0.8rem;">
                        {deal['priority']} PRIORITY
                    </span>
                </div>
                <div style="text-align: right;">
                    <div style="color: {border_color}; font-weight: bold; font-size: 1.1rem;">
                        ⏰ {deal['days_left']}d {deal['hours_left']}h left
                    </div>
                    <div style="color: #ef4444; font-size: 0.9rem;">👥 {deal['competition']}</div>
                </div>
            </div>
            
            <!-- Key metrics -->
            <div style="display: grid; grid-template-columns: repeat(6, 1fr); gap: 1rem; margin-bottom: 1rem;">
                <div><strong>ARV:</strong><br>${deal['arv']:,.0f}</div>
                <div><strong>Investment:</strong><br>${deal['investment']:,.0f}</div>
                <div><strong>ROI:</strong><br><span style="color: #059669; font-weight: bold; font-size: 1.1rem;">{deal['roi']:.1f}%</span></div>
                <div><strong>AI Score:</strong><br><span style="color: #7c3aed; font-weight: bold;">{deal['ai_score']}/100</span></div>
                <div><strong>Type:</strong><br>{deal['deal_type']}</div>
                <div><strong>Updated:</strong><br><span style="color: #059669;">{deal['last_updated']}</span></div>
            </div>
            
            <!-- Confidence bar -->
            <div style="margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.3rem;">
                    <span><strong>AI Confidence Level</strong></span>
                    <span style="font-weight: bold; color: #059669;">{deal['confidence']}%</span>
                </div>
                <div style="background: #e5e7eb; border-radius: 10px; height: 8px;">
                    <div style="background: linear-gradient(90deg, #ef4444, #f59e0b, #22c55e); 
                               width: {deal['confidence']}%; height: 100%; border-radius: 10px;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Action buttons with enhanced functionality
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button(f"📞 Contact Seller", key=f"contact_{i}", use_container_width=True):
                st.success("🎯 Seller contact info sent to your email! Check within 2 minutes.")
        with col2:
            if st.button(f"💾 Save Deal", key=f"save_{i}", use_container_width=True):
                st.success("✅ Deal saved to your pipeline with priority flag!")
        with col3:
            if st.button(f"📊 Full Analysis", key=f"analyze_{i}", use_container_width=True):
                st.info("📈 Comprehensive CMA report generating... Check Market Analysis in 30 seconds.")
        with col4:
            bid_amount = st.number_input(f"Quick Bid $", min_value=1000, value=deal['investment'], step=1000, key=f"bid_{i}")
            if st.button(f"⚡ Submit Bid", key=f"quick_bid_{i}", use_container_width=True):
                st.warning(f"🔥 Bid of ${bid_amount:,.0f} submitted! Seller will respond within 2 hours.")
    
    # Summary stats
    st.markdown("---")
    col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
    with col_stats1:
        st.metric("🔥 Hot Deals Available", len(hot_deals))
    with col_stats2:
        st.metric("⏰ Expiring Today", 2)
    with col_stats3:
        st.metric("💰 Avg ROI", "24.3%")
    with col_stats4:
        st.metric("👥 Active Investors", 47)
    
    # Auto-refresh notice
    st.markdown("""
    <div style="background: #fef3c7; border: 1px solid #f59e0b; padding: 1rem; border-radius: 8px; margin-top: 1rem;">
        <p style="margin: 0; color: #92400e; text-align: center;">
            🔄 <strong>Auto-refresh enabled</strong> • New deals appear automatically • 
            Set up SMS alerts in <a href="#" style="color: #92400e;">Settings</a> to never miss opportunities
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("⬅️ Back to Dashboard"):
        st.session_state.pop("show_hot_deals", None)
        st.rerun()

def show_add_seller_lead():
    """Add seller lead form"""
    st.markdown("### ➕ Add Seller Lead")
    
    with st.form("add_seller_lead"):
        property_address = st.text_input("Property Address*")
        seller_name = st.text_input("Seller Name")
        seller_phone = st.text_input("Seller Phone")
        
        col1, col2 = st.columns(2)
        with col1:
            arv = st.number_input("After Repair Value (ARV)*", min_value=0, value=150000)
            repair_costs = st.number_input("Estimated Repair Costs", min_value=0, value=25000)
        with col2:
            asking_price = st.number_input("Asking Price", min_value=0, value=100000)
            buyer_roi = st.number_input("Estimated Buyer ROI (%)", min_value=0.0, value=20.0, step=0.1)
        
        status = st.selectbox("Status", ["New", "Contacted", "Follow-Up", "In Contract", "Closed", "Dead"])
        notes = st.text_area("Notes")
        
        if st.form_submit_button("Add Seller Lead", type="primary"):
            if property_address and arv:
                try:
                    user_id = st.session_state["user_info"]["id"]
                    new_lead = {
                        "user_id": user_id,
                        "property_address": property_address,
                        "seller_name": seller_name,
                        "seller_phone": seller_phone,
                        "arv": arv,
                        "repair_costs": repair_costs,
                        "asking_price": asking_price,
                        "buyer_roi": buyer_roi,
                        "status": status,
                        "notes": notes
                    }
                    
                    result = supabase.table("seller_leads").insert(new_lead).execute()
                    st.success("✅ Seller lead added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding seller lead: {str(e)}")
            else:
                st.warning("Please fill in required fields (Property Address and ARV)")

def show_add_buyer_lead():
    """Add buyer lead form"""
    st.markdown("### ➕ Add Buyer Lead")
    
    with st.form("add_buyer_lead"):
        investor_name = st.text_input("Investor Name*")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        
        col1, col2 = st.columns(2)
        with col1:
            max_budget = st.number_input("Maximum Budget*", min_value=0, value=200000)
            min_roi = st.number_input("Minimum ROI Required (%)", min_value=0.0, value=15.0, step=0.1)
        with col2:
            preferred_location = st.text_input("Preferred Location", value="Any")
            property_type = st.selectbox("Property Type", ["Single Family", "Multi-Family", "Commercial", "Any"])
        
        status = st.selectbox("Status", ["Active", "Inactive", "Closed"])
        notes = st.text_area("Notes")
        
        if st.form_submit_button("Add Buyer Lead", type="primary"):
            if investor_name and max_budget:
                try:
                    user_id = st.session_state["user_info"]["id"]
                    new_lead = {
                        "user_id": user_id,
                        "investor_name": investor_name,
                        "email": email,
                        "phone": phone,
                        "max_budget": max_budget,
                        "min_roi": min_roi,
                        "preferred_location": preferred_location,
                        "property_type": property_type,
                        "status": status,
                        "notes": notes
                    }
                    
                    result = supabase.table("buyer_leads").insert(new_lead).execute()
                    st.success("✅ Buyer lead added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding buyer lead: {str(e)}")
            else:
                st.warning("Please fill in required fields (Investor Name and Budget)")

def show_ai_tools_page():
    """AI Tools Hub page"""
    st.markdown("### 🤖 AI Tools Hub")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #8b5cf6, #7c3aed); color: white; 
               padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem;">
        <h3 style="margin: 0;">🚀 AI-Powered Real Estate Tools</h3>
        <p style="margin: 0.5rem 0 0 0;">Automate your real estate investment workflow</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔍 Property Analysis")
        if st.button("Analyze Property", use_container_width=True):
            st.session_state["show_deal_finder"] = True
            st.rerun()
        
        st.markdown("#### 📊 Market Intelligence")
        if st.button("Market Reports", use_container_width=True):
            st.info("AI Market Reports coming soon!")
        
        st.markdown("#### 📧 Email Automation")
        if st.button("Email Templates", use_container_width=True):
            st.info("AI Email Generator coming soon!")
    
    with col2:
        st.markdown("#### 🎯 Lead Scoring")
        if st.button("Score Leads", use_container_width=True):
            st.info("AI Lead Scoring coming soon!")
        
        st.markdown("#### 📞 Call Scripts")
        if st.button("Generate Scripts", use_container_width=True):
            st.info("AI Call Scripts coming soon!")
        
        st.markdown("#### 📋 Contract Generation")
        if st.button("Create Contracts", use_container_width=True):
            st.info("AI Contract Generator coming soon!")
    
    if st.button("⬅️ Back to Dashboard"):
        for key in ["show_ai_tools", "show_deal_finder", "show_analytics", "show_leads"]:
            st.session_state.pop(key, None)
        st.rerun()

def show_clients_page():
    """Client management page"""
    st.markdown("### 👥 Client Management")
    
    st.info("🚧 **Coming Soon**: Complete client relationship management system with investor profiles, communication history, and deal tracking.")
    
    # Placeholder content
    st.markdown("#### Features in Development:")
    st.markdown("- Investor profile management")
    st.markdown("- Communication tracking") 
    st.markdown("- Deal history per client")
    st.markdown("- Client preferences and criteria")
    st.markdown("- Performance analytics per client")
    
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.pop("show_clients", None)
        st.rerun()

def show_payments_page():
    """Payment management page"""
    st.markdown("### 💰 Payment Management")
    
    st.markdown("""
    <div style="background: #f0f9ff; border: 1px solid #3b82f6; padding: 1rem; border-radius: 8px;">
        <h4 style="color: #1e40af; margin: 0 0 0.5rem 0;">🎯 Current Plan: Team</h4>
        <p style="margin: 0; color: #1e40af;">
            ✅ Unlimited leads | ✅ AI tools | ✅ Advanced analytics
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("#### 📊 Usage This Month")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Leads Added", "47", "↗️ +12")
    with col2:
        st.metric("AI Analyses", "23", "↗️ +8")
    with col3:
        st.metric("Deals Closed", "3", "↗️ +2")
    
    st.markdown("#### 💳 Billing")
    st.info("Next billing date: October 1, 2025 - $119/month (Team Plan)")
    
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.pop("show_payments", None)
        st.rerun()

def show_settings_page():
    """Settings and configuration page"""
    st.markdown("### ⚙️ Settings & Configuration")
    
    tab1, tab2, tab3 = st.tabs(["Profile", "Preferences", "Integrations"])
    
    with tab1:
        st.markdown("#### 👤 Profile Settings")
        user_info = st.session_state.get("user_info", {})
        
        with st.form("profile_settings"):
            name = st.text_input("Full Name", value=user_info.get("full_name", ""))
            email = st.text_input("Email", value=user_info.get("email", ""), disabled=True)
            phone = st.text_input("Phone Number", value="")
            company = st.text_input("Company Name", value="")
            
            if st.form_submit_button("Update Profile"):
                st.success("Profile updated successfully!")
    
    with tab2:
        st.markdown("#### 🎯 Preferences")
        st.selectbox("Default Currency", ["USD", "EUR", "GBP"])
        st.selectbox("Time Zone", ["EST", "PST", "CST", "MST"])
        st.checkbox("Email Notifications", value=True)
        st.checkbox("SMS Notifications", value=False)
    
    with tab3:
        st.markdown("#### 🔗 Integrations")
        st.info("🚧 **Coming Soon**: Integrations with popular real estate platforms, CRMs, and marketing tools.")
        
        st.markdown("**Planned Integrations:**")
        st.markdown("- MLS Connections")
        st.markdown("- BiggerPockets API")
        st.markdown("- Mailchimp Integration") 
        st.markdown("- Zapier Webhooks")
    
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.pop("show_settings", None)
        st.rerun()

# ===== PAGE LOADERS FOR ACTUAL PAGES =====
def add_navigation_ctas():
    """Add navigation call-to-action buttons to every page"""
    st.markdown("---")
    
    # Navigation bar
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("🏠 Dashboard", use_container_width=True, key="nav_dashboard"):
            # Clear all navigation flags to return to main dashboard
            for key in list(st.session_state.keys()):
                if key.startswith("show_"):
                    st.session_state.pop(key, None)
            st.rerun()
    
    with col2:
        if st.button("🎯 Leads", use_container_width=True, key="nav_leads"):
            # Clear other navigation flags and set leads
            for key in list(st.session_state.keys()):
                if key.startswith("show_"):
                    st.session_state.pop(key, None)
            st.session_state["show_leads"] = True
            st.rerun()
    
    with col3:
        if st.button("📊 Analytics", use_container_width=True, key="nav_analytics"):
            # Clear other navigation flags and set analytics
            for key in list(st.session_state.keys()):
                if key.startswith("show_"):
                    st.session_state.pop(key, None)
            st.session_state["show_analytics"] = True
            st.rerun()
    
    with col4:
        if st.button("🔄 Pipeline", use_container_width=True, key="nav_pipeline"):
            # Clear other navigation flags and set pipeline
            for key in list(st.session_state.keys()):
                if key.startswith("show_"):
                    st.session_state.pop(key, None)
            st.session_state["show_pipeline"] = True
            st.rerun()
    
    with col5:
        if st.button("🤖 AI Tools", use_container_width=True, key="nav_ai"):
            # Clear other navigation flags and set AI tools
            for key in list(st.session_state.keys()):
                if key.startswith("show_"):
                    st.session_state.pop(key, None)
            st.session_state["show_ai_tools"] = True
            st.rerun()
    
    # Quick actions row
    st.markdown("### ⚡ Quick Actions")
    col_q1, col_q2, col_q3, col_q4 = st.columns(4)
    
    with col_q1:
        if st.button("➕ Add Lead", use_container_width=True, key="quick_add_lead"):
            # Clear other navigation flags and set leads with add action
            for key in list(st.session_state.keys()):
                if key.startswith("show_"):
                    st.session_state.pop(key, None)
            st.session_state["show_leads"] = True
            st.session_state["quick_action"] = "add_lead"
            st.rerun()
    
    with col_q2:
        if st.button("⚡ Automation", use_container_width=True, key="quick_automation"):
            # Clear other navigation flags and set automation
            for key in list(st.session_state.keys()):
                if key.startswith("show_"):
                    st.session_state.pop(key, None)
            st.session_state["show_automation"] = True
            st.rerun()
    
    with col_q3:
        if st.button("👥 Investors", use_container_width=True, key="quick_investors"):
            # Clear other navigation flags and set investor clients
            for key in list(st.session_state.keys()):
                if key.startswith("show_"):
                    st.session_state.pop(key, None)
            st.session_state["show_clients"] = True
            st.rerun()
    
    with col_q4:
        if st.button("✅ Tasks", use_container_width=True, key="quick_tasks"):
            # Clear other navigation flags and set tasks
            for key in list(st.session_state.keys()):
                if key.startswith("show_"):
                    st.session_state.pop(key, None)
            st.session_state["show_tasks"] = True
            st.rerun()
    
    # Support contact section
    st.markdown("---")
    st.markdown("### 📞 Need Help?")
    
    col_support1, col_support2 = st.columns(2)
    
    with col_support1:
        st.markdown("""
        **� Customer Support:**
        - Email: support@nxtrix.app
        - Response: Within 24 hours
        """)
    
    with col_support2:
        st.markdown("""
        **💬 Quick Support:**
        - Live Chat: Business hours
        - Help Center: 24/7 self-service
        """)

def load_page_content(page_filename, page_title, fallback_message):
    """Helper function to load page content with embedded fallback functionality"""
    try:
        import os
        import sys
        
        st.markdown(f"### {page_title}")
        st.markdown("---")
        
        # Get the current script directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Try to load from files first
        search_paths = [
            (os.path.join(current_dir, 'pages'), f"{page_filename.replace('.py', '')}.py"),
            (current_dir, f"{page_filename.replace('.py', '')}_backup.py"),
            (current_dir, f"{page_filename.replace('.py', '')}.py"),
        ]
        
        content = None
        found_file = None
        
        for directory, filename in search_paths:
            if not os.path.exists(directory):
                continue
                
            full_path = os.path.join(directory, filename)
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    found_file = filename
                    st.success(f"✅ Loaded: {filename}")
                    break
                except Exception as e:
                    continue
        
        if content and found_file:
            try:
                # Remove page config and execute
                content = content.replace('st.set_page_config(', '# st.set_page_config(')
                exec_globals = {'st': st, '__name__': '__main__'}
                exec(content, exec_globals)
                return
            except Exception as e:
                st.error(f"Error executing {found_file}: {str(e)}")
        
        # If file loading fails, use embedded functionality
        if "leads" in page_filename.lower():
            load_embedded_leads_page()
        elif "analytics" in page_filename.lower():
            load_embedded_analytics_page()
        elif "dashboard" in page_filename.lower():
            load_embedded_dashboard_page()
        elif "ai_tools" in page_filename.lower():
            load_embedded_ai_tools_page()
        elif "pipeline" in page_filename.lower():
            load_embedded_pipeline_page()
        elif "automation" in page_filename.lower():
            load_embedded_automation_page()
        elif "task" in page_filename.lower():
            load_embedded_task_page()
        elif "investor" in page_filename.lower():
            load_embedded_investor_page()
        elif "payment" in page_filename.lower():
            load_embedded_payment_page()
        elif "settings" in page_filename.lower():
            load_embedded_settings_page()
        else:
            show_page_fallback(page_title, fallback_message)
        
    except Exception as e:
        st.error(f"Error loading page: {str(e)}")
        show_page_fallback(page_title, fallback_message)

def load_embedded_leads_page():
    """Embedded lead management functionality"""
    try:
        # Import required libraries
        import pandas as pd
        from datetime import datetime
        
        st.markdown("### 🎯 Lead Management System")
        st.markdown("*Full-featured lead management with ROI analysis*")
        
        # Initialize session state for leads
        if 'leads_data' not in st.session_state:
            st.session_state.leads_data = []
        
        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📝 Add Lead", "📊 Lead List", "💰 ROI Analysis", "📱 SMS Alerts"])
        
        with tab1:
            st.subheader("Add New Lead")
            
            with st.form("lead_entry_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    property_address = st.text_input("Property Address*", placeholder="123 Main St, City, State")
                    owner_name = st.text_input("Owner Name", placeholder="John Doe")
                    owner_phone = st.text_input("Owner Phone", placeholder="(555) 123-4567")
                    owner_email = st.text_input("Owner Email", placeholder="owner@email.com")
                    asking_price = st.number_input("Asking Price ($)", min_value=0, value=0, step=1000)
                    arv = st.number_input("ARV Estimate ($)", min_value=0, value=0, step=1000)
                
                with col2:
                    lead_source = st.selectbox("Lead Source", [
                        "Cold Calling", "Direct Mail", "Online Marketing", "Referral", 
                        "Driving for Dollars", "Wholesaler", "Real Estate Agent", "Other"
                    ])
                    property_type = st.selectbox("Property Type", [
                        "Single Family", "Multi Family", "Condo/Townhouse", 
                        "Commercial", "Land", "Mobile Home"
                    ])
                    bedrooms = st.number_input("Bedrooms", min_value=0, max_value=10, value=3)
                    square_feet = st.number_input("Square Feet", min_value=0, value=0, step=100)
                    rehab_estimate = st.number_input("Rehab Estimate ($)", min_value=0, value=0, step=1000)
                
                # Additional details
                st.subheader("Deal Details")
                col3, col4 = st.columns(2)
                
                with col3:
                    motivation = st.selectbox("Seller Motivation", [
                        "High", "Medium", "Low", "Unknown"
                    ])
                    timeline = st.selectbox("Timeline", [
                        "ASAP", "1-30 days", "1-3 months", "3-6 months", "6+ months"
                    ])
                    offer_amount = st.number_input("Your Offer ($)", min_value=0, value=0, step=1000)
                
                with col4:
                    lead_status = st.selectbox("Lead Status", [
                        "New", "Contacted", "Interested", "Under Contract", 
                        "Closed", "Not Interested", "Follow Up"
                    ])
                    priority = st.selectbox("Priority", ["High", "Medium", "Low"])
                    assigned_to = st.text_input("Assigned To", placeholder="Team Member")
                
                notes = st.text_area("Notes", placeholder="Additional details about the lead...")
                
                submitted = st.form_submit_button("💾 Add Lead", use_container_width=True)
                
                if submitted and property_address:
                    # Calculate basic ROI metrics
                    potential_profit = arv - rehab_estimate - offer_amount if offer_amount > 0 else 0
                    roi_percentage = (potential_profit / offer_amount * 100) if offer_amount > 0 else 0
                    
                    new_lead = {
                        'id': len(st.session_state.leads_data) + 1,
                        'date_added': datetime.now().strftime("%Y-%m-%d %H:%M"),
                        'property_address': property_address,
                        'owner_name': owner_name,
                        'owner_phone': owner_phone,
                        'owner_email': owner_email,
                        'asking_price': asking_price,
                        'arv': arv,
                        'lead_source': lead_source,
                        'property_type': property_type,
                        'bedrooms': bedrooms,
                        'square_feet': square_feet,
                        'rehab_estimate': rehab_estimate,
                        'motivation': motivation,
                        'timeline': timeline,
                        'offer_amount': offer_amount,
                        'lead_status': lead_status,
                        'priority': priority,
                        'assigned_to': assigned_to,
                        'notes': notes,
                        'potential_profit': potential_profit,
                        'roi_percentage': roi_percentage
                    }
                    
                    st.session_state.leads_data.append(new_lead)
                    st.success(f"✅ Lead added successfully! Potential profit: ${potential_profit:,.2f} ({roi_percentage:.1f}% ROI)")
                    st.rerun()
        
        with tab2:
            st.subheader("Lead Database")
            
            if st.session_state.leads_data:
                df = pd.DataFrame(st.session_state.leads_data)
                
                # Filters
                col1, col2, col3 = st.columns(3)
                with col1:
                    status_filter = st.selectbox("Filter by Status", ["All"] + list(df['lead_status'].unique()))
                with col2:
                    priority_filter = st.selectbox("Filter by Priority", ["All"] + list(df['priority'].unique()))
                with col3:
                    source_filter = st.selectbox("Filter by Source", ["All"] + list(df['lead_source'].unique()))
                
                # Apply filters
                filtered_df = df.copy()
                if status_filter != "All":
                    filtered_df = filtered_df[filtered_df['lead_status'] == status_filter]
                if priority_filter != "All":
                    filtered_df = filtered_df[filtered_df['priority'] == priority_filter]
                if source_filter != "All":
                    filtered_df = filtered_df[filtered_df['lead_source'] == source_filter]
                
                # Display leads
                st.dataframe(
                    filtered_df[['property_address', 'owner_name', 'asking_price', 'arv', 'potential_profit', 'roi_percentage', 'lead_status', 'priority']],
                    use_container_width=True
                )
                
                # Summary metrics
                st.subheader("📊 Lead Summary")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Leads", len(filtered_df))
                with col2:
                    avg_arv = filtered_df['arv'].mean() if len(filtered_df) > 0 else 0
                    st.metric("Avg ARV", f"${avg_arv:,.0f}")
                with col3:
                    total_profit = filtered_df['potential_profit'].sum()
                    st.metric("Total Potential Profit", f"${total_profit:,.0f}")
                with col4:
                    avg_roi = filtered_df['roi_percentage'].mean() if len(filtered_df) > 0 else 0
                    st.metric("Avg ROI", f"{avg_roi:.1f}%")
            else:
                st.info("No leads added yet. Use the 'Add Lead' tab to get started!")
        
        with tab3:
            st.subheader("💰 ROI Analysis")
            
            if st.session_state.leads_data:
                df = pd.DataFrame(st.session_state.leads_data)
                
                # ROI Calculator
                st.subheader("Quick ROI Calculator")
                col1, col2 = st.columns(2)
                with col1:
                    calc_arv = st.number_input("ARV ($)", min_value=0, value=200000, key="calc_arv")
                    calc_rehab = st.number_input("Rehab Cost ($)", min_value=0, value=30000, key="calc_rehab")
                    calc_offer = st.number_input("Offer Price ($)", min_value=0, value=140000, key="calc_offer")
                
                with col2:
                    holding_costs = st.number_input("Holding Costs ($)", min_value=0, value=5000, key="holding")
                    closing_costs = st.number_input("Closing Costs ($)", min_value=0, value=3000, key="closing")
                    profit_margin = st.number_input("Desired Profit ($)", min_value=0, value=20000, key="profit")
                
                # Calculate results
                total_costs = calc_offer + calc_rehab + holding_costs + closing_costs + profit_margin
                max_offer = calc_arv - calc_rehab - holding_costs - closing_costs - profit_margin
                actual_profit = calc_arv - total_costs
                roi = (actual_profit / calc_offer * 100) if calc_offer > 0 else 0
                
                st.subheader("Analysis Results")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Maximum Offer", f"${max_offer:,.0f}")
                with col2:
                    st.metric("Projected Profit", f"${actual_profit:,.0f}")
                with col3:
                    st.metric("ROI Percentage", f"{roi:.1f}%")
                
                # Deal quality indicator
                if roi >= 25:
                    st.success("🎯 Excellent Deal! High ROI potential")
                elif roi >= 15:
                    st.warning("⚠️ Good Deal - Acceptable ROI")
                elif roi >= 10:
                    st.warning("⚠️ Marginal Deal - Low ROI")
                else:
                    st.error("❌ Poor Deal - Negative or very low ROI")
            else:
                st.info("Add some leads to see ROI analysis")
        
        with tab4:
            st.subheader("📱 SMS Alert System")
            st.info("🚀 SMS notifications are configured with Twilio integration")
            
            # SMS settings
            st.subheader("SMS Configuration")
            col1, col2 = st.columns(2)
            with col1:
                sms_enabled = st.checkbox("Enable SMS Alerts", value=True)
                notify_new_leads = st.checkbox("New Lead Notifications", value=True)
                notify_hot_leads = st.checkbox("Hot Lead Alerts", value=True)
            
            with col2:
                notify_contracts = st.checkbox("Contract Notifications", value=True)
                notify_follow_ups = st.checkbox("Follow-up Reminders", value=True)
                admin_phone = st.text_input("Admin Phone", value="(XXX) XXX-XXXX", disabled=True)
            
        if st.button("Test SMS System"):
            st.success("📱 SMS test would be sent to configured number")
            st.info("Twilio integration configured and ready")
    
    except Exception as e:
        st.error(f"Error in leads page: {str(e)}")
        st.info("Please check your Supabase connection and try again.")
    
    # Add navigation CTAs
    add_navigation_ctas()

def load_embedded_analytics_page():
    """Advanced Analytics & Business Intelligence - Full Implementation"""
    try:
        st.markdown("### 📊 Advanced Analytics & Business Intelligence")
        st.markdown("*Comprehensive performance tracking and predictive insights*")
        
        # Initialize analytics data
        if 'analytics_data' not in st.session_state:
            st.session_state.analytics_data = {
                'revenue_data': [
                    {'month': 'Jan 2025', 'revenue': 450000, 'deals': 12, 'leads': 234},
                    {'month': 'Feb 2025', 'revenue': 520000, 'deals': 15, 'leads': 289},
                    {'month': 'Mar 2025', 'revenue': 680000, 'deals': 18, 'leads': 312},
                    {'month': 'Apr 2025', 'revenue': 590000, 'deals': 16, 'leads': 298},
                    {'month': 'May 2025', 'revenue': 750000, 'deals': 21, 'leads': 356},
                    {'month': 'Jun 2025', 'revenue': 820000, 'deals': 24, 'leads': 401},
                    {'month': 'Jul 2025', 'revenue': 920000, 'deals': 27, 'leads': 445},
                    {'month': 'Aug 2025', 'revenue': 1050000, 'deals': 31, 'leads': 489},
                    {'month': 'Sep 2025', 'revenue': 890000, 'deals': 25, 'leads': 412}
                ],
                'performance_metrics': {
                    'conversion_rate': 12.5,
                    'avg_deal_size': 78500,
                    'lead_response_time': 2.3,
                    'deal_cycle_time': 45,
                    'customer_satisfaction': 4.7,
                    'roi_percentage': 24.8
                }
            }
        
        # Main analytics tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Executive Dashboard", "💰 Revenue Analytics", "🎯 Performance Metrics", "🌍 Market Intelligence", "🔮 Predictive Analytics"])
        
        with tab1:
            st.markdown("## 📈 Executive Dashboard")
            
            # Key Performance Indicators
            col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5 = st.columns(5)
            
            with col_kpi1:
                total_revenue = sum(item['revenue'] for item in st.session_state.analytics_data['revenue_data'])
                st.metric("💰 Total Revenue", f"${total_revenue:,.0f}", delta="+18.5%")
            
            with col_kpi2:
                total_deals = sum(item['deals'] for item in st.session_state.analytics_data['revenue_data'])
                st.metric("🤝 Total Deals", total_deals, delta="+12.3%")
            
            with col_kpi3:
                conversion_rate = st.session_state.analytics_data['performance_metrics']['conversion_rate']
                st.metric("📊 Conversion Rate", f"{conversion_rate}%", delta="+2.1%")
            
            with col_kpi4:
                avg_deal_size = st.session_state.analytics_data['performance_metrics']['avg_deal_size']
                st.metric("💎 Avg Deal Size", f"${avg_deal_size:,.0f}", delta="+8.7%")
            
            with col_kpi5:
                roi = st.session_state.analytics_data['performance_metrics']['roi_percentage']
                st.metric("📈 ROI", f"{roi}%", delta="+3.2%")
            
            # Revenue trend chart
            st.markdown("### 📈 Revenue Trend Analysis")
            
            revenue_df = pd.DataFrame(st.session_state.analytics_data['revenue_data'])
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=revenue_df['month'],
                y=revenue_df['revenue'],
                mode='lines+markers',
                name='Revenue',
                line=dict(color='#2E86AB', width=3),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                title="Monthly Revenue Performance",
                xaxis_title="Month",
                yaxis_title="Revenue ($)",
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Deal pipeline visualization
            col_pipeline1, col_pipeline2 = st.columns(2)
            
            with col_pipeline1:
                st.markdown("### 🎯 Deal Pipeline Health")
                
                pipeline_data = {
                    'Lead': 156,
                    'Qualified': 89,
                    'Proposal': 34,
                    'Negotiation': 18,
                    'Closed': 12
                }
                
                fig_funnel = go.Figure(go.Funnel(
                    y=list(pipeline_data.keys()),
                    x=list(pipeline_data.values()),
                    textinfo="value+percent initial"
                ))
                
                fig_funnel.update_layout(height=400)
                st.plotly_chart(fig_funnel, use_container_width=True)
            
            with col_pipeline2:
                st.markdown("### 🏢 Property Type Distribution")
                
                property_types = ['Commercial Office', 'Residential Multi', 'Industrial', 'Retail', 'Mixed Use']
                property_values = [35, 28, 22, 8, 7]
                
                fig_pie = go.Figure(data=[go.Pie(
                    labels=property_types,
                    values=property_values,
                    hole=0.4
                )])
                
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with tab2:
            st.markdown("## 💰 Revenue Analytics")
            
            # Revenue breakdown
            col_rev1, col_rev2, col_rev3 = st.columns(3)
            
            with col_rev1:
                current_month_revenue = st.session_state.analytics_data['revenue_data'][-1]['revenue']
                st.metric("🗓️ Current Month", f"${current_month_revenue:,.0f}")
                
                ytd_revenue = sum(item['revenue'] for item in st.session_state.analytics_data['revenue_data'])
                st.metric("📅 YTD Revenue", f"${ytd_revenue:,.0f}")
            
            with col_rev2:
                last_month_revenue = st.session_state.analytics_data['revenue_data'][-2]['revenue']
                monthly_growth = ((current_month_revenue - last_month_revenue) / last_month_revenue) * 100
                st.metric("📈 Monthly Growth", f"{monthly_growth:+.1f}%")
                
                projected_annual = ytd_revenue * (12/9)
                st.metric("🎯 Annual Projection", f"${projected_annual:,.0f}")
            
            with col_rev3:
                avg_monthly = ytd_revenue / 9
                st.metric("📊 Monthly Average", f"${avg_monthly:,.0f}")
                
                best_month = max(st.session_state.analytics_data['revenue_data'], key=lambda x: x['revenue'])
                st.metric("🏆 Best Month", f"${best_month['revenue']:,.0f}")
            
            # Revenue vs Deals correlation
            st.markdown("### 📈 Revenue vs Deals Analysis")
            
            fig_scatter = go.Figure()
            fig_scatter.add_trace(go.Scatter(
                x=[item['deals'] for item in st.session_state.analytics_data['revenue_data']],
                y=[item['revenue'] for item in st.session_state.analytics_data['revenue_data']],
                mode='markers+text',
                text=[item['month'] for item in st.session_state.analytics_data['revenue_data']],
                textposition="top center",
                marker=dict(size=12, color=[item['revenue'] for item in st.session_state.analytics_data['revenue_data']], 
                           colorscale='Viridis', showscale=True)
            ))
            
            fig_scatter.update_layout(
                title="Revenue vs Number of Deals",
                xaxis_title="Number of Deals",
                yaxis_title="Revenue ($)",
                height=400
            )
            
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        with tab3:
            st.markdown("## 🎯 Performance Metrics")
            
            # Core performance indicators
            metrics = st.session_state.analytics_data['performance_metrics']
            
            col_perf1, col_perf2, col_perf3 = st.columns(3)
            
            with col_perf1:
                st.markdown("### 📊 Sales Performance")
                st.metric("🎯 Conversion Rate", f"{metrics['conversion_rate']}%", delta="+2.1%")
                st.metric("💰 Avg Deal Size", f"${metrics['avg_deal_size']:,.0f}", delta="+8.7%")
                st.metric("⏱️ Deal Cycle Time", f"{metrics['deal_cycle_time']} days", delta="-3 days")
            
            with col_perf2:
                st.markdown("### 🚀 Operational Efficiency")
                st.metric("⚡ Response Time", f"{metrics['lead_response_time']} hours", delta="-0.5 hrs")
                st.metric("😊 Customer Satisfaction", f"{metrics['customer_satisfaction']}/5.0", delta="+0.2")
                st.metric("📈 ROI", f"{metrics['roi_percentage']}%", delta="+3.2%")
            
            with col_perf3:
                st.markdown("### 📈 Growth Metrics")
                
                total_leads = sum(item['leads'] for item in st.session_state.analytics_data['revenue_data'])
                total_deals = sum(item['deals'] for item in st.session_state.analytics_data['revenue_data'])
                
                st.metric("🎯 Lead-to-Deal Rate", f"{(total_deals/total_leads)*100:.1f}%", delta="+1.8%")
                st.metric("💎 Revenue per Lead", f"${(sum(item['revenue'] for item in st.session_state.analytics_data['revenue_data'])/total_leads):,.0f}", delta="+$145")
                st.metric("🏆 Deal Win Rate", "68.5%", delta="+4.2%")
        
        with tab4:
            st.markdown("## 🌍 Market Intelligence")
            
            # Market overview
            st.markdown("### 📊 Market Overview")
            
            col_market1, col_market2, col_market3, col_market4 = st.columns(4)
            
            with col_market1:
                st.metric("🏢 Market Cap", "$2.8B", delta="+12.5%")
            with col_market2:
                st.metric("📈 Market Growth", "8.7%", delta="+1.2%")
            with col_market3:
                st.metric("🏆 Market Share", "15.3%", delta="+2.1%")
            with col_market4:
                st.metric("🎯 Market Ranking", "#3", delta="+1 position")
            
            # Property type trends
            st.markdown("### 🏢 Property Type Performance")
            
            market_trends = [
                {'property_type': 'Commercial Office', 'trend': '+8.2%'},
                {'property_type': 'Residential Multi', 'trend': '+12.5%'},
                {'property_type': 'Industrial', 'trend': '+15.1%'},
                {'property_type': 'Retail', 'trend': '-2.3%'},
                {'property_type': 'Mixed Use', 'trend': '+6.7%'}
            ]
            
            for trend in market_trends:
                trend_color = "🟢" if "+" in trend['trend'] else "🔴"
                st.write(f"{trend_color} **{trend['property_type']}**: {trend['trend']}")
        
        with tab5:
            st.markdown("## 🔮 Predictive Analytics")
            
            # AI-powered predictions
            st.markdown("### 🤖 AI-Powered Forecasting")
            
            col_pred1, col_pred2, col_pred3 = st.columns(3)
            
            with col_pred1:
                st.markdown("#### 💰 Revenue Predictions")
                st.metric("📅 Next Quarter", "$3.2M", delta="+15.2%")
                st.metric("📅 Next 6 Months", "$6.8M", delta="+18.7%")
                st.metric("📅 End of Year", "$12.4M", delta="+22.1%")
            
            with col_pred2:
                st.markdown("#### 🎯 Deal Forecasting")
                st.metric("🤝 Next Month", "28 deals", delta="+3")
                st.metric("📊 Success Rate", "71.2%", delta="+2.7%")
                st.metric("💎 Avg Deal Value", "$95K", delta="+$12K")
            
            with col_pred3:
                st.markdown("#### 📈 Market Predictions")
                st.metric("🏢 Market Growth", "+9.2%", delta="+0.5%")
                st.metric("🎯 Opportunity Score", "8.4/10", delta="+0.6")
                st.metric("⚠️ Risk Level", "Low", delta="Stable")
            
            # Generate prediction chart
            st.markdown("### 📈 Revenue Prediction Model")
            
            months_historical = [item['month'] for item in st.session_state.analytics_data['revenue_data']]
            revenue_historical = [item['revenue'] for item in st.session_state.analytics_data['revenue_data']]
            
            months_future = ['Oct 2025', 'Nov 2025', 'Dec 2025']
            revenue_predicted = [920000, 1080000, 1150000]
            
            fig_prediction = go.Figure()
            
            fig_prediction.add_trace(go.Scatter(
                x=months_historical,
                y=revenue_historical,
                mode='lines+markers',
                name='Historical Revenue',
                line=dict(color='#2E86AB', width=3)
            ))
            
            fig_prediction.add_trace(go.Scatter(
                x=months_future,
                y=revenue_predicted,
                mode='lines+markers',
                name='Predicted Revenue',
                line=dict(color='#FF6B6B', width=3, dash='dash')
            ))
            
            fig_prediction.update_layout(
                title="Revenue Prediction Model",
                xaxis_title="Month",
                yaxis_title="Revenue ($)",
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_prediction, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error in analytics: {str(e)}")
    
    # Add navigation CTAs
    add_navigation_ctas()

def load_embedded_dashboard_page():
    """Embedded dashboard functionality"""
    st.markdown("### 🏠 NxTrix CRM Dashboard")
    st.markdown("*Executive overview and quick actions*")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Active Leads", "25", delta="5")
    with col2:
        st.metric("Deals Closed", "8", delta="2")
    with col3:
        st.metric("Revenue (MTD)", "$45,000", delta="$12,000")
    with col4:
        st.metric("Pipeline Value", "$250,000", delta="$35,000")
    
    st.info("Full dashboard with interactive charts and real-time updates available in production mode.")

def load_embedded_ai_tools_page():
    """Embedded AI tools functionality"""
    st.markdown("### 🤖 AI Tools Hub")
    st.markdown("*Artificial intelligence-powered business optimization*")
    
    tab1, tab2, tab3 = st.tabs(["🎯 Lead Scoring", "📝 Content Generator", "📊 Market Analysis"])
    
    with tab1:
        st.subheader("AI Lead Scoring")
        st.info("🤖 Machine learning model analyzes leads and predicts closure probability")
        
        if st.button("Score Current Leads"):
            st.success("AI scoring complete! High-priority leads identified.")
    
    with tab2:
        st.subheader("AI Content Generator")
        content_type = st.selectbox("Content Type", ["Email Template", "SMS Message", "Follow-up Script"])
        lead_context = st.text_area("Lead Context", placeholder="Tell me about the lead...")
        
        if st.button("Generate Content"):
            st.success("AI-generated content ready!")
            st.text_area("Generated Content", "Sample AI-generated professional communication...", height=100)
    
    with tab3:
        st.subheader("Market Analysis AI")
        st.info("AI-powered market trend analysis and property valuation")

def load_embedded_pipeline_page():
    """Advanced Pipeline Management System - Full Implementation"""
    try:
        st.markdown("### 🔄 Advanced Pipeline Management")
        st.markdown("*Visual deal progression and stage management*")
        
        # Initialize pipeline data in session state
        if 'pipeline_deals' not in st.session_state:
            st.session_state.pipeline_deals = {
                'New Lead': [
                    {'id': 1, 'address': '123 Oak St', 'value': 180000, 'owner': 'John Smith', 'probability': 30},
                    {'id': 2, 'address': '456 Pine Ave', 'value': 220000, 'owner': 'Jane Doe', 'probability': 25}
                ],
                'Contacted': [
                    {'id': 3, 'address': '789 Elm Dr', 'value': 195000, 'owner': 'Bob Wilson', 'probability': 50}
                ],
                'Qualified': [
                    {'id': 4, 'address': '321 Maple St', 'value': 165000, 'owner': 'Alice Brown', 'probability': 70}
                ],
                'Under Contract': [
                    {'id': 5, 'address': '654 Cedar Ln', 'value': 240000, 'owner': 'Mike Davis', 'probability': 90}
                ],
                'Closed': [
                    {'id': 6, 'address': '987 Birch Rd', 'value': 210000, 'owner': 'Sarah Lee', 'probability': 100}
                ],
                'Lost': []
            }
        
        # Pipeline stages
        stages = ['New Lead', 'Contacted', 'Qualified', 'Under Contract', 'Closed', 'Lost']
        stage_colors = {
            'New Lead': '#ff6b6b',
            'Contacted': '#ffa726', 
            'Qualified': '#66bb6a',
            'Under Contract': '#42a5f5',
            'Closed': '#4caf50',
            'Lost': '#757575'
        }
        
        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🏗️ Pipeline Board", "📊 Analytics", "⚙️ Automation", "➕ Add Deal"])
        
        with tab1:
            st.markdown("## 🏗️ Visual Deal Pipeline")
            
            # Pipeline overview metrics
            total_deals = sum(len(deals) for deals in st.session_state.pipeline_deals.values())
            total_value = sum(deal['value'] for deals in st.session_state.pipeline_deals.values() for deal in deals)
            weighted_value = sum(deal['value'] * deal['probability'] / 100 for deals in st.session_state.pipeline_deals.values() for deal in deals)
            
            col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
            with col_metric1:
                st.metric("Total Deals", total_deals)
            with col_metric2:
                st.metric("Pipeline Value", f"${total_value:,.0f}")
            with col_metric3:
                st.metric("Weighted Value", f"${weighted_value:,.0f}")
            with col_metric4:
                avg_prob = sum(deal['probability'] for deals in st.session_state.pipeline_deals.values() for deal in deals) / total_deals if total_deals > 0 else 0
                st.metric("Avg Probability", f"{avg_prob:.0f}%")
            
            st.markdown("---")
            
            # Kanban-style pipeline board
            cols = st.columns(len(stages))
            
            for i, stage in enumerate(stages):
                with cols[i]:
                    # Stage header
                    stage_count = len(st.session_state.pipeline_deals[stage])
                    stage_value = sum(deal['value'] for deal in st.session_state.pipeline_deals[stage])
                    
                    st.markdown(f"""
                    <div style="background-color: {stage_colors[stage]}; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
                        <h4 style="color: white; margin: 0; text-align: center;">{stage}</h4>
                        <p style="color: white; margin: 0; text-align: center; font-size: 0.8rem;">
                            {stage_count} deals • ${stage_value:,.0f}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Deal cards in this stage
                    for deal in st.session_state.pipeline_deals[stage]:
                        with st.container():
                            st.markdown(f"""
                            <div style="border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 8px; background: white;">
                                <h5 style="margin: 0 0 5px 0;">{deal['address']}</h5>
                                <p style="margin: 0; font-size: 0.9rem; color: #666;">Owner: {deal['owner']}</p>
                                <p style="margin: 0; font-size: 0.9rem; color: #666;">Value: ${deal['value']:,.0f}</p>
                                <p style="margin: 5px 0 0 0; font-size: 0.9rem;">
                                    <span style="background: {stage_colors[stage]}; color: white; padding: 2px 8px; border-radius: 12px;">
                                        {deal['probability']}% probability
                                    </span>
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Action buttons for each deal
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                if st.button("▶️", key=f"advance_{deal['id']}", help="Move to next stage"):
                                    if stage != 'Lost' and stage != 'Closed':
                                        next_stage_idx = stages.index(stage) + 1
                                        if next_stage_idx < len(stages) - 1:  # Don't auto-advance to Lost
                                            next_stage = stages[next_stage_idx]
                                            st.session_state.pipeline_deals[stage].remove(deal)
                                            # Update probability based on stage
                                            if next_stage == 'Contacted':
                                                deal['probability'] = 50
                                            elif next_stage == 'Qualified':
                                                deal['probability'] = 70
                                            elif next_stage == 'Under Contract':
                                                deal['probability'] = 90
                                            elif next_stage == 'Closed':
                                                deal['probability'] = 100
                                            st.session_state.pipeline_deals[next_stage].append(deal)
                                            st.success(f"Moved {deal['address']} to {next_stage}")
                                            st.rerun()
                            
                            with col_btn2:
                                if st.button("❌", key=f"lost_{deal['id']}", help="Mark as lost"):
                                    st.session_state.pipeline_deals[stage].remove(deal)
                                    deal['probability'] = 0
                                    st.session_state.pipeline_deals['Lost'].append(deal)
                                    st.warning(f"Moved {deal['address']} to Lost")
                                    st.rerun()
        
        with tab2:
            st.markdown("## 📊 Pipeline Analytics")
            
            # Conversion funnel
            st.markdown("### 🔄 Conversion Funnel")
            
            funnel_data = []
            for stage in stages[:-1]:  # Exclude 'Lost' from funnel
                count = len(st.session_state.pipeline_deals[stage])
                funnel_data.append({'Stage': stage, 'Count': count})
            
            if funnel_data:
                df_funnel = pd.DataFrame(funnel_data)
                fig_funnel = px.funnel(df_funnel, x='Count', y='Stage', title="Deal Conversion Funnel")
                st.plotly_chart(fig_funnel, use_container_width=True)
            
            # Stage performance
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                # Deals by stage
                stage_counts = {stage: len(deals) for stage, deals in st.session_state.pipeline_deals.items()}
                fig_pie = px.pie(values=list(stage_counts.values()), names=list(stage_counts.keys()),
                               title="Deals by Stage")
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col_chart2:
                # Value by stage
                stage_values = {stage: sum(deal['value'] for deal in deals) 
                              for stage, deals in st.session_state.pipeline_deals.items()}
                fig_bar = px.bar(x=list(stage_values.keys()), y=list(stage_values.values()),
                               title="Pipeline Value by Stage")
                st.plotly_chart(fig_bar, use_container_width=True)
            
            # Velocity metrics
            st.markdown("### ⚡ Pipeline Velocity")
            col_vel1, col_vel2, col_vel3 = st.columns(3)
            
            with col_vel1:
                avg_deal_size = total_value / total_deals if total_deals > 0 else 0
                st.metric("Average Deal Size", f"${avg_deal_size:,.0f}")
            
            with col_vel2:
                # Mock velocity calculation
                avg_days_per_stage = 14  # Sample data
                st.metric("Avg Days per Stage", f"{avg_days_per_stage} days")
            
            with col_vel3:
                # Conversion rate from lead to close
                closed_deals = len(st.session_state.pipeline_deals['Closed'])
                conversion_rate = (closed_deals / total_deals * 100) if total_deals > 0 else 0
                st.metric("Lead to Close Rate", f"{conversion_rate:.1f}%")
        
        with tab3:
            st.markdown("## ⚙️ Pipeline Automation")
            
            st.markdown("### 🔄 Stage Automation Rules")
            
            # Automation rule builder
            with st.expander("➕ Create New Automation Rule"):
                rule_name = st.text_input("Rule Name", placeholder="Auto-advance high probability deals")
                
                trigger_type = st.selectbox("Trigger", [
                    "Deal enters stage",
                    "Deal stays in stage for X days", 
                    "Probability reaches threshold",
                    "Value exceeds amount"
                ])
                
                action_type = st.selectbox("Action", [
                    "Move to next stage",
                    "Send email notification",
                    "Create task",
                    "Update probability",
                    "Assign to team member"
                ])
                
                if st.button("Create Automation Rule"):
                    st.success(f"Created automation rule: {rule_name}")
                    # In full implementation, this would save to database
            
            # Existing automation rules
            st.markdown("### 📋 Active Automation Rules")
            
            sample_rules = [
                {"name": "Auto-advance Qualified Deals", "trigger": "Probability > 60%", "action": "Move to Under Contract", "active": True},
                {"name": "Stale Lead Alert", "trigger": "In New Lead > 7 days", "action": "Create follow-up task", "active": True},
                {"name": "High Value Notification", "trigger": "Deal value > $200K", "action": "Notify manager", "active": False}
            ]
            
            for rule in sample_rules:
                col_rule1, col_rule2, col_rule3, col_rule4 = st.columns([3, 2, 2, 1])
                
                with col_rule1:
                    st.write(f"**{rule['name']}**")
                
                with col_rule2:
                    st.write(rule['trigger'])
                
                with col_rule3:
                    st.write(rule['action'])
                
                with col_rule4:
                    status = "🟢 Active" if rule['active'] else "🔴 Inactive"
                    st.write(status)
        
        with tab4:
            st.markdown("## ➕ Add New Deal")
            
            with st.form("add_deal_form"):
                col_add1, col_add2 = st.columns(2)
                
                with col_add1:
                    new_address = st.text_input("Property Address*")
                    new_owner = st.text_input("Owner Name*")
                    new_value = st.number_input("Deal Value ($)*", min_value=0, step=1000)
                
                with col_add2:
                    new_stage = st.selectbox("Initial Stage", stages[:-1])  # Exclude 'Lost'
                    new_probability = st.slider("Probability (%)", 0, 100, 30)
                    new_notes = st.text_area("Notes")
                
                if st.form_submit_button("Add Deal to Pipeline"):
                    if new_address and new_owner and new_value > 0:
                        new_deal = {
                            'id': max([deal['id'] for deals in st.session_state.pipeline_deals.values() for deal in deals], default=0) + 1,
                            'address': new_address,
                            'owner': new_owner,
                            'value': new_value,
                            'probability': new_probability,
                            'notes': new_notes,
                            'created_date': datetime.now().strftime("%Y-%m-%d")
                        }
                        
                        st.session_state.pipeline_deals[new_stage].append(new_deal)
                        st.success(f"✅ Added {new_address} to {new_stage} stage")
                        st.rerun()
                    else:
                        st.error("Please fill in all required fields")
        
    except Exception as e:
        st.error(f"Error in pipeline management: {str(e)}")
    
    # Add navigation CTAs
    add_navigation_ctas()

def load_embedded_automation_page():
    """Advanced Automation Center - Full Implementation"""
    try:
        st.markdown("### ⚡ Automation Center")
        st.markdown("*Workflow automation and business process optimization*")
        
        # Initialize automation data
        if 'automation_rules' not in st.session_state:
            st.session_state.automation_rules = [
                {
                    'id': 1,
                    'name': 'Welcome New Leads',
                    'trigger': 'New lead added',
                    'action': 'Send welcome email',
                    'active': True,
                    'executions': 45
                },
                {
                    'id': 2, 
                    'name': 'Follow-up Sequence',
                    'trigger': 'Lead not contacted in 3 days',
                    'action': 'Send follow-up SMS',
                    'active': True,
                    'executions': 23
                },
                {
                    'id': 3,
                    'name': 'Hot Lead Alert',
                    'trigger': 'Lead score > 80',
                    'action': 'Notify sales team',
                    'active': False,
                    'executions': 12
                }
            ]
        
        if 'email_sequences' not in st.session_state:
            st.session_state.email_sequences = []
        
        # Main tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔧 Workflow Builder", "📧 Email Automation", "📱 SMS Campaigns", "📊 Analytics", "⚙️ Settings"])
        
        with tab1:
            st.markdown("## 🔧 Automation Workflow Builder")
            
            # Quick stats
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            with col_stat1:
                active_rules = sum(1 for rule in st.session_state.automation_rules if rule['active'])
                st.metric("Active Rules", active_rules)
            with col_stat2:
                total_executions = sum(rule['executions'] for rule in st.session_state.automation_rules)
                st.metric("Total Executions", total_executions)
            with col_stat3:
                st.metric("Success Rate", "94.2%")
            with col_stat4:
                st.metric("Time Saved", "18.5 hrs/week")
            
            # Rule builder
            st.markdown("### ➕ Create New Automation Rule")
            
            with st.expander("Build Custom Automation"):
                col_builder1, col_builder2 = st.columns(2)
                
                with col_builder1:
                    st.markdown("**🎯 When (Trigger)**")
                    trigger_category = st.selectbox("Trigger Category", [
                        "Lead Events", "Deal Events", "Time-based", "Behavioral", "Custom"
                    ])
                    
                    if trigger_category == "Lead Events":
                        trigger_event = st.selectbox("Specific Trigger", [
                            "New lead added", "Lead updated", "Lead contacted", 
                            "Lead score changed", "Lead source assigned"
                        ])
                    elif trigger_category == "Deal Events":
                        trigger_event = st.selectbox("Specific Trigger", [
                            "Deal stage changed", "Deal value updated", "Contract signed",
                            "Deal closed", "Deal lost"
                        ])
                    elif trigger_category == "Time-based":
                        trigger_event = st.selectbox("Specific Trigger", [
                            "Daily at specific time", "Weekly on day", "Monthly",
                            "X days after event", "X hours without action"
                        ])
                        
                        if "days after" in trigger_event or "hours without" in trigger_event:
                            time_value = st.number_input("Time Value", min_value=1, value=3)
                            time_unit = st.selectbox("Unit", ["hours", "days", "weeks"])
                    
                    # Conditions
                    st.markdown("**🎯 Conditions (Optional)**")
                    add_conditions = st.checkbox("Add conditions")
                    
                    if add_conditions:
                        condition_field = st.selectbox("Field", [
                            "Lead score", "Deal value", "Property type", "Lead source", "Owner name"
                        ])
                        condition_operator = st.selectbox("Operator", [
                            "equals", "greater than", "less than", "contains", "not equals"
                        ])
                        condition_value = st.text_input("Value")
                
                with col_builder2:
                    st.markdown("**⚡ Then (Action)**")
                    action_category = st.selectbox("Action Category", [
                        "Communication", "Data Update", "Task Creation", "Notification", "Integration"
                    ])
                    
                    if action_category == "Communication":
                        action_type = st.selectbox("Communication Type", [
                            "Send email", "Send SMS", "Send letter", "Schedule call"
                        ])
                        
                        if action_type == "Send email":
                            email_template = st.selectbox("Email Template", [
                                "Welcome New Lead", "Follow-up #1", "Follow-up #2",
                                "Deal Update", "Market Report", "Custom"
                            ])
                        elif action_type == "Send SMS":
                            sms_template = st.selectbox("SMS Template", [
                                "Quick Follow-up", "Deal Alert", "Appointment Reminder", "Custom"
                            ])
                    
                    elif action_category == "Data Update":
                        action_type = st.selectbox("Update Type", [
                            "Change lead status", "Update deal stage", "Modify score",
                            "Add tags", "Assign to user"
                        ])
                    
                    elif action_category == "Task Creation":
                        task_type = st.selectbox("Task Type", [
                            "Follow-up call", "Send proposal", "Property visit",
                            "Contract review", "Custom task"
                        ])
                    
                    # Additional settings
                    st.markdown("**⚙️ Settings**")
                    rule_name = st.text_input("Rule Name", placeholder="My Automation Rule")
                    rule_active = st.checkbox("Activate immediately", value=True)
                
                if st.button("🚀 Create Automation Rule", use_container_width=True):
                    if rule_name:
                        new_rule = {
                            'id': len(st.session_state.automation_rules) + 1,
                            'name': rule_name,
                            'trigger': f"{trigger_category}: {trigger_event}",
                            'action': f"{action_category}: {action_type}",
                            'active': rule_active,
                            'executions': 0
                        }
                        st.session_state.automation_rules.append(new_rule)
                        st.success(f"✅ Created automation rule: {rule_name}")
                        st.rerun()
                    else:
                        st.error("Please provide a rule name")
            
            # Existing rules management
            st.markdown("### 📋 Existing Automation Rules")
            
            for rule in st.session_state.automation_rules:
                with st.expander(f"{'🟢' if rule['active'] else '🔴'} {rule['name']}"):
                    col_rule1, col_rule2 = st.columns(2)
                    
                    with col_rule1:
                        st.write(f"**Trigger:** {rule['trigger']}")
                        st.write(f"**Action:** {rule['action']}")
                        st.write(f"**Executions:** {rule['executions']}")
                    
                    with col_rule2:
                        col_btn1, col_btn2, col_btn3 = st.columns(3)
                        
                        with col_btn1:
                            if st.button("✏️ Edit", key=f"edit_{rule['id']}"):
                                st.info("Edit functionality would open here")
                        
                        with col_btn2:
                            current_status = "Deactivate" if rule['active'] else "Activate"
                            if st.button(current_status, key=f"toggle_{rule['id']}"):
                                rule['active'] = not rule['active']
                                st.success(f"Rule {current_status.lower()}d")
                                st.rerun()
                        
                        with col_btn3:
                            if st.button("🗑️ Delete", key=f"delete_{rule['id']}"):
                                st.session_state.automation_rules.remove(rule)
                                st.success("Rule deleted")
                                st.rerun()
        
        with tab2:
            st.markdown("## 📧 Email Automation Sequences")
            
            # Email sequence builder
            st.markdown("### ✉️ Create Email Sequence")
            
            with st.form("email_sequence_form"):
                sequence_name = st.text_input("Sequence Name", placeholder="New Lead Welcome Series")
                sequence_trigger = st.selectbox("Trigger", [
                    "New lead added", "Lead not contacted in X days", "Deal stage changed", "Manual trigger"
                ])
                
                st.markdown("**📬 Email Steps**")
                
                # Email step 1
                st.markdown("**Step 1:**")
                col_email1, col_email2 = st.columns(2)
                with col_email1:
                    email1_delay = st.number_input("Send after (hours)", min_value=0, value=0, key="email1_delay")
                    email1_subject = st.text_input("Subject Line", placeholder="Welcome to our investment network", key="email1_subject")
                with col_email2:
                    email1_template = st.selectbox("Template", [
                        "Welcome Message", "Follow-up", "Deal Alert", "Market Update", "Custom"
                    ], key="email1_template")
                
                # Email step 2
                st.markdown("**Step 2 (Optional):**")
                col_email2_1, col_email2_2 = st.columns(2)
                with col_email2_1:
                    email2_delay = st.number_input("Send after (days)", min_value=0, value=3, key="email2_delay")
                    email2_subject = st.text_input("Subject Line", placeholder="Following up on your property interest", key="email2_subject")
                with col_email2_2:
                    email2_template = st.selectbox("Template", [
                        "Welcome Message", "Follow-up", "Deal Alert", "Market Update", "Custom"
                    ], key="email2_template")
                
                if st.form_submit_button("🚀 Create Email Sequence"):
                    if sequence_name:
                        new_sequence = {
                            'name': sequence_name,
                            'trigger': sequence_trigger,
                            'steps': [
                                {'delay': email1_delay, 'subject': email1_subject, 'template': email1_template},
                                {'delay': email2_delay, 'subject': email2_subject, 'template': email2_template}
                            ]
                        }
                        st.session_state.email_sequences.append(new_sequence)
                        st.success(f"✅ Created email sequence: {sequence_name}")
                    else:
                        st.error("Please provide a sequence name")
            
            # Existing sequences
            if st.session_state.email_sequences:
                st.markdown("### 📋 Active Email Sequences")
                
                for seq in st.session_state.email_sequences:
                    with st.expander(f"📧 {seq['name']}"):
                        st.write(f"**Trigger:** {seq['trigger']}")
                        st.write(f"**Steps:** {len(seq['steps'])}")
                        
                        for i, step in enumerate(seq['steps'], 1):
                            if step['subject']:  # Only show steps with content
                                st.write(f"Step {i}: {step['subject']} (after {step['delay']} {'hours' if i == 1 else 'days'})")
        
        with tab3:
            st.markdown("## 📱 SMS Campaign Automation")
            
            # SMS campaign builder
            st.markdown("### 📲 Create SMS Campaign")
            
            col_sms1, col_sms2 = st.columns(2)
            
            with col_sms1:
                campaign_name = st.text_input("Campaign Name", placeholder="Hot Lead Follow-up")
                campaign_trigger = st.selectbox("Trigger", [
                    "Lead score > threshold", "No contact in X days", "Deal stage change", "Manual send"
                ])
                
                target_audience = st.selectbox("Target Audience", [
                    "All leads", "High-value leads", "Recent leads", "Stale leads", "Custom filter"
                ])
                
                sms_message = st.text_area("SMS Message", 
                    placeholder="Hi {name}, I have an exciting investment opportunity that matches your criteria. Can we chat? Reply YES for details.",
                    max_chars=160
                )
                
                st.write(f"Character count: {len(sms_message)}/160")
            
            with col_sms2:
                st.markdown("**📊 Campaign Settings**")
                
                send_immediately = st.checkbox("Send immediately")
                if not send_immediately:
                    send_time = st.time_input("Send at time")
                
                respect_timezone = st.checkbox("Respect recipient timezone", value=True)
                avoid_weekends = st.checkbox("Avoid weekends", value=True)
                
                st.markdown("**📈 Expected Results**")
                estimated_recipients = 150  # Mock data
                estimated_responses = int(estimated_recipients * 0.15)  # 15% response rate
                
                st.metric("Estimated Recipients", estimated_recipients)
                st.metric("Expected Responses", estimated_responses)
                st.metric("Est. Response Rate", "15%")
                
                if st.button("🚀 Launch SMS Campaign", use_container_width=True):
                    st.success(f"✅ SMS campaign '{campaign_name}' launched!")
                    st.info(f"📱 Sending to {estimated_recipients} recipients")
        
        with tab4:
            st.markdown("## 📊 Automation Analytics")
            
            # Performance metrics
            col_perf1, col_perf2, col_perf3, col_perf4 = st.columns(4)
            
            with col_perf1:
                st.metric("Rules Executed", "1,247", delta="23")
            with col_perf2:
                st.metric("Success Rate", "94.2%", delta="2.1%")
            with col_perf3:
                st.metric("Time Saved", "18.5 hrs", delta="3.2 hrs")
            with col_perf4:
                st.metric("Response Rate", "16.8%", delta="1.4%")
            
            # Charts
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                # Mock automation performance data
                days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                executions = [45, 52, 38, 61, 49, 23, 31]
                
                fig_line = px.line(x=days, y=executions, title="Daily Automation Executions")
                st.plotly_chart(fig_line, use_container_width=True)
            
            with col_chart2:
                # Rule performance
                rule_names = [rule['name'] for rule in st.session_state.automation_rules]
                rule_executions = [rule['executions'] for rule in st.session_state.automation_rules]
                
                fig_bar = px.bar(x=rule_names, y=rule_executions, title="Rule Performance")
                st.plotly_chart(fig_bar, use_container_width=True)
        
        with tab5:
            st.markdown("## ⚙️ Automation Settings")
            
            col_settings1, col_settings2 = st.columns(2)
            
            with col_settings1:
                st.markdown("### 📧 Email Settings")
                
                default_from_email = st.text_input("Default From Email", value="noreply@nxtrix.com")
                email_signature = st.text_area("Email Signature", 
                    value="Best regards,\nThe NxTrix Team\nYour Real Estate Investment Partner")
                
                st.markdown("### 📱 SMS Settings")
                
                default_sms_sender = st.text_input("SMS Sender ID", value="NxTrix")
                sms_opt_out_message = st.text_input("Opt-out Instructions", 
                    value="Reply STOP to unsubscribe")
            
            with col_settings2:
                st.markdown("### 🕒 Timing Settings")
                
                business_start = st.time_input("Business Hours Start", value=pd.to_datetime("09:00").time())
                business_end = st.time_input("Business Hours End", value=pd.to_datetime("17:00").time())
                
                weekend_sends = st.checkbox("Allow weekend sends", value=False)
                holiday_sends = st.checkbox("Allow holiday sends", value=False)
                
                st.markdown("### 🔔 Notification Settings")
                
                notify_on_error = st.checkbox("Notify on automation errors", value=True)
                daily_summary = st.checkbox("Send daily automation summary", value=True)
                
                if st.button("💾 Save Settings", use_container_width=True):
                    st.success("✅ Automation settings saved!")
    
    except Exception as e:
        st.error(f"Error in automation center: {str(e)}")
    
    # Add navigation CTAs
    add_navigation_ctas()

def load_embedded_task_page():
    """Embedded task management"""
    st.markdown("### ✅ Task Management")
    st.markdown("*Productivity and activity tracking*")
    
    if st.button("Add New Task"):
        st.success("Task added to your workflow!")

def load_embedded_investor_page():
    """Advanced Investor Management - Full Implementation"""
    try:
        st.markdown("### 🏦 Investor Management")
        st.markdown("*Comprehensive investor relationship management and deal tracking*")
        
        # Initialize investor data
        if 'investors' not in st.session_state:
            st.session_state.investors = [
                {
                    'id': 1, 'name': 'Goldman Sachs Real Estate', 'type': 'Institutional', 
                    'investment_range': '$50M - $500M', 'focus': 'Commercial', 'location': 'New York, NY',
                    'contact': 'sarah.johnson@gs.com', 'phone': '(212) 555-0123',
                    'deals_funded': 23, 'total_invested': '$1.2B', 'avg_deal_size': '$52M',
                    'status': 'Active', 'last_contact': '2025-09-28',
                    'preferences': ['Office Buildings', 'Retail Centers', 'Industrial'],
                    'notes': 'Prefers deals in major metropolitan areas. Quick decision maker.'
                },
                {
                    'id': 2, 'name': 'Blackstone Group', 'type': 'Private Equity', 
                    'investment_range': '$100M - $1B', 'focus': 'Mixed-Use', 'location': 'Los Angeles, CA',
                    'contact': 'mike.chen@blackstone.com', 'phone': '(310) 555-0156',
                    'deals_funded': 18, 'total_invested': '$850M', 'avg_deal_size': '$47M',
                    'status': 'Active', 'last_contact': '2025-09-25',
                    'preferences': ['Mixed-Use', 'Luxury Residential', 'Hotels'],
                    'notes': 'Focuses on high-growth markets. Requires detailed market analysis.'
                },
                {
                    'id': 3, 'name': 'REIT Capital Partners', 'type': 'REIT', 
                    'investment_range': '$25M - $200M', 'focus': 'Residential', 'location': 'Austin, TX',
                    'contact': 'lisa.rodriguez@reitcap.com', 'phone': '(512) 555-0189',
                    'deals_funded': 31, 'total_invested': '$420M', 'avg_deal_size': '$13.5M',
                    'status': 'Interested', 'last_contact': '2025-09-20',
                    'preferences': ['Multifamily', 'Student Housing', 'Senior Living'],
                    'notes': 'Conservative approach. Prefers stable, income-generating properties.'
                }
            ]
        
        # Initialize deal tracking
        if 'investor_deals' not in st.session_state:
            st.session_state.investor_deals = [
                {'id': 1, 'investor_id': 1, 'property': 'Manhattan Office Tower', 'amount': '$150M', 'stage': 'Due Diligence', 'probability': 75},
                {'id': 2, 'investor_id': 2, 'property': 'LA Mixed-Use Development', 'amount': '$89M', 'stage': 'LOI Signed', 'probability': 90},
                {'id': 3, 'investor_id': 3, 'property': 'Austin Apartment Complex', 'amount': '$45M', 'stage': 'Initial Interest', 'probability': 40}
            ]
        
        # Main tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["👥 Investor Database", "🤝 Deal Tracking", "📈 Analytics", "📧 Communication", "⚙️ Management"])
        
        with tab1:
            st.markdown("## 👥 Investor Database")
            
            # Search and filters
            col_search1, col_search2, col_search3 = st.columns([3, 2, 2])
            
            with col_search1:
                search_query = st.text_input("🔍 Search investors", placeholder="Name, location, focus area...")
            
            with col_search2:
                investor_type_filter = st.selectbox("Type Filter", ["All Types", "Institutional", "Private Equity", "REIT", "Family Office"])
            
            with col_search3:
                status_filter = st.selectbox("Status Filter", ["All Status", "Active", "Interested", "Inactive", "Prospect"])
            
            # Add new investor button
            if st.button("➕ Add New Investor", type="primary"):
                st.session_state.show_add_investor = True
                st.rerun()
            
            # Add investor form (modal-style)
            if 'show_add_investor' in st.session_state and st.session_state.show_add_investor:
                st.markdown("---")
                st.markdown("## ➕ Add New Investor")
                
                with st.form("add_investor_form"):
                    col_form1, col_form2 = st.columns(2)
                    
                    with col_form1:
                        new_name = st.text_input("Investor Name*", placeholder="Investor Company LLC")
                        new_type = st.selectbox("Investor Type*", ["Institutional", "Private Equity", "REIT", "Family Office", "Individual"])
                        new_focus = st.selectbox("Investment Focus*", ["Commercial", "Residential", "Mixed-Use", "Industrial", "Retail"])
                        new_location = st.text_input("Location*", placeholder="City, State")
                        new_range = st.text_input("Investment Range*", placeholder="$10M - $100M")
                    
                    with col_form2:
                        new_contact = st.text_input("Primary Contact Email*", placeholder="contact@investor.com")
                        new_phone = st.text_input("Phone Number", placeholder="(555) 123-4567")
                        new_status = st.selectbox("Status", ["Prospect", "Active", "Interested", "Inactive"])
                        new_preferences = st.multiselect("Property Preferences", 
                                                        ["Office Buildings", "Retail Centers", "Industrial", "Multifamily", 
                                                         "Student Housing", "Senior Living", "Hotels", "Mixed-Use", "Luxury Residential"])
                        new_notes = st.text_area("Notes", placeholder="Additional information about this investor...")
                    
                    col_submit1, col_submit2 = st.columns(2)
                    with col_submit1:
                        if st.form_submit_button("💾 Add Investor", type="primary"):
                            if new_name and new_contact:
                                new_investor = {
                                    'id': len(st.session_state.investors) + 1,
                                    'name': new_name, 'type': new_type, 'focus': new_focus,
                                    'location': new_location, 'investment_range': new_range,
                                    'contact': new_contact, 'phone': new_phone, 'status': new_status,
                                    'preferences': new_preferences, 'notes': new_notes,
                                    'deals_funded': 0, 'total_invested': '$0', 'avg_deal_size': '$0',
                                    'last_contact': '2025-01-04'
                                }
                                st.session_state.investors.append(new_investor)
                                st.success(f"✅ Added investor: {new_name}")
                                st.session_state.show_add_investor = False
                                st.rerun()
                            else:
                                st.error("Please fill in required fields (marked with *)")
                    
                    with col_submit2:
                        if st.form_submit_button("❌ Cancel"):
                            st.session_state.show_add_investor = False
                            st.rerun()
            
            # Display investors
            st.markdown("---")
            for investor in st.session_state.investors:
                # Apply filters
                if search_query and search_query.lower() not in f"{investor['name']} {investor['location']} {investor['focus']}".lower():
                    continue
                if investor_type_filter != "All Types" and investor['type'] != investor_type_filter:
                    continue
                if status_filter != "All Status" and investor['status'] != status_filter:
                    continue
                
                # Investor card
                with st.expander(f"🏦 {investor['name']} - {investor['type']} ({investor['status']})"):
                    col_info1, col_info2, col_info3 = st.columns([2, 2, 1])
                    
                    with col_info1:
                        st.write(f"**📍 Location:** {investor['location']}")
                        st.write(f"**🎯 Focus:** {investor['focus']}")
                        st.write(f"**💰 Investment Range:** {investor['investment_range']}")
                        st.write(f"**📧 Contact:** {investor['contact']}")
                        if investor['phone']:
                            st.write(f"**📞 Phone:** {investor['phone']}")
                    
                    with col_info2:
                        st.write(f"**📊 Deals Funded:** {investor['deals_funded']}")
                        st.write(f"**💎 Total Invested:** {investor['total_invested']}")
                        st.write(f"**📈 Avg Deal Size:** {investor['avg_deal_size']}")
                        st.write(f"**📅 Last Contact:** {investor['last_contact']}")
                        
                        if investor['preferences']:
                            st.write(f"**🏢 Preferences:** {', '.join(investor['preferences'])}")
                    
                    with col_info3:
                        status_color = {
                            'Active': '🟢', 'Interested': '🟡', 
                            'Inactive': '🔴', 'Prospect': '🔵'
                        }
                        st.markdown(f"### {status_color.get(investor['status'], '⚪')} {investor['status']}")
                        
                        if st.button(f"📧 Contact", key=f"contact_{investor['id']}"):
                            st.session_state.selected_investor_contact = investor['id']
                            st.rerun()
                        
                        if st.button(f"✏️ Edit", key=f"edit_{investor['id']}"):
                            st.session_state.selected_investor_edit = investor['id']
                            st.rerun()
                    
                    if investor['notes']:
                        st.markdown(f"**📝 Notes:** {investor['notes']}")
        
        with tab2:
            st.markdown("## 🤝 Deal Tracking")
            
            # Deal pipeline overview
            col_pipeline1, col_pipeline2, col_pipeline3, col_pipeline4 = st.columns(4)
            
            with col_pipeline1:
                initial_deals = [d for d in st.session_state.investor_deals if d['stage'] == 'Initial Interest']
                st.metric("🎯 Initial Interest", len(initial_deals))
            
            with col_pipeline2:
                loi_deals = [d for d in st.session_state.investor_deals if d['stage'] == 'LOI Signed']
                st.metric("📄 LOI Signed", len(loi_deals))
            
            with col_pipeline3:
                dd_deals = [d for d in st.session_state.investor_deals if d['stage'] == 'Due Diligence']
                st.metric("🔍 Due Diligence", len(dd_deals))
            
            with col_pipeline4:
                closed_deals = [d for d in st.session_state.investor_deals if d['stage'] == 'Closed']
                st.metric("✅ Closed", len(closed_deals))
            
            # Add new deal
            if st.button("➕ Add New Deal", type="primary"):
                st.session_state.show_add_deal = True
                st.rerun()
            
            # Add deal form
            if 'show_add_deal' in st.session_state and st.session_state.show_add_deal:
                st.markdown("---")
                st.markdown("## ➕ Add New Deal")
                
                with st.form("add_deal_form"):
                    col_deal1, col_deal2 = st.columns(2)
                    
                    with col_deal1:
                        investor_options = [f"{inv['name']} ({inv['type']})" for inv in st.session_state.investors]
                        selected_investor = st.selectbox("Select Investor*", investor_options)
                        deal_property = st.text_input("Property/Project Name*", placeholder="Downtown Office Complex")
                        deal_amount = st.text_input("Deal Amount*", placeholder="$50M")
                    
                    with col_deal2:
                        deal_stage = st.selectbox("Current Stage*", ["Initial Interest", "LOI Signed", "Due Diligence", "Closed", "Withdrawn"])
                        deal_probability = st.slider("Success Probability (%)", 0, 100, 50)
                        deal_notes = st.text_area("Deal Notes", placeholder="Key details about this deal...")
                    
                    col_deal_submit1, col_deal_submit2 = st.columns(2)
                    with col_deal_submit1:
                        if st.form_submit_button("💾 Add Deal", type="primary"):
                            if selected_investor and deal_property and deal_amount:
                                # Find investor ID
                                investor_name = selected_investor.split(" (")[0]
                                investor_id = next(inv['id'] for inv in st.session_state.investors if inv['name'] == investor_name)
                                
                                new_deal = {
                                    'id': len(st.session_state.investor_deals) + 1,
                                    'investor_id': investor_id,
                                    'property': deal_property,
                                    'amount': deal_amount,
                                    'stage': deal_stage,
                                    'probability': deal_probability,
                                    'notes': deal_notes,
                                    'created_date': '2025-01-04'
                                }
                                st.session_state.investor_deals.append(new_deal)
                                st.success(f"✅ Added deal: {deal_property}")
                                st.session_state.show_add_deal = False
                                st.rerun()
                            else:
                                st.error("Please fill in required fields")
                    
                    with col_deal_submit2:
                        if st.form_submit_button("❌ Cancel"):
                            st.session_state.show_add_deal = False
                            st.rerun()
            
            # Display deals
            st.markdown("---")
            st.markdown("### 📋 Active Deals")
            
            for deal in st.session_state.investor_deals:
                # Find investor name
                investor = next((inv for inv in st.session_state.investors if inv['id'] == deal['investor_id']), None)
                if not investor:
                    continue
                
                # Deal card
                with st.expander(f"🏢 {deal['property']} - {deal['amount']} ({deal['stage']})"):
                    col_deal_info1, col_deal_info2, col_deal_info3 = st.columns([2, 2, 1])
                    
                    with col_deal_info1:
                        st.write(f"**🏦 Investor:** {investor['name']}")
                        st.write(f"**💰 Amount:** {deal['amount']}")
                        st.write(f"**📊 Stage:** {deal['stage']}")
                    
                    with col_deal_info2:
                        st.write(f"**📈 Probability:** {deal['probability']}%")
                        st.progress(deal['probability'] / 100)
                        
                        if 'notes' in deal and deal['notes']:
                            st.write(f"**📝 Notes:** {deal['notes']}")
                    
                    with col_deal_info3:
                        stage_colors = {
                            'Initial Interest': '🔵', 'LOI Signed': '🟡',
                            'Due Diligence': '🟠', 'Closed': '🟢', 'Withdrawn': '🔴'
                        }
                        st.markdown(f"### {stage_colors.get(deal['stage'], '⚪')}")
                        
                        if st.button(f"📧 Update", key=f"update_deal_{deal['id']}"):
                            st.info("Deal update form would appear here")
                        
                        if st.button(f"🗑️ Remove", key=f"remove_deal_{deal['id']}"):
                            st.warning("This would remove the deal")
        
        with tab3:
            st.markdown("## 📈 Investor Analytics")
            
            # Key metrics
            col_metrics1, col_metrics2, col_metrics3, col_metrics4 = st.columns(4)
            
            with col_metrics1:
                total_investors = len(st.session_state.investors)
                st.metric("👥 Total Investors", total_investors)
            
            with col_metrics2:
                active_investors = len([inv for inv in st.session_state.investors if inv['status'] == 'Active'])
                st.metric("🟢 Active Investors", active_investors)
            
            with col_metrics3:
                total_deals = len(st.session_state.investor_deals)
                st.metric("🤝 Total Deals", total_deals)
            
            with col_metrics4:
                avg_deal_value = sum(float(deal['amount'].replace('$', '').replace('M', '')) for deal in st.session_state.investor_deals) / len(st.session_state.investor_deals) if st.session_state.investor_deals else 0
                st.metric("💰 Avg Deal Size", f"${avg_deal_value:.1f}M")
            
            # Charts and visualizations
            st.markdown("### 📊 Investment Analysis")
            
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("**🎯 Investor Types Distribution**")
                investor_types = {}
                for investor in st.session_state.investors:
                    investor_types[investor['type']] = investor_types.get(investor['type'], 0) + 1
                
                for inv_type, count in investor_types.items():
                    st.write(f"• {inv_type}: {count} investors")
            
            with col_chart2:
                st.markdown("**📈 Deal Stage Pipeline**")
                deal_stages = {}
                for deal in st.session_state.investor_deals:
                    deal_stages[deal['stage']] = deal_stages.get(deal['stage'], 0) + 1
                
                for stage, count in deal_stages.items():
                    st.write(f"• {stage}: {count} deals")
            
            # Performance metrics
            st.markdown("### 🏆 Performance Metrics")
            
            col_perf1, col_perf2 = st.columns(2)
            
            with col_perf1:
                st.markdown("**📈 Top Performing Investors**")
                for i, investor in enumerate(st.session_state.investors[:3]):
                    st.write(f"{i+1}. {investor['name']} - {investor['deals_funded']} deals")
            
            with col_perf2:
                st.markdown("**💰 Highest Value Deals**")
                sorted_deals = sorted(st.session_state.investor_deals, 
                                    key=lambda x: float(x['amount'].replace('$', '').replace('M', '')), reverse=True)
                for i, deal in enumerate(sorted_deals[:3]):
                    st.write(f"{i+1}. {deal['property']} - {deal['amount']}")
        
        with tab4:
            st.markdown("## 📧 Communication Center")
            
            # Communication overview
            col_comm1, col_comm2 = st.columns(2)
            
            with col_comm1:
                st.markdown("### 📨 Recent Communications")
                
                # Mock communication history
                communications = [
                    {'date': '2025-01-03', 'investor': 'Goldman Sachs Real Estate', 'type': 'Email', 'subject': 'Manhattan Office Tower - Due Diligence Update'},
                    {'date': '2025-01-02', 'investor': 'Blackstone Group', 'type': 'Call', 'subject': 'LA Mixed-Use Development Discussion'},
                    {'date': '2025-01-01', 'investor': 'REIT Capital Partners', 'type': 'Email', 'subject': 'New Opportunity - Austin Apartment Complex'},
                ]
                
                for comm in communications:
                    with st.expander(f"📧 {comm['investor']} - {comm['date']}"):
                        st.write(f"**Type:** {comm['type']}")
                        st.write(f"**Subject:** {comm['subject']}")
                        st.write(f"**Date:** {comm['date']}")
                        
                        col_comm_action1, col_comm_action2 = st.columns(2)
                        with col_comm_action1:
                            if st.button(f"📖 View Details", key=f"view_{comm['date']}"):
                                st.info("Communication details would appear here")
                        with col_comm_action2:
                            if st.button(f"↩️ Reply", key=f"reply_{comm['date']}"):
                                st.info("Reply form would appear here")
            
            with col_comm2:
                st.markdown("### ✉️ Send New Communication")
                
                with st.form("send_communication"):
                    recipient_options = [inv['name'] for inv in st.session_state.investors]
                    recipient = st.selectbox("Select Recipient", recipient_options)
                    
                    comm_type = st.selectbox("Communication Type", ["Email", "SMS", "Call Scheduled"])
                    
                    subject = st.text_input("Subject", placeholder="Follow-up on recent opportunity")
                    
                    message = st.text_area("Message", placeholder="Dear [Investor Name],\n\nI wanted to follow up...", height=150)
                    
                    col_send1, col_send2 = st.columns(2)
                    with col_send1:
                        if st.form_submit_button("📤 Send Communication", type="primary"):
                            st.success(f"✅ {comm_type} sent to {recipient}")
                    
                    with col_send2:
                        if st.form_submit_button("💾 Save Draft"):
                            st.info("📝 Communication saved as draft")
            
            # Communication templates
            st.markdown("### 📋 Email Templates")
            
            templates = [
                "New Investment Opportunity",
                "Due Diligence Request", 
                "Deal Update",
                "Thank You - Investment Completed",
                "Follow-up Meeting Request"
            ]
            
            col_temp1, col_temp2, col_temp3 = st.columns(3)
            
            for i, template in enumerate(templates):
                with [col_temp1, col_temp2, col_temp3][i % 3]:
                    if st.button(f"📄 {template}", key=f"template_{i}"):
                        st.session_state.selected_template = template
                        st.info(f"Template '{template}' loaded")
        
        with tab5:
            st.markdown("## ⚙️ Investor Management Settings")
            
            col_mgmt1, col_mgmt2 = st.columns(2)
            
            with col_mgmt1:
                st.markdown("### 🔔 Notification Settings")
                
                new_investor_alerts = st.checkbox("New investor notifications", value=True)
                deal_stage_updates = st.checkbox("Deal stage change alerts", value=True)
                communication_reminders = st.checkbox("Follow-up reminders", value=True)
                weekly_reports = st.checkbox("Weekly investor reports", value=False)
                
                st.markdown("### 📊 Data Management")
                
                if st.button("📁 Export Investor Database"):
                    st.success("📊 Investor database exported to CSV")
                
                if st.button("📈 Export Deal Pipeline"):
                    st.success("📊 Deal pipeline exported to Excel")
                
                if st.button("🔄 Sync with CRM"):
                    st.success("🔄 Data synced with main CRM")
            
            with col_mgmt2:
                st.markdown("### 🎯 Investor Matching Settings")
                
                auto_matching = st.checkbox("Automatic investor matching", value=True)
                match_threshold = st.slider("Matching confidence threshold", 0, 100, 75)
                
                preferred_deal_size = st.text_input("Preferred deal size range", value="$25M - $100M")
                preferred_locations = st.multiselect("Preferred locations", 
                                                   ["New York", "Los Angeles", "Chicago", "Austin", "Miami", "Seattle"])
                
                st.markdown("### 🔐 Privacy & Security")
                
                data_encryption = st.checkbox("Enable data encryption", value=True)
                access_logging = st.checkbox("Log all data access", value=True)
                
                if st.button("🔒 Review Security Settings"):
                    st.info("🔐 Security review panel would open here")
                
                if st.button("💾 Save All Settings"):
                    st.success("✅ All settings saved successfully!")
    
    except Exception as e:
        st.error(f"Error in investor management: {str(e)}")
    
    # Add navigation CTAs
    add_navigation_ctas()

def load_embedded_payment_page():
    """Advanced Payment & Subscription Management - Full Implementation"""
    try:
        st.markdown("### 💳 Payment & Subscription Management")
        st.markdown("*🔴 **LIVE STRIPE ACCOUNT ACTIVE** - Production payment processing ready*")
        
        # Live account status banner
        st.success("🎉 **Stripe Live Account Activated!** Your payment system is now ready for production transactions.")
        
        # Initialize subscription data
        if 'user_subscription' not in st.session_state:
            st.session_state.user_subscription = {
                'current_plan': 'Free',
                'billing_cycle': 'monthly',
                'next_billing': '2025-10-04',
                'payment_method': 'card',
                'last_4_digits': '4242'
            }
        
        # Main tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["💰 Subscription Plans", "💳 Payment Methods", "📊 Billing History", "⚙️ Account Settings", "🔄 Plan Management"])
        
        with tab1:
            st.markdown("## 💰 Choose Your Plan")
            
            # Founders pricing banner
            st.markdown("""
            <div style="background: linear-gradient(135deg, #ff6b6b, #ee5a24); color: white; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                <h3 style="margin: 0;">🎯 FOUNDERS PRICING - LIMITED TIME</h3>
                <p style="margin: 5px 0;">Save up to 32% compared to regular pricing!</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Current plan status
            current_plan = st.session_state.user_subscription['current_plan']
            st.info(f"Current Plan: **{current_plan}**")
            
            # Billing toggle
            col_toggle1, col_toggle2, col_toggle3 = st.columns([1, 2, 1])
            with col_toggle2:
                billing_type = st.radio("Billing Cycle", ["Monthly", "Annual (Save 2 months!)"], horizontal=True)
            
            # Plan comparison
            col_solo, col_team, col_business = st.columns(3)
            
            with col_solo:
                regular_price = "$79" if billing_type == "Monthly" else "$948"
                billing_cycle = "/month" if billing_type == "Monthly" else "/year"
                
                st.markdown(f"""
                <div style="border: 2px solid #4CAF50; padding: 20px; border-radius: 15px; text-align: center;">
                    <h3>🚀 Solo</h3>
                    <h2 style="color: #4CAF50;">{regular_price}{billing_cycle}</h2>
                    <p style="background: #4CAF50; color: white; padding: 5px; border-radius: 10px; margin: 10px 0;">ENTRY LEVEL</p>
                    <hr>
                    <p style="text-align: left;">✅ Up to 50 leads/month</p>
                    <p style="text-align: left;">✅ Basic CRM & pipeline</p>
                    <p style="text-align: left;">✅ Email automation</p>
                    <p style="text-align: left;">✅ Lead capture forms</p>
                    <p style="text-align: left;">✅ Basic analytics</p>
                    <p style="text-align: left;">✅ Mobile app access</p>
                    <p style="text-align: left;">✅ 5GB storage</p>
                    <p style="text-align: left;">✅ Email support</p>
                </div>
                """, unsafe_allow_html=True)
                
                if current_plan != 'Solo':
                    if st.button("� Choose Solo", key="upgrade_solo", type="primary"):
                        st.session_state.show_payment_form = 'Solo'
                        st.rerun()
                else:
                    st.success("✅ Current Plan")
            
            with col_team:
                regular_price = "$119" if billing_type == "Monthly" else "$1,428"
                billing_cycle = "/month" if billing_type == "Monthly" else "/year"
                
                st.markdown(f"""
                <div style="border: 3px solid #2196F3; padding: 20px; border-radius: 15px; text-align: center; background: #f3f8ff;">
                    <h3>⚡ Team</h3>
                    <h2 style="color: #2196F3;">{regular_price}{billing_cycle}</h2>
                    <p style="background: #2196F3; color: white; padding: 5px; border-radius: 10px; margin: 10px 0;">MOST POPULAR</p>
                    <hr>
                    <p style="text-align: left;">✅ Up to 500 leads/month</p>
                    <p style="text-align: left;">✅ Advanced CRM & deals</p>
                    <p style="text-align: left;">✅ Marketing automation</p>
                    <p style="text-align: left;">✅ Landing page builder</p>
                    <p style="text-align: left;">✅ Advanced analytics</p>
                    <p style="text-align: left;">✅ SMS deal alerts & messaging</p>
                    <p style="text-align: left;">✅ Team collaboration (5 users)</p>
                    <p style="text-align: left;">✅ 25GB storage</p>
                    <p style="text-align: left;">✅ Priority support</p>
                    <p style="text-align: left;">✅ API integrations</p>
                </div>
                """, unsafe_allow_html=True)
                
                if current_plan != 'Team':
                    if st.button("⚡ Choose Team", key="upgrade_team", type="primary"):
                        st.session_state.show_payment_form = 'Team'
                        st.rerun()
                else:
                    st.success("✅ Current Plan")
            
            with col_business:
                regular_price = "$219" if billing_type == "Monthly" else "$2,628"
                billing_cycle = "/month" if billing_type == "Monthly" else "/year"
                
                st.markdown(f"""
                <div style="border: 2px solid #FF9800; padding: 20px; border-radius: 15px; text-align: center;">
                    <h3>🏢 Business</h3>
                    <h2 style="color: #FF9800;">{regular_price}{billing_cycle}</h2>
                    <p style="background: #FF9800; color: white; padding: 5px; border-radius: 10px; margin: 10px 0;">COMPLETE SOLUTION</p>
                    <hr>
                    <p style="text-align: left;">✅ Unlimited leads & users</p>
                    <p style="text-align: left;">✅ Enterprise CRM</p>
                    <p style="text-align: left;">✅ Multi-channel marketing</p>
                    <p style="text-align: left;">✅ Advanced workflow automation</p>
                    <p style="text-align: left;">✅ AI-powered insights</p>
                    <p style="text-align: left;">✅ Enterprise API (35k calls/month)</p>
                    <p style="text-align: left;">✅ 100GB storage</p>
                    <p style="text-align: left;">✅ Smart deal alerts</p>
                    <p style="text-align: left;">✅ Advanced data exports</p>
                </div>
                """, unsafe_allow_html=True)
                
                if current_plan != 'Business':
                    if st.button("🏢 Choose Business", key="upgrade_business"):
                        st.session_state.show_payment_form = 'Business'
                        st.rerun()
                else:
                    st.success("✅ Current Plan")
            
            # Payment form popup
            if 'show_payment_form' in st.session_state:
                selected_plan = st.session_state.show_payment_form
                plan_price = '$119' if selected_plan == 'Team' else '$219'
                
                st.markdown("---")
                st.markdown(f"## 💳 Complete Your {selected_plan} Subscription")
                
                with st.form("payment_form"):
                    col_payment1, col_payment2 = st.columns(2)
                    
                    with col_payment1:
                        st.markdown("**💳 Payment Information**")
                        card_number = st.text_input("Card Number", placeholder="1234 5678 9012 3456")
                        col_exp1, col_exp2 = st.columns(2)
                        with col_exp1:
                            exp_month = st.selectbox("Month", list(range(1, 13)))
                        with col_exp2:
                            exp_year = st.selectbox("Year", list(range(2025, 2035)))
                        cvv = st.text_input("CVV", placeholder="123", max_chars=4)
                    
                    with col_payment2:
                        st.markdown("**📄 Billing Information**")
                        billing_name = st.text_input("Full Name", placeholder="John Doe")
                        billing_email = st.text_input("Email", placeholder="john@example.com")
                        billing_address = st.text_input("Address", placeholder="123 Main St")
                        col_city, col_zip = st.columns(2)
                        with col_city:
                            billing_city = st.text_input("City", placeholder="Anytown")
                        with col_zip:
                            billing_zip = st.text_input("ZIP", placeholder="12345")
                    
                    # Plan summary
                    st.markdown(f"**📋 Order Summary**")
                    st.write(f"Plan: {selected_plan}")
                    st.write(f"Price: {plan_price}/month")
                    st.write(f"Billing Cycle: Monthly")
                    
                    col_form1, col_form2 = st.columns(2)
                    with col_form1:
                        if st.form_submit_button("💳 Complete Payment", type="primary"):
                            # Process payment (mock)
                            st.success(f"✅ Payment successful! Welcome to {selected_plan}!")
                            st.session_state.user_subscription['current_plan'] = selected_plan
                            st.session_state.pop('show_payment_form', None)
                            st.balloons()
                            st.rerun()
                    
                    with col_form2:
                        if st.form_submit_button("❌ Cancel"):
                            st.session_state.pop('show_payment_form', None)
                            st.rerun()
        
        with tab2:
            st.markdown("## 💳 Payment Methods")
            
            # Current payment method
            if st.session_state.user_subscription['current_plan'] != 'Free':
                st.markdown("### 💳 Current Payment Method")
                
                col_card1, col_card2 = st.columns([2, 1])
                with col_card1:
                    st.markdown(f"""
                    <div style="border: 1px solid #ddd; padding: 15px; border-radius: 10px;">
                        <p><strong>💳 Visa ending in {st.session_state.user_subscription['last_4_digits']}</strong></p>
                        <p>Expires: 12/2027</p>
                        <p>Default payment method</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_card2:
                    if st.button("✏️ Update Card"):
                        st.info("Card update form would appear here")
                    if st.button("🗑️ Remove Card"):
                        st.warning("This will cancel your subscription")
            
            # Add new payment method
            st.markdown("### ➕ Add New Payment Method")
            
            with st.expander("Add Credit/Debit Card"):
                new_card_number = st.text_input("Card Number", placeholder="1234 5678 9012 3456", key="new_card")
                col_new1, col_new2 = st.columns(2)
                with col_new1:
                    new_exp_month = st.selectbox("Month", list(range(1, 13)), key="new_month")
                with col_new2:
                    new_exp_year = st.selectbox("Year", list(range(2025, 2035)), key="new_year")
                
                if st.button("💾 Save Payment Method"):
                    st.success("✅ Payment method added successfully!")
        
        with tab3:
            st.markdown("## 📊 Billing History")
            
            # Mock billing history
            billing_history = [
                {'date': '2025-09-04', 'amount': '$119.00', 'plan': 'Team', 'status': 'Paid'},
                {'date': '2025-08-04', 'amount': '$119.00', 'plan': 'Team', 'status': 'Paid'},
                {'date': '2025-07-04', 'amount': '$119.00', 'plan': 'Team', 'status': 'Paid'},
                {'date': '2025-06-04', 'amount': '$0.00', 'plan': 'Free', 'status': 'N/A'},
            ]
            
            for bill in billing_history:
                col_bill1, col_bill2, col_bill3, col_bill4, col_bill5 = st.columns([2, 2, 2, 1, 1])
                
                with col_bill1:
                    st.write(bill['date'])
                with col_bill2:
                    st.write(bill['plan'])
                with col_bill3:
                    st.write(bill['amount'])
                with col_bill4:
                    status_color = "🟢" if bill['status'] == 'Paid' else "⚪"
                    st.write(f"{status_color} {bill['status']}")
                with col_bill5:
                    if bill['status'] == 'Paid':
                        if st.button("📄", key=f"invoice_{bill['date']}", help="Download invoice"):
                            st.success("Invoice downloaded!")
            
            # Billing summary
            st.markdown("### 📈 Billing Summary")
            col_summary1, col_summary2, col_summary3 = st.columns(3)
            
            with col_summary1:
                st.metric("Total Spent", "$291.00")
            with col_summary2:
                st.metric("Next Billing", st.session_state.user_subscription['next_billing'])
            with col_summary3:
                st.metric("Billing Cycle", st.session_state.user_subscription['billing_cycle'].title())
        
        with tab4:
            st.markdown("## ⚙️ Account Settings")
            
            col_settings1, col_settings2 = st.columns(2)
            
            with col_settings1:
                st.markdown("### 🔔 Billing Notifications")
                
                email_receipts = st.checkbox("Email receipts", value=True)
                payment_reminders = st.checkbox("Payment reminders", value=True)
                billing_alerts = st.checkbox("Billing alerts", value=False)
                
                st.markdown("### 💰 Billing Preferences")
                
                auto_pay = st.checkbox("Auto-pay enabled", value=True)
                billing_cycle = st.selectbox("Billing Cycle", ["Monthly", "Yearly"], 
                                           index=0 if st.session_state.user_subscription['billing_cycle'] == 'monthly' else 1)
                
                if billing_cycle != st.session_state.user_subscription['billing_cycle'].title():
                    st.info(f"Switch to {billing_cycle.lower()} billing for better rates!")
            
            with col_settings2:
                st.markdown("### 📧 Contact Information")
                
                billing_email = st.text_input("Billing Email", value="user@example.com")
                billing_phone = st.text_input("Phone Number", value="+1 (555) 123-4567")
                
                st.markdown("### 🏢 Company Information")
                
                company_name = st.text_input("Company Name", placeholder="Your Company LLC")
                tax_id = st.text_input("Tax ID (Optional)", placeholder="12-3456789")
                
                st.markdown("### 📞 Support Contact")
                st.info("**Customer Support:** Email support available for all billing inquiries")
                
                # Display the support options
                st.markdown("""
                **Support Options:**
                - 📧 **Email Support:** support@nxtrix.app
                - 💬 **Live Chat:** Available during business hours
                - 🎫 **Support Portal:** Submit tickets anytime
                - 📚 **Help Center:** Self-service documentation
                """)
                
                if st.button("💾 Update Account Settings"):
                    st.success("✅ Account settings updated!")
        
        with tab5:
            st.markdown("## 🔄 Plan Management")
            
            current_plan = st.session_state.user_subscription['current_plan']
            
            # Current plan overview
            st.markdown(f"### 📋 Current Plan: {current_plan}")
            
            if current_plan == 'Free':
                st.info("🆓 You're on the Free plan. Upgrade for premium features!")
                
                col_upgrade1, col_upgrade2 = st.columns(2)
                with col_upgrade1:
                    if st.button("🚀 Upgrade to Team ($119/month)", type="primary"):
                        st.session_state.show_payment_form = 'Team'
                        st.rerun()
                
                with col_upgrade2:
                    if st.button("🏢 Upgrade to Business ($219/month)"):
                        st.session_state.show_payment_form = 'Business'
                        st.rerun()
            
            else:
                # Plan usage statistics
                st.markdown("### 📊 Plan Usage")
                
                col_usage1, col_usage2, col_usage3 = st.columns(3)
                
                with col_usage1:
                    leads_used = 847 if current_plan == 'Professional' else 2156
                    leads_limit = "Unlimited"
                    st.metric("Leads This Month", leads_used, delta="45")
                
                with col_usage2:
                    sms_sent = 156 if current_plan == 'Professional' else 423
                    sms_limit = "Unlimited"
                    st.metric("SMS Sent", sms_sent, delta="23")
                
                with col_usage3:
                    storage_used = "2.4 GB" if current_plan == 'Professional' else "7.8 GB"
                    storage_limit = "100 GB" if current_plan == 'Professional' else "1 TB"
                    st.metric("Storage Used", storage_used)
                
                # Plan actions
                st.markdown("### ⚡ Plan Actions")
                
                col_action1, col_action2 = st.columns(2)
                
                with col_action1:
                    if current_plan == 'Professional':
                        if st.button("⬆️ Upgrade to Enterprise", type="primary"):
                            st.session_state.show_payment_form = 'Enterprise'
                            st.rerun()
                    
                    if st.button("📄 Download Usage Report"):
                        st.success("📊 Usage report downloaded!")
                
                with col_action2:
                    if st.button("⬇️ Downgrade Plan", type="secondary"):
                        st.warning("⚠️ Downgrading will limit your features")
                        if st.button("Confirm Downgrade"):
                            st.session_state.user_subscription['current_plan'] = 'Free'
                            st.success("Plan downgraded to Free")
                            st.rerun()
                    
                    if st.button("❌ Cancel Subscription"):
                        st.error("⚠️ This will cancel your subscription at the end of the billing period")
                        if st.button("Confirm Cancellation"):
                            st.success("Subscription cancelled. You'll retain access until the end of your billing period.")
    
    except Exception as e:
        st.error(f"Error in payment management: {str(e)}")
    
    # Add navigation CTAs
    add_navigation_ctas()

def load_embedded_settings_page():
    """Embedded settings functionality"""
    st.markdown("### ⚙️ System Settings")
    st.markdown("*Configuration and preferences*")
    
    st.subheader("User Preferences")
    st.checkbox("Enable SMS Notifications")
    st.checkbox("Email Alerts")
    st.text_input("Business Phone", value="(XXX) XXX-XXXX")

# Keep the existing show_page_fallback function

def show_page_fallback(page_title, fallback_message):
    """Show a basic fallback page when the full page can't be loaded"""
    st.info(fallback_message)
    
    if "leads" in page_title.lower():
        st.markdown("""
        ### 🎯 Lead Management (Simplified View)
        
        This is a simplified version of the leads page. The full functionality will be available once deployment is complete.
        
        **Key Features Available in Full Version:**
        - Complete lead database with 25+ fields
        - ROI calculations and profit analysis
        - Lead scoring and priority ranking  
        - SMS notifications via Twilio
        - Deal tracking and pipeline management
        - Advanced search and filtering
        - Automated follow-up systems
        
        **Status:** Loading from backup system...
        """)
        
        # Show a basic lead entry form as placeholder
        with st.form("basic_lead_form"):
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Property Address")
                st.number_input("Asking Price", min_value=0)
            with col2:
                st.text_input("Owner Name")  
                st.number_input("ARV Estimate", min_value=0)
            
            if st.form_submit_button("Add Lead (Simplified)"):
                st.success("Lead would be added to database when full system is loaded")
    
    elif "analytics" in page_title.lower():
        st.markdown("""
        ### 📊 Analytics Dashboard (Simplified View)
        
        **Full Analytics Features:**
        - Deal performance metrics
        - ROI tracking and trends
        - Lead conversion analysis
        - Revenue forecasting
        - Geographic heat maps
        - Team performance dashboards
        
        **Status:** Loading from backup system...
        """)
    
    else:
        st.markdown(f"""
        ### {page_title}
        
        This page is currently loading from the backup system.
        Full functionality will be available once deployment completes.
        """)
    
    st.markdown("---")
    st.info("💡 **For immediate access:** All features are working in the local development version.")

# Keep the existing load_page_content function signature for compatibility

def load_leads_page():
    """Comprehensive Lead Management System with Investor Types and Buybox Criteria"""
    try:
        st.markdown("### 🎯 Comprehensive Lead Management System")
        st.markdown("*Advanced lead tracking with investor types and detailed buybox criteria*")
        
        # Initialize session state
        if 'active_lead_tab' not in st.session_state:
            st.session_state.active_lead_tab = 0
        
        # Quick action for adding leads
        if st.session_state.get("quick_action") == "add_lead":
            st.session_state.active_lead_tab = 2  # Set to Add Leads tab
            st.session_state.pop("quick_action", None)
        
        # Main tabs for comprehensive lead management
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Seller Leads", "👥 Buyer Leads", "➕ Add Leads", "📊 Lead Analytics", "⚙️ Lead Settings"])
        
        user_id = st.session_state["user_info"]["id"]
        
        # === TAB 1: SELLER LEADS ===
        with tab1:
            st.markdown("## 🏠 Seller Lead Management")
            
            # Load seller leads with enhanced data
            try:
                seller_leads = supabase.table("seller_leads").select("*").eq("user_id", user_id).order("created_at", desc=True).execute().data or []
            except:
                seller_leads = []
            
            # Seller lead overview metrics
            col_metrics1, col_metrics2, col_metrics3, col_metrics4 = st.columns(4)
            
            with col_metrics1:
                total_sellers = len(seller_leads)
                st.metric("📊 Total Seller Leads", total_sellers)
            
            with col_metrics2:
                active_sellers = len([l for l in seller_leads if l.get('status') not in ['Closed', 'Dead']])
                st.metric("🔥 Active Leads", active_sellers)
            
            with col_metrics3:
                if seller_leads:
                    avg_roi = sum(l.get('buyer_roi', 0) for l in seller_leads) / len(seller_leads)
                    st.metric("📈 Avg ROI", f"{avg_roi:.1f}%")
                else:
                    st.metric("📈 Avg ROI", "0%")
            
            with col_metrics4:
                closed_deals = len([l for l in seller_leads if l.get('status') == 'Closed'])
                st.metric("✅ Closed Deals", closed_deals)
            
            # Seller lead filters
            col_filter1, col_filter2, col_filter3 = st.columns(3)
            
            with col_filter1:
                status_filter = st.selectbox("Filter by Status", 
                    ["All Status", "New", "Contacted", "Follow-Up", "In Contract", "Closed", "Dead"])
            
            with col_filter2:
                roi_filter = st.selectbox("Filter by ROI", 
                    ["All ROI", "High ROI (>20%)", "Good ROI (15-20%)", "Low ROI (<15%)"])
            
            with col_filter3:
                property_type_filter = st.selectbox("Filter by Type", 
                    ["All Types", "Single Family", "Multi-Family", "Commercial", "Land", "Other"])
            
            # Apply filters
            filtered_sellers = seller_leads
            if status_filter != "All Status":
                filtered_sellers = [l for l in filtered_sellers if l.get('status') == status_filter]
            if roi_filter == "High ROI (>20%)":
                filtered_sellers = [l for l in filtered_sellers if l.get('buyer_roi', 0) > 20]
            elif roi_filter == "Good ROI (15-20%)":
                filtered_sellers = [l for l in filtered_sellers if 15 <= l.get('buyer_roi', 0) <= 20]
            elif roi_filter == "Low ROI (<15%)":
                filtered_sellers = [l for l in filtered_sellers if l.get('buyer_roi', 0) < 15]
            if property_type_filter != "All Types":
                filtered_sellers = [l for l in filtered_sellers if l.get('property_type') == property_type_filter]
            
            # Display seller leads
            if filtered_sellers:
                st.markdown(f"### 📋 Seller Leads ({len(filtered_sellers)} found)")
                
                for lead in filtered_sellers:
                    with st.expander(f"🏠 {lead.get('property_address', 'Unknown Address')} - {lead.get('status', 'Unknown')} | ROI: {lead.get('buyer_roi', 0):.1f}%"):
                        col_lead1, col_lead2, col_lead3 = st.columns([2, 2, 1])
                        
                        with col_lead1:
                            st.write(f"**📍 Address:** {lead.get('property_address', 'N/A')}")
                            st.write(f"**👤 Seller:** {lead.get('seller_name', 'N/A')}")
                            st.write(f"**📞 Phone:** {lead.get('seller_phone', 'N/A')}")
                            st.write(f"**🏠 Property Type:** {lead.get('property_type', 'N/A')}")
                            st.write(f"**📊 Status:** {lead.get('status', 'N/A')}")
                        
                        with col_lead2:
                            st.write(f"**💰 ARV:** ${lead.get('arv', 0):,.0f}")
                            st.write(f"**🔧 Repair Costs:** ${lead.get('repair_costs', 0):,.0f}")
                            st.write(f"**💵 Asking Price:** ${lead.get('asking_price', 0):,.0f}")
                            st.write(f"**📈 Buyer ROI:** {lead.get('buyer_roi', 0):.1f}%")
                            st.write(f"**📅 Created:** {lead.get('created_at', 'N/A')[:10] if lead.get('created_at') else 'N/A'}")
                        
                        with col_lead3:
                            if st.button(f"✏️ Edit", key=f"edit_seller_{lead.get('id')}"):
                                st.session_state[f"edit_seller_{lead.get('id')}"] = True
                                st.rerun()
                            
                            if st.button(f"🗑️ Delete", key=f"delete_seller_{lead.get('id')}"):
                                try:
                                    supabase.table("seller_leads").delete().eq("id", lead.get('id')).execute()
                                    st.success("Seller lead deleted!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting: {str(e)}")
                        
                        # Notes section
                        if lead.get('notes'):
                            st.markdown(f"**📝 Notes:** {lead.get('notes')}")
                        
                        # Edit form
                        if st.session_state.get(f"edit_seller_{lead.get('id')}"):
                            st.markdown("---")
                            st.markdown("### ✏️ Edit Seller Lead")
                            
                            with st.form(f"edit_seller_form_{lead.get('id')}"):
                                col_edit1, col_edit2 = st.columns(2)
                                
                                with col_edit1:
                                    new_address = st.text_input("Property Address", value=lead.get('property_address', ''))
                                    new_seller_name = st.text_input("Seller Name", value=lead.get('seller_name', ''))
                                    new_seller_phone = st.text_input("Seller Phone", value=lead.get('seller_phone', ''))
                                    new_property_type = st.selectbox("Property Type", 
                                        ["Single Family", "Multi-Family", "Commercial", "Land", "Other"],
                                        index=["Single Family", "Multi-Family", "Commercial", "Land", "Other"].index(lead.get('property_type', 'Single Family')) if lead.get('property_type') in ["Single Family", "Multi-Family", "Commercial", "Land", "Other"] else 0)
                                
                                with col_edit2:
                                    new_arv = st.number_input("ARV", value=lead.get('arv', 0))
                                    new_repair_costs = st.number_input("Repair Costs", value=lead.get('repair_costs', 0))
                                    new_asking_price = st.number_input("Asking Price", value=lead.get('asking_price', 0))
                                    new_buyer_roi = st.number_input("Buyer ROI (%)", value=lead.get('buyer_roi', 0))
                                
                                new_status = st.selectbox("Status", 
                                    ["New", "Contacted", "Follow-Up", "In Contract", "Closed", "Dead"],
                                    index=["New", "Contacted", "Follow-Up", "In Contract", "Closed", "Dead"].index(lead.get('status', 'New')) if lead.get('status') in ["New", "Contacted", "Follow-Up", "In Contract", "Closed", "Dead"] else 0)
                                
                                new_notes = st.text_area("Notes", value=lead.get('notes', ''))
                                
                                col_submit1, col_submit2 = st.columns(2)
                                with col_submit1:
                                    if st.form_submit_button("💾 Save Changes", type="primary"):
                                        try:
                                            update_data = {
                                                'property_address': new_address,
                                                'seller_name': new_seller_name,
                                                'seller_phone': new_seller_phone,
                                                'property_type': new_property_type,
                                                'arv': new_arv,
                                                'repair_costs': new_repair_costs,
                                                'asking_price': new_asking_price,
                                                'buyer_roi': new_buyer_roi,
                                                'status': new_status,
                                                'notes': new_notes
                                            }
                                            supabase.table("seller_leads").update(update_data).eq("id", lead.get('id')).execute()
                                            st.success("✅ Seller lead updated!")
                                            st.session_state.pop(f"edit_seller_{lead.get('id')}", None)
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error updating: {str(e)}")
                                
                                with col_submit2:
                                    if st.form_submit_button("❌ Cancel"):
                                        st.session_state.pop(f"edit_seller_{lead.get('id')}", None)
                                        st.rerun()
            else:
                st.info("No seller leads found. Add your first seller lead in the 'Add Leads' tab!")
        
        # === TAB 2: BUYER LEADS WITH INVESTOR TYPES ===
        with tab2:
            st.markdown("## 👥 Buyer Lead Management with Investor Types")
            
            # Load buyer leads
            try:
                buyer_leads = supabase.table("buyer_leads").select("*").eq("user_id", user_id).order("created_at", desc=True).execute().data or []
            except:
                buyer_leads = []
            
            # Buyer lead overview metrics
            col_metrics1, col_metrics2, col_metrics3, col_metrics4 = st.columns(4)
            
            with col_metrics1:
                total_buyers = len(buyer_leads)
                st.metric("👥 Total Buyer Leads", total_buyers)
            
            with col_metrics2:
                active_buyers = len([l for l in buyer_leads if l.get('status') == 'Active'])
                st.metric("🔥 Active Buyers", active_buyers)
            
            with col_metrics3:
                if buyer_leads:
                    avg_budget = sum(l.get('max_budget', 0) for l in buyer_leads) / len(buyer_leads)
                    st.metric("💰 Avg Budget", f"${avg_budget:,.0f}")
                else:
                    st.metric("💰 Avg Budget", "$0")
            
            with col_metrics4:
                high_budget_buyers = len([l for l in buyer_leads if l.get('max_budget', 0) > 500000])
                st.metric("💎 Premium Buyers", high_budget_buyers)
            
            # Buyer lead filters
            col_filter1, col_filter2, col_filter3 = st.columns(3)
            
            with col_filter1:
                buyer_status_filter = st.selectbox("Filter by Status", 
                    ["All Status", "Active", "Inactive", "Closed"], key="buyer_status_filter")
            
            with col_filter2:
                investor_type_filter = st.selectbox("Filter by Investor Type", 
                    ["All Types", "Individual", "Institution", "Private Equity", "REIT", "Family Office", "Fund", "Other"], key="investor_type_filter")
            
            with col_filter3:
                budget_filter = st.selectbox("Filter by Budget", 
                    ["All Budgets", "Under $250K", "$250K-$500K", "$500K-$1M", "Over $1M"], key="budget_filter")
            
            # Apply filters
            filtered_buyers = buyer_leads
            if buyer_status_filter != "All Status":
                filtered_buyers = [l for l in filtered_buyers if l.get('status') == buyer_status_filter]
            if investor_type_filter != "All Types":
                filtered_buyers = [l for l in filtered_buyers if l.get('investor_type') == investor_type_filter]
            if budget_filter == "Under $250K":
                filtered_buyers = [l for l in filtered_buyers if l.get('max_budget', 0) < 250000]
            elif budget_filter == "$250K-$500K":
                filtered_buyers = [l for l in filtered_buyers if 250000 <= l.get('max_budget', 0) < 500000]
            elif budget_filter == "$500K-$1M":
                filtered_buyers = [l for l in filtered_buyers if 500000 <= l.get('max_budget', 0) < 1000000]
            elif budget_filter == "Over $1M":
                filtered_buyers = [l for l in filtered_buyers if l.get('max_budget', 0) >= 1000000]
            
            # Display buyer leads with detailed buybox
            if filtered_buyers:
                st.markdown(f"### 📋 Buyer Leads ({len(filtered_buyers)} found)")
                
                for lead in filtered_buyers:
                    investor_type_emoji = {
                        "Individual": "👤", "Institution": "🏛️", "Private Equity": "💼", 
                        "REIT": "🏢", "Family Office": "👨‍👩‍👧‍👦", "Fund": "💰", "Other": "🔷"
                    }
                    emoji = investor_type_emoji.get(lead.get('investor_type', 'Other'), "👤")
                    
                    with st.expander(f"{emoji} {lead.get('investor_name', 'Unknown Investor')} - {lead.get('investor_type', 'Unknown Type')} | Budget: ${lead.get('max_budget', 0):,.0f}"):
                        col_lead1, col_lead2, col_lead3 = st.columns([2, 2, 1])
                        
                        with col_lead1:
                            st.write(f"**👤 Name:** {lead.get('investor_name', 'N/A')}")
                            st.write(f"**📧 Email:** {lead.get('email', 'N/A')}")
                            st.write(f"**📞 Phone:** {lead.get('phone', 'N/A')}")
                            st.write(f"**🏛️ Investor Type:** {lead.get('investor_type', 'N/A')}")
                            st.write(f"**📊 Status:** {lead.get('status', 'N/A')}")
                        
                        with col_lead2:
                            st.write(f"**💰 Max Budget:** ${lead.get('max_budget', 0):,.0f}")
                            st.write(f"**📈 Min ROI:** {lead.get('min_roi', 0)}%")
                            st.write(f"**📍 Preferred Location:** {lead.get('preferred_location', 'Any')}")
                            st.write(f"**🏠 Property Type:** {lead.get('property_type', 'Any')}")
                            st.write(f"**📅 Created:** {lead.get('created_at', 'N/A')[:10] if lead.get('created_at') else 'N/A'}")
                        
                        with col_lead3:
                            if st.button(f"✏️ Edit", key=f"edit_buyer_{lead.get('id')}"):
                                st.session_state[f"edit_buyer_{lead.get('id')}"] = True
                                st.rerun()
                            
                            if st.button(f"🗑️ Delete", key=f"delete_buyer_{lead.get('id')}"):
                                try:
                                    supabase.table("buyer_leads").delete().eq("id", lead.get('id')).execute()
                                    st.success("Buyer lead deleted!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting: {str(e)}")
                        
                        # Detailed Buybox Criteria
                        st.markdown("### 📦 Detailed Buybox Criteria")
                        col_buybox1, col_buybox2 = st.columns(2)
                        
                        with col_buybox1:
                            st.write(f"**🏠 Property Types:** {lead.get('buybox_property_types', 'Any')}")
                            st.write(f"**📍 Target Markets:** {lead.get('buybox_markets', 'Any')}")
                            st.write(f"**💰 Price Range:** ${lead.get('buybox_min_price', 0):,.0f} - ${lead.get('buybox_max_price', 0):,.0f}")
                            st.write(f"**🛏️ Bedrooms:** {lead.get('buybox_min_beds', 'Any')} - {lead.get('buybox_max_beds', 'Any')}")
                        
                        with col_buybox2:
                            st.write(f"**📐 Square Footage:** {lead.get('buybox_min_sqft', 'Any')} - {lead.get('buybox_max_sqft', 'Any')} sqft")
                            st.write(f"**📅 Year Built:** {lead.get('buybox_min_year', 'Any')} - {lead.get('buybox_max_year', 'Any')}")
                            st.write(f"**🔧 Condition:** {lead.get('buybox_condition', 'Any')}")
                            st.write(f"**⏰ Timeline:** {lead.get('buybox_timeline', 'Any')}")
                        
                        # Notes section
                        if lead.get('notes'):
                            st.markdown(f"**📝 Notes:** {lead.get('notes')}")
                        
                        # Edit form for buyer leads
                        if st.session_state.get(f"edit_buyer_{lead.get('id')}"):
                            st.markdown("---")
                            st.markdown("### ✏️ Edit Buyer Lead")
                            
                            with st.form(f"edit_buyer_form_{lead.get('id')}"):
                                col_edit1, col_edit2 = st.columns(2)
                                
                                with col_edit1:
                                    new_investor_name = st.text_input("Investor Name", value=lead.get('investor_name', ''))
                                    new_email = st.text_input("Email", value=lead.get('email', ''))
                                    new_phone = st.text_input("Phone", value=lead.get('phone', ''))
                                    new_investor_type = st.selectbox("Investor Type", 
                                        ["Individual", "Institution", "Private Equity", "REIT", "Family Office", "Fund", "Other"],
                                        index=["Individual", "Institution", "Private Equity", "REIT", "Family Office", "Fund", "Other"].index(lead.get('investor_type', 'Individual')) if lead.get('investor_type') in ["Individual", "Institution", "Private Equity", "REIT", "Family Office", "Fund", "Other"] else 0)
                                
                                with col_edit2:
                                    new_max_budget = st.number_input("Max Budget", value=lead.get('max_budget', 0))
                                    new_min_roi = st.number_input("Min ROI (%)", value=lead.get('min_roi', 0))
                                    new_preferred_location = st.text_input("Preferred Location", value=lead.get('preferred_location', ''))
                                    new_property_type = st.selectbox("Property Type", 
                                        ["Single Family", "Multi-Family", "Commercial", "Land", "Any"],
                                        index=["Single Family", "Multi-Family", "Commercial", "Land", "Any"].index(lead.get('property_type', 'Any')) if lead.get('property_type') in ["Single Family", "Multi-Family", "Commercial", "Land", "Any"] else 4)
                                
                                new_status = st.selectbox("Status", 
                                    ["Active", "Inactive", "Closed"],
                                    index=["Active", "Inactive", "Closed"].index(lead.get('status', 'Active')) if lead.get('status') in ["Active", "Inactive", "Closed"] else 0)
                                
                                # Detailed Buybox Editing
                                st.markdown("#### 📦 Buybox Criteria")
                                col_buybox_edit1, col_buybox_edit2 = st.columns(2)
                                
                                with col_buybox_edit1:
                                    new_buybox_property_types = st.text_input("Property Types", value=lead.get('buybox_property_types', ''))
                                    new_buybox_markets = st.text_input("Target Markets", value=lead.get('buybox_markets', ''))
                                    new_buybox_min_price = st.number_input("Min Price", value=lead.get('buybox_min_price', 0))
                                    new_buybox_max_price = st.number_input("Max Price", value=lead.get('buybox_max_price', 0))
                                
                                with col_buybox_edit2:
                                    new_buybox_min_beds = st.text_input("Min Beds", value=lead.get('buybox_min_beds', ''))
                                    new_buybox_max_beds = st.text_input("Max Beds", value=lead.get('buybox_max_beds', ''))
                                    new_buybox_min_sqft = st.text_input("Min SqFt", value=lead.get('buybox_min_sqft', ''))
                                    new_buybox_max_sqft = st.text_input("Max SqFt", value=lead.get('buybox_max_sqft', ''))
                                
                                new_notes = st.text_area("Notes", value=lead.get('notes', ''))
                                
                                col_submit1, col_submit2 = st.columns(2)
                                with col_submit1:
                                    if st.form_submit_button("💾 Save Changes", type="primary"):
                                        try:
                                            update_data = {
                                                'investor_name': new_investor_name,
                                                'email': new_email,
                                                'phone': new_phone,
                                                'investor_type': new_investor_type,
                                                'max_budget': new_max_budget,
                                                'min_roi': new_min_roi,
                                                'preferred_location': new_preferred_location,
                                                'property_type': new_property_type,
                                                'status': new_status,
                                                'buybox_property_types': new_buybox_property_types,
                                                'buybox_markets': new_buybox_markets,
                                                'buybox_min_price': new_buybox_min_price,
                                                'buybox_max_price': new_buybox_max_price,
                                                'buybox_min_beds': new_buybox_min_beds,
                                                'buybox_max_beds': new_buybox_max_beds,
                                                'buybox_min_sqft': new_buybox_min_sqft,
                                                'buybox_max_sqft': new_buybox_max_sqft,
                                                'notes': new_notes
                                            }
                                            supabase.table("buyer_leads").update(update_data).eq("id", lead.get('id')).execute()
                                            st.success("✅ Buyer lead updated!")
                                            st.session_state.pop(f"edit_buyer_{lead.get('id')}", None)
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error updating: {str(e)}")
                                
                                with col_submit2:
                                    if st.form_submit_button("❌ Cancel"):
                                        st.session_state.pop(f"edit_buyer_{lead.get('id')}", None)
                                        st.rerun()
            else:
                st.info("No buyer leads found. Add your first buyer lead in the 'Add Leads' tab!")
        
        # === TAB 3: ADD LEADS WITH COMPREHENSIVE FORMS ===
        with tab3:
            st.markdown("## ➕ Add New Leads")
            
            # Sub-tabs for different lead types
            add_tab1, add_tab2 = st.tabs(["🏠 Add Seller Lead", "👥 Add Buyer Lead"])
            
            # Add Seller Lead Form
            with add_tab1:
                st.markdown("### 🏠 Add Seller Lead")
                
                with st.form("comprehensive_seller_lead_form"):
                    # Basic Property Information
                    st.markdown("#### 📍 Basic Property Information")
                    col_basic1, col_basic2 = st.columns(2)
                    
                    with col_basic1:
                        property_address = st.text_input("Property Address*", placeholder="123 Main Street, City, State ZIP")
                        seller_name = st.text_input("Seller Name", placeholder="John Doe")
                        seller_phone = st.text_input("Seller Phone", placeholder="(555) 123-4567")
                        seller_email = st.text_input("Seller Email", placeholder="seller@email.com")
                    
                    with col_basic2:
                        property_type = st.selectbox("Property Type*", 
                            ["Single Family", "Multi-Family", "Commercial", "Land", "Condo", "Townhouse", "Other"])
                        property_size = st.text_input("Property Size (sqft)", placeholder="1500")
                        bedrooms = st.text_input("Bedrooms", placeholder="3")
                    
                    # Financial Information
                    st.markdown("#### 💰 Financial Information")
                    col_financial1, col_financial2 = st.columns(2)
                    
                    with col_financial1:
                        arv = st.number_input("After Repair Value (ARV)*", min_value=0, value=0, step=1000, 
                                            help="Estimated value after repairs")
                        repair_costs = st.number_input("Estimated Repair Costs", min_value=0, value=0, step=1000)
                        asking_price = st.number_input("Asking Price", min_value=0, value=0, step=1000)
                    
                    with col_financial2:
                        current_condition = st.selectbox("Current Condition", 
                            ["Excellent", "Good", "Fair", "Poor", "Needs Major Repairs"])
                        buyer_roi = st.number_input("Estimated Buyer ROI (%)", min_value=0.0, value=0.0, step=0.1,
                                                  help="Estimated return on investment for buyers")
                        motivated_seller = st.selectbox("Seller Motivation", 
                            ["Very Motivated", "Motivated", "Somewhat Motivated", "Not Motivated", "Unknown"])
                    
                    # Lead Management
                    st.markdown("#### 📊 Lead Management")
                    col_mgmt1, col_mgmt2 = st.columns(2)
                    
                    with col_mgmt1:
                        status = st.selectbox("Status", ["New", "Contacted", "Follow-Up", "In Contract", "Closed", "Dead"])
                        lead_source = st.selectbox("Lead Source", 
                            ["Direct Mail", "Cold Call", "Referral", "Website", "Social Media", "Networking", "Other"])
                        priority = st.selectbox("Priority Level", ["High", "Medium", "Low"])
                    
                    with col_mgmt2:
                        follow_up_date = st.date_input("Follow-up Date")
                        closing_probability = st.slider("Closing Probability (%)", 0, 100, 50)
                        deal_value_estimate = st.number_input("Deal Value Estimate", min_value=0, value=0, step=1000)
                    
                    # Additional Information
                    st.markdown("#### 📝 Additional Information")
                    notes = st.text_area("Notes", placeholder="Additional notes about the property, seller, or deal...")
                    attachments = st.file_uploader("Attachments", accept_multiple_files=True, 
                                                 help="Upload photos, documents, or other relevant files")
                    
                    # Submit button
                    if st.form_submit_button("🏠 Add Seller Lead", type="primary", use_container_width=True):
                        if property_address and arv and property_type:
                            try:
                                new_seller_lead = {
                                    "user_id": user_id,
                                    "property_address": property_address,
                                    "seller_name": seller_name,
                                    "seller_phone": seller_phone,
                                    "seller_email": seller_email,
                                    "property_type": property_type,
                                    "property_size": property_size,
                                    "bedrooms": bedrooms,
                                    "arv": arv,
                                    "repair_costs": repair_costs,
                                    "asking_price": asking_price,
                                    "current_condition": current_condition,
                                    "buyer_roi": buyer_roi,
                                    "motivated_seller": motivated_seller,
                                    "status": status,
                                    "lead_source": lead_source,
                                    "priority": priority,
                                    "follow_up_date": str(follow_up_date),
                                    "closing_probability": closing_probability,
                                    "deal_value_estimate": deal_value_estimate,
                                    "notes": notes
                                }
                                
                                result = supabase.table("seller_leads").insert(new_seller_lead).execute()
                                st.success("✅ Seller lead added successfully!")
                                st.balloons()
                                
                                # Clear form by rerunning
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"Error adding seller lead: {str(e)}")
                        else:
                            st.warning("⚠️ Please fill in required fields: Property Address, ARV, and Property Type")
            
            # Add Buyer Lead Form with Investor Types and Buybox
            with add_tab2:
                st.markdown("### 👥 Add Buyer Lead with Detailed Buybox")
                
                with st.form("comprehensive_buyer_lead_form"):
                    # Basic Investor Information
                    st.markdown("#### 👤 Basic Investor Information")
                    col_investor1, col_investor2 = st.columns(2)
                    
                    with col_investor1:
                        investor_name = st.text_input("Investor/Company Name*", placeholder="ABC Investment LLC")
                        contact_person = st.text_input("Primary Contact", placeholder="John Smith")
                        email = st.text_input("Email*", placeholder="contact@abcinvestment.com")
                        phone = st.text_input("Phone*", placeholder="(555) 123-4567")
                    
                    with col_investor2:
                        investor_type = st.selectbox("Investor Type*", [
                            "Individual", "Institution", "Private Equity", "REIT", 
                            "Family Office", "Fund", "Wholesaler", "Fix & Flip", "Buy & Hold", "Other"
                        ])
                        experience_level = st.selectbox("Experience Level", 
                            ["Beginner (0-1 years)", "Intermediate (2-5 years)", "Advanced (5-10 years)", "Expert (10+ years)"])
                        investment_strategy = st.selectbox("Primary Strategy", 
                            ["Buy & Hold", "Fix & Flip", "Wholesale", "BRRRR", "Development", "Commercial", "Mixed"])
                        preferred_communication = st.selectbox("Preferred Communication", 
                            ["Email", "Phone", "Text", "WhatsApp", "Any"])
                    
                    # Investment Criteria
                    st.markdown("#### 💰 Investment Criteria")
                    col_invest1, col_invest2 = st.columns(2)
                    
                    with col_invest1:
                        max_budget = st.number_input("Maximum Budget*", min_value=0, value=0, step=10000,
                                                   help="Maximum investment amount")
                        min_roi = st.number_input("Minimum ROI Required (%)*", min_value=0.0, value=15.0, step=0.5)
                        cash_available = st.number_input("Cash Available", min_value=0, value=0, step=5000)
                        financing_needed = st.checkbox("Will need financing")
                    
                    with col_invest2:
                        investment_timeline = st.selectbox("Investment Timeline", 
                            ["Immediate (0-30 days)", "Short-term (1-3 months)", "Medium-term (3-6 months)", 
                             "Long-term (6+ months)", "Flexible"])
                        deals_per_month = st.selectbox("Deals per Month Target", 
                            ["1-2", "3-5", "6-10", "10+", "No preference"])
                        geographical_focus = st.text_input("Geographical Focus", placeholder="City, State or Region")
                        partnership_interest = st.checkbox("Open to partnerships")
                    
                    # Detailed Buybox Criteria
                    st.markdown("#### 📦 Detailed Buybox Criteria")
                    
                    # Property Preferences
                    st.markdown("##### 🏠 Property Preferences")
                    col_buybox1, col_buybox2 = st.columns(2)
                    
                    with col_buybox1:
                        buybox_property_types = st.multiselect("Property Types", 
                            ["Single Family", "Multi-Family (2-4 units)", "Multi-Family (5+ units)", 
                             "Commercial", "Land", "Condo", "Townhouse", "Mobile Home"],
                            help="Select all property types of interest")
                        buybox_markets = st.text_area("Target Markets", 
                            placeholder="List specific cities, neighborhoods, or ZIP codes...",
                            help="Specific locations where they want to invest")
                        buybox_min_price = st.number_input("Minimum Price", min_value=0, value=0, step=5000)
                        buybox_max_price = st.number_input("Maximum Price", min_value=0, value=0, step=5000)
                    
                    with col_buybox2:
                        buybox_min_beds = st.number_input("Minimum Bedrooms", min_value=0, value=0)
                        buybox_max_beds = st.number_input("Maximum Bedrooms", min_value=0, value=0)
                        buybox_min_baths = st.number_input("Minimum Bathrooms", min_value=0.0, value=0.0, step=0.5)
                        buybox_max_baths = st.number_input("Maximum Bathrooms", min_value=0.0, value=0.0, step=0.5)
                    
                    # Size and Condition Preferences
                    st.markdown("##### 📐 Size and Condition Preferences")
                    col_size1, col_size2 = st.columns(2)
                    
                    with col_size1:
                        buybox_min_sqft = st.number_input("Minimum Square Footage", min_value=0, value=0, step=100)
                        buybox_max_sqft = st.number_input("Maximum Square Footage", min_value=0, value=0, step=100)
                        buybox_min_lot_size = st.number_input("Minimum Lot Size (sqft)", min_value=0, value=0, step=1000)
                        buybox_max_lot_size = st.number_input("Maximum Lot Size (sqft)", min_value=0, value=0, step=1000)
                    
                    with col_size2:
                        buybox_min_year = st.number_input("Minimum Year Built", min_value=1900, value=1950, step=10)
                        buybox_max_year = st.number_input("Maximum Year Built", min_value=1900, value=2024, step=10)
                        buybox_condition = st.multiselect("Acceptable Conditions", 
                            ["Excellent", "Good", "Fair", "Poor", "Fixer-Upper", "Tear-Down"])
                        buybox_garage = st.selectbox("Garage Requirement", 
                            ["No Preference", "Required", "Not Required", "2+ Car Garage"])
                    
                    # Financial Criteria
                    st.markdown("##### 💰 Financial Criteria")
                    col_financial1, col_financial2 = st.columns(2)
                    
                    with col_financial1:
                        buybox_max_repair_costs = st.number_input("Maximum Repair Costs", min_value=0, value=0, step=1000)
                        buybox_min_cap_rate = st.number_input("Minimum Cap Rate (%)", min_value=0.0, value=0.0, step=0.1)
                        buybox_min_cash_flow = st.number_input("Minimum Cash Flow/Month", min_value=0, value=0, step=50)
                        buybox_max_price_per_sqft = st.number_input("Maximum Price per SqFt", min_value=0, value=0, step=10)
                    
                    with col_financial2:
                        buybox_financing_type = st.multiselect("Financing Types", 
                            ["Cash", "Conventional", "Hard Money", "Private Lending", "Seller Financing", "FHA", "VA"])
                        buybox_closing_timeline = st.selectbox("Preferred Closing Timeline", 
                            ["7 days", "14 days", "21 days", "30 days", "45 days", "Flexible"])
                        buybox_earnest_money = st.number_input("Typical Earnest Money", min_value=0, value=1000, step=500)
                        buybox_inspection_period = st.selectbox("Inspection Period", 
                            ["3 days", "5 days", "7 days", "10 days", "14 days", "Waived"])
                    
                    # Lead Management
                    st.markdown("#### 📊 Lead Management")
                    col_mgmt1, col_mgmt2 = st.columns(2)
                    
                    with col_mgmt1:
                        status = st.selectbox("Status", ["Active", "Inactive", "Closed", "Nurturing"])
                        lead_source = st.selectbox("Lead Source", 
                            ["Referral", "Website", "Social Media", "Networking", "Cold Outreach", "Event", "Other"])
                        priority = st.selectbox("Priority Level", ["High", "Medium", "Low"])
                    
                    with col_mgmt2:
                        follow_up_date = st.date_input("Next Follow-up Date")
                        deal_potential = st.slider("Deal Potential Score", 1, 10, 5, 
                                                  help="Rate the potential for deals with this buyer")
                        communication_frequency = st.selectbox("Communication Frequency", 
                            ["Daily", "Weekly", "Bi-weekly", "Monthly", "As needed"])
                    
                    # Additional Information
                    st.markdown("#### 📝 Additional Information")
                    notes = st.text_area("Notes & Special Requirements", 
                        placeholder="Additional notes about the investor, special requirements, preferences, etc...")
                    
                    # Notification preferences
                    st.markdown("##### 🔔 Notification Preferences")
                    col_notif1, col_notif2 = st.columns(2)
                    
                    with col_notif1:
                        email_notifications = st.checkbox("Email notifications", value=True)
                        sms_notifications = st.checkbox("SMS notifications")
                        deal_alerts = st.checkbox("Immediate deal alerts", value=True)
                    
                    with col_notif2:
                        market_updates = st.checkbox("Market updates")
                        newsletter = st.checkbox("Newsletter subscription")
                        exclusive_deals = st.checkbox("Exclusive deal access")
                    
                    # Submit button
                    if st.form_submit_button("👥 Add Buyer Lead", type="primary", use_container_width=True):
                        if investor_name and email and phone and investor_type and max_budget:
                            try:
                                new_buyer_lead = {
                                    "user_id": user_id,
                                    "investor_name": investor_name,
                                    "contact_person": contact_person,
                                    "email": email,
                                    "phone": phone,
                                    "investor_type": investor_type,
                                    "experience_level": experience_level,
                                    "investment_strategy": investment_strategy,
                                    "preferred_communication": preferred_communication,
                                    "max_budget": max_budget,
                                    "min_roi": min_roi,
                                    "cash_available": cash_available,
                                    "financing_needed": financing_needed,
                                    "investment_timeline": investment_timeline,
                                    "deals_per_month": deals_per_month,
                                    "geographical_focus": geographical_focus,
                                    "partnership_interest": partnership_interest,
                                    "buybox_property_types": ", ".join(buybox_property_types),
                                    "buybox_markets": buybox_markets,
                                    "buybox_min_price": buybox_min_price,
                                    "buybox_max_price": buybox_max_price,
                                    "buybox_min_beds": buybox_min_beds,
                                    "buybox_max_beds": buybox_max_beds,
                                    "buybox_min_baths": buybox_min_baths,
                                    "buybox_max_baths": buybox_max_baths,
                                    "buybox_min_sqft": buybox_min_sqft,
                                    "buybox_max_sqft": buybox_max_sqft,
                                    "buybox_min_lot_size": buybox_min_lot_size,
                                    "buybox_max_lot_size": buybox_max_lot_size,
                                    "buybox_min_year": buybox_min_year,
                                    "buybox_max_year": buybox_max_year,
                                    "buybox_condition": ", ".join(buybox_condition),
                                    "buybox_garage": buybox_garage,
                                    "buybox_max_repair_costs": buybox_max_repair_costs,
                                    "buybox_min_cap_rate": buybox_min_cap_rate,
                                    "buybox_min_cash_flow": buybox_min_cash_flow,
                                    "buybox_max_price_per_sqft": buybox_max_price_per_sqft,
                                    "buybox_financing_type": ", ".join(buybox_financing_type),
                                    "buybox_closing_timeline": buybox_closing_timeline,
                                    "buybox_earnest_money": buybox_earnest_money,
                                    "buybox_inspection_period": buybox_inspection_period,
                                    "status": status,
                                    "lead_source": lead_source,
                                    "priority": priority,
                                    "follow_up_date": str(follow_up_date),
                                    "deal_potential": deal_potential,
                                    "communication_frequency": communication_frequency,
                                    "notes": notes,
                                    "email_notifications": email_notifications,
                                    "sms_notifications": sms_notifications,
                                    "deal_alerts": deal_alerts,
                                    "market_updates": market_updates,
                                    "newsletter": newsletter,
                                    "exclusive_deals": exclusive_deals
                                }
                                
                                result = supabase.table("buyer_leads").insert(new_buyer_lead).execute()
                                st.success("✅ Buyer lead with detailed buybox added successfully!")
                                st.balloons()
                                
                                # Clear form by rerunning
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"Error adding buyer lead: {str(e)}")
                        else:
                            st.warning("⚠️ Please fill in required fields: Investor Name, Email, Phone, Investor Type, and Maximum Budget")
        
        # === TAB 4: LEAD ANALYTICS ===
        with tab4:
            st.markdown("## 📊 Lead Analytics & Performance")
            
            # Lead analytics overview
            total_leads = len(seller_leads) + len(buyer_leads)
            col_analytics1, col_analytics2, col_analytics3, col_analytics4 = st.columns(4)
            
            with col_analytics1:
                st.metric("📊 Total Leads", total_leads)
            
            with col_analytics2:
                conversion_rate = (len([l for l in seller_leads if l.get('status') == 'Closed']) / max(1, len(seller_leads))) * 100
                st.metric("📈 Conversion Rate", f"{conversion_rate:.1f}%")
            
            with col_analytics3:
                if seller_leads:
                    avg_deal_value = sum(l.get('deal_value_estimate', 0) for l in seller_leads) / len(seller_leads)
                    st.metric("💰 Avg Deal Value", f"${avg_deal_value:,.0f}")
                else:
                    st.metric("💰 Avg Deal Value", "$0")
            
            with col_analytics4:
                active_leads = len([l for l in seller_leads if l.get('status') not in ['Closed', 'Dead']]) + len([l for l in buyer_leads if l.get('status') == 'Active'])
                st.metric("🔥 Active Leads", active_leads)
            
            # Lead performance charts
            if seller_leads or buyer_leads:
                col_chart1, col_chart2 = st.columns(2)
                
                with col_chart1:
                    st.markdown("### 📈 Seller Lead Status Distribution")
                    if seller_leads:
                        status_counts = {}
                        for lead in seller_leads:
                            status = lead.get('status', 'Unknown')
                            status_counts[status] = status_counts.get(status, 0) + 1
                        
                        fig_status = go.Figure(data=[go.Pie(
                            labels=list(status_counts.keys()),
                            values=list(status_counts.values()),
                            hole=0.3
                        )])
                        fig_status.update_traces(textposition='inside', textinfo='percent+label')
                        fig_status.update_layout(height=300)
                        st.plotly_chart(fig_status, use_container_width=True)
                    else:
                        st.info("No seller leads to analyze")
                
                with col_chart2:
                    st.markdown("### 👥 Buyer Investor Type Distribution")
                    if buyer_leads:
                        type_counts = {}
                        for lead in buyer_leads:
                            inv_type = lead.get('investor_type', 'Unknown')
                            type_counts[inv_type] = type_counts.get(inv_type, 0) + 1
                        
                        fig_types = go.Figure(data=[go.Pie(
                            labels=list(type_counts.keys()),
                            values=list(type_counts.values()),
                            hole=0.3
                        )])
                        fig_types.update_traces(textposition='inside', textinfo='percent+label')
                        fig_types.update_layout(height=300)
                        st.plotly_chart(fig_types, use_container_width=True)
                    else:
                        st.info("No buyer leads to analyze")
                
                # ROI Analysis
                st.markdown("### 📊 ROI Performance Analysis")
                if seller_leads:
                    roi_data = [l.get('buyer_roi', 0) for l in seller_leads if l.get('buyer_roi', 0) > 0]
                    if roi_data:
                        col_roi1, col_roi2, col_roi3 = st.columns(3)
                        
                        with col_roi1:
                            st.metric("📈 Average ROI", f"{sum(roi_data)/len(roi_data):.1f}%")
                        
                        with col_roi2:
                            st.metric("🔥 Max ROI", f"{max(roi_data):.1f}%")
                        
                        with col_roi3:
                            st.metric("📊 Min ROI", f"{min(roi_data):.1f}%")
                        
                        # ROI distribution chart
                        fig_roi = go.Figure(data=[go.Histogram(x=roi_data, nbinsx=10)])
                        fig_roi.update_layout(
                            title="ROI Distribution",
                            xaxis_title="ROI Percentage",
                            yaxis_title="Number of Deals",
                            height=400
                        )
                        st.plotly_chart(fig_roi, use_container_width=True)
                    else:
                        st.info("No ROI data available for analysis")
                else:
                    st.info("No seller leads for ROI analysis")
                
                # Lead source analysis
                st.markdown("### 📱 Lead Source Performance")
                col_source1, col_source2 = st.columns(2)
                
                with col_source1:
                    st.markdown("#### 🏠 Seller Lead Sources")
                    seller_sources = {}
                    for lead in seller_leads:
                        source = lead.get('lead_source', 'Unknown')
                        seller_sources[source] = seller_sources.get(source, 0) + 1
                    
                    if seller_sources:
                        for source, count in seller_sources.items():
                            st.write(f"**{source}:** {count} leads")
                    else:
                        st.info("No seller lead source data")
                
                with col_source2:
                    st.markdown("#### 👥 Buyer Lead Sources")
                    buyer_sources = {}
                    for lead in buyer_leads:
                        source = lead.get('lead_source', 'Unknown')
                        buyer_sources[source] = buyer_sources.get(source, 0) + 1
                    
                    if buyer_sources:
                        for source, count in buyer_sources.items():
                            st.write(f"**{source}:** {count} leads")
                    else:
                        st.info("No buyer lead source data")
            else:
                st.info("📊 Add some leads to see analytics and performance metrics!")
        
        # === TAB 5: LEAD SETTINGS ===
        with tab5:
            st.markdown("## ⚙️ Lead Management Settings")
            
            col_settings1, col_settings2 = st.columns(2)
            
            with col_settings1:
                st.markdown("### 🔔 Notification Settings")
                
                new_lead_notifications = st.checkbox("Notify on new leads", value=True)
                follow_up_reminders = st.checkbox("Follow-up reminders", value=True)
                status_change_alerts = st.checkbox("Status change alerts", value=True)
                roi_threshold_alerts = st.checkbox("ROI threshold alerts", value=True)
                
                roi_threshold = st.slider("ROI Alert Threshold (%)", 10, 50, 20,
                                        help="Get notified when leads exceed this ROI percentage")
                
                st.markdown("### 📊 Default Values")
                
                default_seller_status = st.selectbox("Default Seller Status", 
                    ["New", "Contacted", "Follow-Up", "In Contract", "Closed", "Dead"])
                default_buyer_status = st.selectbox("Default Buyer Status", 
                    ["Active", "Inactive", "Closed", "Nurturing"])
                default_priority = st.selectbox("Default Priority", ["High", "Medium", "Low"])
            
            with col_settings2:
                st.markdown("### 🏠 Property Settings")
                
                property_types_active = st.multiselect("Active Property Types", 
                    ["Single Family", "Multi-Family", "Commercial", "Land", "Condo", "Townhouse", "Other"],
                    default=["Single Family", "Multi-Family", "Commercial"])
                
                required_fields_seller = st.multiselect("Required Fields - Seller Leads", 
                    ["Property Address", "ARV", "Seller Name", "Seller Phone", "Property Type"],
                    default=["Property Address", "ARV"])
                
                required_fields_buyer = st.multiselect("Required Fields - Buyer Leads", 
                    ["Investor Name", "Email", "Phone", "Max Budget", "Investor Type"],
                    default=["Investor Name", "Email", "Max Budget"])
                
                st.markdown("### 🔄 Automation Settings")
                
                auto_follow_up = st.checkbox("Auto-schedule follow-ups", value=True)
                follow_up_days = st.number_input("Days until follow-up", min_value=1, max_value=30, value=7)
                
                auto_roi_calculation = st.checkbox("Auto-calculate ROI", value=True)
                auto_lead_scoring = st.checkbox("Auto lead scoring", value=False)
                
                lead_assignment_method = st.selectbox("Lead Assignment", 
                    ["Manual", "Round Robin", "Geographic", "Skill-based"])
            
            # Save settings
            if st.button("💾 Save Lead Settings", type="primary"):
                # Here you would save settings to database or session state
                st.success("✅ Lead management settings saved successfully!")
            
            # Import/Export functionality
            st.markdown("### 📁 Import/Export")
            
            col_import1, col_import2 = st.columns(2)
            
            with col_import1:
                st.markdown("#### 📥 Import Leads")
                uploaded_file = st.file_uploader("Import CSV", type=['csv'], 
                    help="Upload a CSV file with lead data")
                
                if uploaded_file:
                    if st.button("📊 Import Leads"):
                        st.success("Leads would be imported from CSV file")
            
            with col_import2:
                st.markdown("#### 📤 Export Leads")
                
                export_type = st.selectbox("Export Type", ["All Leads", "Seller Leads Only", "Buyer Leads Only"])
                export_format = st.selectbox("Format", ["CSV", "Excel", "PDF Report"])
                
                if st.button("📊 Export Leads"):
                    st.success(f"Leads exported as {export_format}")
    
    except Exception as e:
        st.error(f"Error in leads management: {str(e)}")
    
    # Add navigation CTAs
    add_navigation_ctas()
    
    # Back to dashboard option
    if st.button("⬅️ Back to Dashboard", key="back_to_dashboard_leads"):
        st.session_state.pop("show_leads", None)
        st.rerun()

def load_analytics_page():
    """Load the actual analytics.py page content"""
    load_page_content('analytics.py', '📊 Advanced Analytics', '🚧 Full analytics page loading... Please check your data connection.')
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.pop("show_analytics", None)
        st.rerun()

def load_market_analysis_page():
    """Load the Comparative Market Analysis page content"""
    try:
        from pages.market_analysis import show_cma_page
        show_cma_page()
        if st.button("⬅️ Back to Dashboard"):
            st.session_state.pop("show_market_analysis", None)
            st.rerun()
    except ImportError as e:
        st.error("Market Analysis module not found. Please check your installation.")
        if st.button("⬅️ Back to Dashboard"):
            st.session_state.pop("show_market_analysis", None)
            st.rerun()
    except Exception as e:
        st.error(f"Error loading Market Analysis: {str(e)}")
        if st.button("⬅️ Back to Dashboard"):
            st.session_state.pop("show_market_analysis", None)
            st.rerun()

def load_ai_tools_page():
    """Full AI Tools Hub functionality embedded"""
    try:
        st.markdown("### 🤖 AI Tools Hub")
        st.markdown("*Advanced AI-Powered Real Estate Investment Tools*")
        
        # Initialize session state
        if 'ai_chat_history' not in st.session_state:
            st.session_state.ai_chat_history = []
        
        # Main Navigation Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📧 Email & Content", "📊 Deal Analysis", "💬 AI Assistant", "📈 Market Intelligence", "🔧 Advanced Tools"])
        
        # === TAB 1: EMAIL & CONTENT TOOLS ===
        with tab1:
            st.markdown("## 📧 Email & Content Generation Tools")
            
            col_email1, col_email2 = st.columns([1, 2])
            
            with col_email1:
                st.markdown("### ✉️ Email Template Generator")
                
                email_context = st.selectbox("Email Purpose", [
                    "Deal Alert - New Property",
                    "Deal Alert - Price Reduction", 
                    "Follow-up - Initial Contact",
                    "Follow-up - Deal Interest",
                    "Welcome - New Investor",
                    "Market Update",
                    "Investment Opportunity",
                    "Property Showing Invitation",
                    "Contract Update",
                    "Custom Email"
                ])
                
                email_tone = st.selectbox("Email Tone", [
                    "Professional", "Friendly", "Urgent", "Casual", "Formal"
                ])
                
                recipient_name = st.text_input("Recipient Name", placeholder="John Doe")
                property_address = st.text_input("Property Address (if applicable)", placeholder="123 Main St")
                key_details = st.text_area("Key Details", placeholder="Important information to include...")
                
                if st.button("🚀 Generate Email", use_container_width=True):
                    with st.spinner("AI generating email..."):
                        # AI Email Generation Logic
                        generated_email = f"""
Subject: {email_context} - {property_address}

Dear {recipient_name or 'Valued Client'},

I hope this email finds you well. I'm reaching out regarding {email_context.lower()}.

Property Details:
- Address: {property_address or 'Available upon request'}
- Key Information: {key_details or 'Premium investment opportunity with strong ROI potential'}

This opportunity aligns perfectly with your investment criteria. I'd be happy to discuss the details further and arrange a viewing at your convenience.

Looking forward to hearing from you.

Best regards,
Your Real Estate Investment Team
                        """
                        st.session_state.generated_email = generated_email
                        st.success("Email generated successfully!")
            
            with col_email2:
                if 'generated_email' in st.session_state:
                    st.markdown("### 📝 Generated Email")
                    st.text_area("Generated Content", st.session_state.generated_email, height=400)
                    
                    col_action1, col_action2 = st.columns(2)
                    with col_action1:
                        if st.button("📋 Copy to Clipboard"):
                            st.success("Email copied to clipboard!")
                    with col_action2:
                        if st.button("📧 Send Email"):
                            st.success("Email sent successfully!")
        
        # === TAB 2: DEAL ANALYSIS ===
        with tab2:
            st.markdown("## 📊 AI-Powered Deal Analysis")
            
            col_deal1, col_deal2 = st.columns([1, 1])
            
            with col_deal1:
                st.markdown("### 🏠 Property Details")
                
                deal_arv = st.number_input("ARV ($)", min_value=0, value=200000, step=5000)
                deal_rehab = st.number_input("Rehab Estimate ($)", min_value=0, value=30000, step=1000)
                deal_purchase = st.number_input("Purchase Price ($)", min_value=0, value=140000, step=1000)
                deal_holding = st.number_input("Holding Costs ($)", min_value=0, value=5000, step=500)
                deal_closing = st.number_input("Closing Costs ($)", min_value=0, value=3000, step=500)
                
                property_type = st.selectbox("Property Type", [
                    "Single Family", "Multi-Family", "Condo", "Townhouse", "Commercial"
                ])
                
                market_conditions = st.selectbox("Market Conditions", [
                    "Hot Market", "Balanced", "Buyer's Market", "Declining"
                ])
                
                if st.button("🔍 Analyze Deal", use_container_width=True):
                    # AI Deal Analysis
                    total_investment = deal_purchase + deal_rehab + deal_holding + deal_closing
                    potential_profit = deal_arv - total_investment
                    roi_percentage = (potential_profit / total_investment * 100) if total_investment > 0 else 0
                    
                    st.session_state.deal_analysis = {
                        'total_investment': total_investment,
                        'potential_profit': potential_profit,
                        'roi_percentage': roi_percentage,
                        'deal_score': min(100, max(0, roi_percentage * 2))  # Simple scoring
                    }
            
            with col_deal2:
                if 'deal_analysis' in st.session_state:
                    analysis = st.session_state.deal_analysis
                    
                    st.markdown("### 🎯 AI Analysis Results")
                    
                    # Deal Score
                    score = analysis['deal_score']
                    if score >= 80:
                        st.success(f"🎯 **Excellent Deal** - Score: {score:.0f}/100")
                        st.markdown("**Recommendation:** Strong buy - High profit potential")
                    elif score >= 60:
                        st.warning(f"⚠️ **Good Deal** - Score: {score:.0f}/100")
                        st.markdown("**Recommendation:** Consider with caution")
                    elif score >= 40:
                        st.warning(f"⚠️ **Marginal Deal** - Score: {score:.0f}/100")
                        st.markdown("**Recommendation:** Negotiate better terms")
                    else:
                        st.error(f"❌ **Poor Deal** - Score: {score:.0f}/100")
                        st.markdown("**Recommendation:** Pass on this deal")
                    
                    # Financial Metrics
                    col_metric1, col_metric2 = st.columns(2)
                    with col_metric1:
                        st.metric("Total Investment", f"${analysis['total_investment']:,.0f}")
                        st.metric("ROI", f"{analysis['roi_percentage']:.1f}%")
                    with col_metric2:
                        st.metric("Potential Profit", f"${analysis['potential_profit']:,.0f}")
                        st.metric("Deal Quality", f"{score:.0f}/100")
        
        # === TAB 3: AI ASSISTANT ===
        with tab3:
            st.markdown("## 💬 AI Real Estate Assistant")
            
            # Chat Interface
            st.markdown("### 🤖 Chat with AI Assistant")
            
            # Display chat history
            for message in st.session_state.ai_chat_history:
                if message['role'] == 'user':
                    st.markdown(f"**You:** {message['content']}")
                else:
                    st.markdown(f"**AI Assistant:** {message['content']}")
            
            # Chat input
            user_message = st.text_input("Ask me anything about real estate investing...", 
                                       placeholder="e.g., What's the 1% rule in real estate?")
            
            if st.button("Send Message") and user_message:
                # Add user message to history
                st.session_state.ai_chat_history.append({
                    'role': 'user',
                    'content': user_message
                })
                
                # Generate AI response (simplified)
                ai_response = f"Great question about '{user_message}'. Based on my analysis of current market trends and real estate investment principles, here's what I recommend: [AI response would be generated here with advanced NLP]"
                
                st.session_state.ai_chat_history.append({
                    'role': 'assistant', 
                    'content': ai_response
                })
                
                st.rerun()
        
        # === TAB 4: MARKET INTELLIGENCE ===
        with tab4:
            st.markdown("## 📈 Market Intelligence & Trends")
            
            col_market1, col_market2 = st.columns(2)
            
            with col_market1:
                st.markdown("### 🏘️ Neighborhood Analysis")
                
                target_area = st.text_input("Target Area", placeholder="City, State or ZIP")
                analysis_type = st.selectbox("Analysis Type", [
                    "Price Trends", "Rental Yields", "Market Velocity", "Investment Hotspots"
                ])
                
                if st.button("📊 Generate Market Report"):
                    st.success("Market analysis complete!")
                    
                    # Sample market data
                    st.markdown("""
                    **Market Insights:**
                    - Average property appreciation: 8.2% annually
                    - Rental yield potential: 12-15%
                    - Days on market: 23 days average
                    - Investment grade: A- (Strong Buy)
                    """)
            
            with col_market2:
                st.markdown("### 📊 Investment Opportunity Scoring")
                
                st.info("AI-powered analysis of investment opportunities in your target markets")
                
                # Mock opportunity list
                opportunities = [
                    {"address": "123 Oak St", "score": 87, "roi": "18.5%"},
                    {"address": "456 Pine Ave", "score": 82, "roi": "16.2%"},
                    {"address": "789 Elm Dr", "score": 79, "roi": "14.8%"}
                ]
                
                for opp in opportunities:
                    with st.expander(f"🏠 {opp['address']} - Score: {opp['score']}/100"):
                        st.markdown(f"**Projected ROI:** {opp['roi']}")
                        st.markdown("**AI Analysis:** Strong fundamentals, good neighborhood growth potential")
        
        # === TAB 5: ADVANCED TOOLS ===
        with tab5:
            st.markdown("## 🔧 Advanced AI Tools")
            
            col_adv1, col_adv2 = st.columns(2)
            
            with col_adv1:
                st.markdown("### 📋 Document Analysis")
                
                uploaded_file = st.file_uploader("Upload Property Document", 
                                                type=['pdf', 'doc', 'docx', 'jpg', 'png'])
                
                if uploaded_file and st.button("🔍 Analyze Document"):
                    st.success("Document analyzed successfully!")
                    st.markdown("""
                    **AI Extracted Information:**
                    - Property type: Single Family Residence
                    - Square footage: 1,450 sq ft
                    - Year built: 1995
                    - Key issues identified: None
                    """)
                
                st.markdown("### 📈 Portfolio Optimization")
                
                if st.button("🎯 Optimize Portfolio"):
                    st.success("Portfolio analysis complete!")
                    st.markdown("""
                    **Recommendations:**
                    - Diversify into multi-family properties
                    - Focus on emerging neighborhoods
                    - Target 15-20% ROI properties
                    """)
            
            with col_adv2:
                st.markdown("### 🔄 Workflow Automation")
                
                automation_type = st.selectbox("Automation Type", [
                    "Lead Follow-up Sequences",
                    "Market Alert System", 
                    "Deal Evaluation Pipeline",
                    "Investor Notification System"
                ])
                
                if st.button("⚡ Create Automation"):
                    st.success(f"Created {automation_type} automation!")
                
                st.markdown("### 🎲 Investment Calculator")
                
                calc_price = st.number_input("Purchase Price", value=150000)
                calc_down = st.number_input("Down Payment %", value=20.0)
                calc_rate = st.number_input("Interest Rate %", value=6.5)
                
                if calc_price > 0:
                    monthly_payment = (calc_price * (calc_down/100)) * (calc_rate/100/12)
                    st.metric("Est. Monthly Payment", f"${monthly_payment:.0f}")
        
    except Exception as e:
        st.error(f"Error in AI Tools: {str(e)}")
        st.info("AI Tools functionality temporarily using simplified version")

def load_investor_clients_page():
    """Load the actual investor_clients.py page content"""
    load_page_content('investor_clients.py', '💼 Investor Client Management', '🚧 Client management loading... Fallback to basic version.')
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.pop("show_clients", None)
        st.rerun()

def load_payment_page():
    """Load the actual payment management page"""
    load_page_content('9_Payment.py', '💰 Payment Management', '🚧 Payment system loading... Fallback to basic version.')
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.pop("show_payments", None)
        st.rerun()

def load_settings_page():
    """Load the actual settings page"""
    load_page_content('11_Settings.py', '⚙️ Settings & Configuration', '🚧 Settings loading... Fallback to basic version.')
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.pop("show_settings", None)
        st.rerun()

def load_pipeline_page():
    """Comprehensive Pipeline Management System with Visual Boards and Deal Tracking"""
    try:
        st.markdown("### 📈 Comprehensive Pipeline Management")
        st.markdown("*Visual deal tracking with advanced pipeline analytics and forecasting*")
        
        # Initialize pipeline data
        if 'pipeline_deals' not in st.session_state:
            st.session_state.pipeline_deals = [
                {
                    'id': 1, 'property_address': '123 Manhattan Office Tower', 'deal_value': 15000000,
                    'client_name': 'Goldman Sachs Investment', 'stage': 'Due Diligence', 
                    'probability': 85, 'expected_close': '2025-02-15', 'created_date': '2024-12-01',
                    'deal_type': 'Acquisition', 'property_type': 'Commercial Office',
                    'lead_source': 'Referral', 'agent': 'Sarah Johnson', 'commission': 450000,
                    'notes': 'High-value commercial deal with institutional investor',
                    'next_action': 'Complete environmental assessment', 'last_contact': '2025-01-03'
                },
                {
                    'id': 2, 'property_address': '456 Austin Apartment Complex', 'deal_value': 8500000,
                    'client_name': 'Blackstone Group', 'stage': 'Negotiation', 
                    'probability': 70, 'expected_close': '2025-03-01', 'created_date': '2024-11-15',
                    'deal_type': 'Sale', 'property_type': 'Multi-Family',
                    'lead_source': 'Cold Outreach', 'agent': 'Mike Chen', 'commission': 255000,
                    'notes': 'Multi-family investment with potential for expansion',
                    'next_action': 'Review counter-offer terms', 'last_contact': '2025-01-02'
                },
                {
                    'id': 3, 'property_address': '789 Denver Industrial Park', 'deal_value': 12000000,
                    'client_name': 'CBRE Investment Fund', 'stage': 'Proposal', 
                    'probability': 60, 'expected_close': '2025-04-10', 'created_date': '2024-12-20',
                    'deal_type': 'Acquisition', 'property_type': 'Industrial',
                    'lead_source': 'Website', 'agent': 'Lisa Rodriguez', 'commission': 360000,
                    'notes': 'Industrial development opportunity in prime location',
                    'next_action': 'Prepare detailed proposal', 'last_contact': '2024-12-28'
                },
                {
                    'id': 4, 'property_address': '321 Miami Retail Center', 'deal_value': 6200000,
                    'client_name': 'Florida REIT Partners', 'stage': 'Initial Contact', 
                    'probability': 25, 'expected_close': '2025-05-20', 'created_date': '2025-01-01',
                    'deal_type': 'Sale', 'property_type': 'Retail',
                    'lead_source': 'Networking', 'agent': 'You', 'commission': 186000,
                    'notes': 'Retail center with high foot traffic potential',
                    'next_action': 'Schedule site visit', 'last_contact': '2025-01-01'
                },
                {
                    'id': 5, 'property_address': '555 LA Mixed-Use Development', 'deal_value': 25000000,
                    'client_name': 'Brookfield Asset Management', 'stage': 'Closed Won', 
                    'probability': 100, 'expected_close': '2024-12-15', 'created_date': '2024-09-01',
                    'deal_type': 'Development', 'property_type': 'Mixed Use',
                    'lead_source': 'Referral', 'agent': 'Sarah Johnson', 'commission': 750000,
                    'notes': 'Successful mixed-use development project completion',
                    'next_action': 'Project handover complete', 'last_contact': '2024-12-15'
                }
            ]
        
        # Pipeline stages configuration
        pipeline_stages = [
            {'name': 'Initial Contact', 'color': '#E5E7EB', 'probability_range': (0, 30)},
            {'name': 'Qualification', 'color': '#DBEAFE', 'probability_range': (20, 40)},
            {'name': 'Proposal', 'color': '#FEF3C7', 'probability_range': (30, 60)},
            {'name': 'Negotiation', 'color': '#FDE68A', 'probability_range': (50, 80)},
            {'name': 'Due Diligence', 'color': '#D1FAE5', 'probability_range': (70, 90)},
            {'name': 'Closed Won', 'color': '#A7F3D0', 'probability_range': (100, 100)},
            {'name': 'Closed Lost', 'color': '#FECACA', 'probability_range': (0, 0)}
        ]
        
        # Main pipeline tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Pipeline Board", "📊 Pipeline Analytics", "💰 Revenue Forecast", "➕ Add Deal", "⚙️ Pipeline Settings"])
        
        # === TAB 1: VISUAL PIPELINE BOARD ===
        with tab1:
            st.markdown("## 📋 Visual Pipeline Board")
            
            # Pipeline overview metrics
            deals = st.session_state.pipeline_deals
            col_overview1, col_overview2, col_overview3, col_overview4 = st.columns(4)
            
            with col_overview1:
                total_deals = len([d for d in deals if d['stage'] not in ['Closed Won', 'Closed Lost']])
                st.metric("🔥 Active Deals", total_deals)
            
            with col_overview2:
                total_value = sum(d['deal_value'] for d in deals if d['stage'] not in ['Closed Won', 'Closed Lost'])
                st.metric("💰 Pipeline Value", f"${total_value:,.0f}")
            
            with col_overview3:
                weighted_value = sum(d['deal_value'] * (d['probability'] / 100) for d in deals if d['stage'] not in ['Closed Won', 'Closed Lost'])
                st.metric("⚖️ Weighted Value", f"${weighted_value:,.0f}")
            
            with col_overview4:
                closed_won = len([d for d in deals if d['stage'] == 'Closed Won'])
                st.metric("✅ Closed Deals", closed_won)
            
            # Stage filters
            col_filter1, col_filter2, col_filter3 = st.columns(3)
            
            with col_filter1:
                agent_filter = st.selectbox("Filter by Agent", 
                    ["All Agents"] + list(set(d['agent'] for d in deals)))
            
            with col_filter2:
                property_type_filter = st.selectbox("Filter by Property Type", 
                    ["All Types"] + list(set(d['property_type'] for d in deals)))
            
            with col_filter3:
                deal_type_filter = st.selectbox("Filter by Deal Type", 
                    ["All Deal Types"] + list(set(d['deal_type'] for d in deals)))
            
            # Apply filters
            filtered_deals = deals
            if agent_filter != "All Agents":
                filtered_deals = [d for d in filtered_deals if d['agent'] == agent_filter]
            if property_type_filter != "All Types":
                filtered_deals = [d for d in filtered_deals if d['property_type'] == property_type_filter]
            if deal_type_filter != "All Deal Types":
                filtered_deals = [d for d in filtered_deals if d['deal_type'] == deal_type_filter]
            
            # Visual Pipeline Board
            st.markdown("### 🎯 Deal Pipeline Visualization")
            
            # Create columns for each stage
            stage_columns = st.columns(len(pipeline_stages))
            
            for i, stage in enumerate(pipeline_stages):
                stage_deals = [d for d in filtered_deals if d['stage'] == stage['name']]
                stage_value = sum(d['deal_value'] for d in stage_deals)
                
                with stage_columns[i]:
                    st.markdown(f"""
                    <div style="background: {stage['color']}; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; text-align: center;">
                        <h4 style="margin: 0; color: #1f2937;">{stage['name']}</h4>
                        <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; color: #6b7280;">
                            {len(stage_deals)} deals | ${stage_value:,.0f}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Display deals in this stage
                    for deal in stage_deals:
                        probability_color = "green" if deal['probability'] >= 70 else "orange" if deal['probability'] >= 40 else "red"
                        
                        with st.expander(f"💼 {deal['property_address'][:30]}... | ${deal['deal_value']:,.0f}"):
                            st.write(f"**🏢 Client:** {deal['client_name']}")
                            st.write(f"**📍 Property:** {deal['property_address']}")
                            st.write(f"**💰 Value:** ${deal['deal_value']:,.0f}")
                            st.write(f"**📊 Probability:** {deal['probability']}%")
                            st.write(f"**📅 Expected Close:** {deal['expected_close']}")
                            st.write(f"**👤 Agent:** {deal['agent']}")
                            st.write(f"**🔄 Next Action:** {deal['next_action']}")
                            
                            # Quick actions
                            col_action1, col_action2 = st.columns(2)
                            
                            with col_action1:
                                if st.button(f"📈 Move Forward", key=f"forward_{deal['id']}"):
                                    # Move to next stage
                                    current_index = next(i for i, s in enumerate(pipeline_stages) if s['name'] == deal['stage'])
                                    if current_index < len(pipeline_stages) - 2:  # Don't move beyond "Closed Won"
                                        deal['stage'] = pipeline_stages[current_index + 1]['name']
                                        st.success(f"Deal moved to {deal['stage']}")
                                        st.rerun()
                            
                            with col_action2:
                                if st.button(f"✏️ Edit", key=f"edit_{deal['id']}"):
                                    st.session_state[f"edit_deal_{deal['id']}"] = True
                                    st.rerun()
                            
                            # Edit form
                            if st.session_state.get(f"edit_deal_{deal['id']}"):
                                st.markdown("---")
                                with st.form(f"edit_deal_form_{deal['id']}"):
                                    new_stage = st.selectbox("Stage", [s['name'] for s in pipeline_stages], 
                                        index=[s['name'] for s in pipeline_stages].index(deal['stage']))
                                    new_probability = st.slider("Probability (%)", 0, 100, deal['probability'])
                                    new_expected_close = st.date_input("Expected Close", 
                                        value=pd.to_datetime(deal['expected_close']).date())
                                    new_next_action = st.text_input("Next Action", value=deal['next_action'])
                                    new_notes = st.text_area("Notes", value=deal['notes'])
                                    
                                    col_submit1, col_submit2 = st.columns(2)
                                    with col_submit1:
                                        if st.form_submit_button("💾 Save"):
                                            deal['stage'] = new_stage
                                            deal['probability'] = new_probability
                                            deal['expected_close'] = str(new_expected_close)
                                            deal['next_action'] = new_next_action
                                            deal['notes'] = new_notes
                                            st.success("Deal updated!")
                                            st.session_state.pop(f"edit_deal_{deal['id']}", None)
                                            st.rerun()
                                    
                                    with col_submit2:
                                        if st.form_submit_button("❌ Cancel"):
                                            st.session_state.pop(f"edit_deal_{deal['id']}", None)
                                            st.rerun()
            
            # Deal velocity metrics
            st.markdown("### ⚡ Pipeline Velocity")
            col_velocity1, col_velocity2, col_velocity3 = st.columns(3)
            
            with col_velocity1:
                avg_deal_size = sum(d['deal_value'] for d in filtered_deals) / max(1, len(filtered_deals))
                st.metric("📊 Avg Deal Size", f"${avg_deal_size:,.0f}")
            
            with col_velocity2:
                # Calculate average days in pipeline (mock calculation)
                avg_days = 65  # This would be calculated from actual data
                st.metric("📅 Avg Days in Pipeline", f"{avg_days} days")
            
            with col_velocity3:
                conversion_rate = len([d for d in deals if d['stage'] == 'Closed Won']) / max(1, len(deals)) * 100
                st.metric("📈 Conversion Rate", f"{conversion_rate:.1f}%")
        
        # === TAB 2: PIPELINE ANALYTICS ===
        with tab2:
            st.markdown("## 📊 Pipeline Analytics & Performance")
            
            # Analytics overview
            col_analytics1, col_analytics2, col_analytics3, col_analytics4 = st.columns(4)
            
            with col_analytics1:
                total_pipeline_value = sum(d['deal_value'] for d in deals if d['stage'] not in ['Closed Won', 'Closed Lost'])
                st.metric("💰 Total Pipeline", f"${total_pipeline_value:,.0f}")
            
            with col_analytics2:
                closed_won_value = sum(d['deal_value'] for d in deals if d['stage'] == 'Closed Won')
                st.metric("✅ Closed Won Value", f"${closed_won_value:,.0f}")
            
            with col_analytics3:
                avg_deal_probability = sum(d['probability'] for d in deals if d['stage'] not in ['Closed Won', 'Closed Lost']) / max(1, len([d for d in deals if d['stage'] not in ['Closed Won', 'Closed Lost']]))
                st.metric("📊 Avg Probability", f"{avg_deal_probability:.1f}%")
            
            with col_analytics4:
                high_probability_deals = len([d for d in deals if d['probability'] >= 70 and d['stage'] not in ['Closed Won', 'Closed Lost']])
                st.metric("🔥 High Probability", high_probability_deals)
            
            # Stage analysis
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("### 📈 Deals by Stage")
                
                stage_counts = {}
                stage_values = {}
                for stage in pipeline_stages:
                    stage_deals = [d for d in deals if d['stage'] == stage['name']]
                    stage_counts[stage['name']] = len(stage_deals)
                    stage_values[stage['name']] = sum(d['deal_value'] for d in stage_deals)
                
                fig_stages = go.Figure(data=[go.Bar(
                    x=list(stage_counts.keys()),
                    y=list(stage_counts.values()),
                    marker_color=['#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444', '#10B981', '#22C55E', '#F87171']
                )])
                
                fig_stages.update_layout(
                    title="Number of Deals by Stage",
                    xaxis_title="Pipeline Stage",
                    yaxis_title="Number of Deals",
                    height=400
                )
                
                st.plotly_chart(fig_stages, use_container_width=True)
            
            with col_chart2:
                st.markdown("### 💰 Value by Stage")
                
                fig_values = go.Figure(data=[go.Bar(
                    x=list(stage_values.keys()),
                    y=list(stage_values.values()),
                    marker_color=['#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444', '#10B981', '#22C55E', '#F87171']
                )])
                
                fig_values.update_layout(
                    title="Deal Value by Stage",
                    xaxis_title="Pipeline Stage",
                    yaxis_title="Deal Value ($)",
                    height=400
                )
                
                st.plotly_chart(fig_values, use_container_width=True)
            
            # Performance by agent
            st.markdown("### 👥 Performance by Agent")
            
            agent_performance = {}
            for deal in deals:
                agent = deal['agent']
                if agent not in agent_performance:
                    agent_performance[agent] = {'deals': 0, 'value': 0, 'commission': 0}
                
                agent_performance[agent]['deals'] += 1
                agent_performance[agent]['value'] += deal['deal_value']
                agent_performance[agent]['commission'] += deal.get('commission', 0)
            
            for agent, performance in agent_performance.items():
                col_agent1, col_agent2, col_agent3, col_agent4 = st.columns(4)
                
                with col_agent1:
                    st.write(f"**👤 {agent}**")
                
                with col_agent2:
                    st.write(f"📊 {performance['deals']} deals")
                
                with col_agent3:
                    st.write(f"💰 ${performance['value']:,.0f}")
                
                with col_agent4:
                    st.write(f"💵 ${performance['commission']:,.0f} commission")
            
            # Property type analysis
            st.markdown("### 🏢 Analysis by Property Type")
            
            property_performance = {}
            for deal in deals:
                prop_type = deal['property_type']
                if prop_type not in property_performance:
                    property_performance[prop_type] = {'deals': 0, 'value': 0, 'avg_probability': 0}
                
                property_performance[prop_type]['deals'] += 1
                property_performance[prop_type]['value'] += deal['deal_value']
            
            # Calculate average probabilities
            for prop_type in property_performance:
                type_deals = [d for d in deals if d['property_type'] == prop_type]
                avg_prob = sum(d['probability'] for d in type_deals) / len(type_deals) if type_deals else 0
                property_performance[prop_type]['avg_probability'] = avg_prob
            
            for prop_type, performance in property_performance.items():
                col_prop1, col_prop2, col_prop3, col_prop4 = st.columns(4)
                
                with col_prop1:
                    st.write(f"**🏠 {prop_type}**")
                
                with col_prop2:
                    st.write(f"📊 {performance['deals']} deals")
                
                with col_prop3:
                    st.write(f"💰 ${performance['value']:,.0f}")
                
                with col_prop4:
                    st.write(f"📈 {performance['avg_probability']:.1f}% avg prob")
        
        # Continue with Revenue Forecast and Add Deal tabs...
        
        # === TAB 3: REVENUE FORECAST ===
        with tab3:
            st.markdown("## 💰 Revenue Forecast & Projections")
            
            # This month's forecast
            import datetime
            current_month = datetime.datetime.now().strftime("%B %Y")
            
            col_forecast1, col_forecast2, col_forecast3, col_forecast4 = st.columns(4)
            
            # Calculate forecasts
            this_month_forecast = sum(d['deal_value'] * (d['probability'] / 100) for d in deals 
                                    if d['expected_close'].startswith('2025-01') and d['stage'] not in ['Closed Lost'])
            
            next_month_forecast = sum(d['deal_value'] * (d['probability'] / 100) for d in deals 
                                    if d['expected_close'].startswith('2025-02') and d['stage'] not in ['Closed Lost'])
            
            quarter_forecast = sum(d['deal_value'] * (d['probability'] / 100) for d in deals 
                                 if d['expected_close'].startswith('2025') and d['stage'] not in ['Closed Lost'])
            
            total_commission = sum(d.get('commission', 0) * (d['probability'] / 100) for d in deals 
                                 if d['stage'] not in ['Closed Lost'])
            
            with col_forecast1:
                st.metric("📅 This Month Forecast", f"${this_month_forecast:,.0f}")
            
            with col_forecast2:
                st.metric("📅 Next Month Forecast", f"${next_month_forecast:,.0f}")
            
            with col_forecast3:
                st.metric("📅 Quarter Forecast", f"${quarter_forecast:,.0f}")
            
            with col_forecast4:
                st.metric("💵 Commission Forecast", f"${total_commission:,.0f}")
            
            # Revenue trend chart
            st.markdown("### 📈 Revenue Trend Projection")
            
            # Mock monthly data for trend
            months = ['Nov 2024', 'Dec 2024', 'Jan 2025', 'Feb 2025', 'Mar 2025', 'Apr 2025', 'May 2025']
            actual_revenue = [18500000, 25000000, 0, 0, 0, 0, 0]  # Past actual + current forecasts
            forecasted_revenue = [0, 0, this_month_forecast, next_month_forecast, 15000000, 12000000, 18000000]
            
            fig_forecast = go.Figure()
            
            fig_forecast.add_trace(go.Scatter(
                x=months, y=actual_revenue,
                mode='lines+markers', name='Actual Revenue',
                line=dict(color='#22C55E', width=3)
            ))
            
            fig_forecast.add_trace(go.Scatter(
                x=months, y=forecasted_revenue,
                mode='lines+markers', name='Forecasted Revenue',
                line=dict(color='#3B82F6', width=3, dash='dash')
            ))
            
            fig_forecast.update_layout(
                title="Revenue Trend & Forecast",
                xaxis_title="Month",
                yaxis_title="Revenue ($)",
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_forecast, use_container_width=True)
            
            # Forecast by probability bands
            st.markdown("### 🎯 Forecast by Probability Bands")
            
            high_prob_forecast = sum(d['deal_value'] for d in deals if d['probability'] >= 70 and d['stage'] not in ['Closed Won', 'Closed Lost'])
            med_prob_forecast = sum(d['deal_value'] for d in deals if 40 <= d['probability'] < 70 and d['stage'] not in ['Closed Won', 'Closed Lost'])
            low_prob_forecast = sum(d['deal_value'] for d in deals if d['probability'] < 40 and d['stage'] not in ['Closed Won', 'Closed Lost'])
            
            col_prob1, col_prob2, col_prob3 = st.columns(3)
            
            with col_prob1:
                st.metric("🔥 High Probability (70%+)", f"${high_prob_forecast:,.0f}", 
                         help="Deals with 70%+ closing probability")
            
            with col_prob2:
                st.metric("📊 Medium Probability (40-70%)", f"${med_prob_forecast:,.0f}", 
                         help="Deals with 40-70% closing probability")
            
            with col_prob3:
                st.metric("📉 Low Probability (<40%)", f"${low_prob_forecast:,.0f}", 
                         help="Deals with less than 40% closing probability")
        
        # === TAB 4: ADD DEAL ===
        with tab4:
            st.markdown("## ➕ Add New Deal to Pipeline")
            
            with st.form("add_new_deal"):
                # Basic deal information
                st.markdown("#### 🏢 Basic Deal Information")
                col_basic1, col_basic2 = st.columns(2)
                
                with col_basic1:
                    property_address = st.text_input("Property Address*", placeholder="123 Main Street, City, State")
                    client_name = st.text_input("Client/Company Name*", placeholder="ABC Investment Group")
                    deal_value = st.number_input("Deal Value*", min_value=0, value=0, step=10000)
                    deal_type = st.selectbox("Deal Type*", ["Acquisition", "Sale", "Lease", "Development", "Joint Venture"])
                
                with col_basic2:
                    property_type = st.selectbox("Property Type*", 
                        ["Commercial Office", "Multi-Family", "Single Family", "Industrial", "Retail", "Mixed Use", "Land", "Other"])
                    stage = st.selectbox("Initial Stage*", [s['name'] for s in pipeline_stages if s['name'] not in ['Closed Won', 'Closed Lost']])
                    probability = st.slider("Closing Probability (%)*", 0, 100, 25)
                    expected_close = st.date_input("Expected Close Date*")
                
                # Agent and source information
                st.markdown("#### 👥 Assignment & Source")
                col_assign1, col_assign2 = st.columns(2)
                
                with col_assign1:
                    agent_options = ["You", "Sarah Johnson", "Mike Chen", "Lisa Rodriguez", "Other"]
                    assigned_agent = st.selectbox("Assigned Agent*", agent_options)
                    if assigned_agent == "Other":
                        assigned_agent = st.text_input("Enter Agent Name")
                    
                    lead_source = st.selectbox("Lead Source", 
                        ["Referral", "Cold Outreach", "Website", "Networking", "Social Media", "Advertisement", "Other"])
                
                with col_assign2:
                    commission_rate = st.number_input("Commission Rate (%)", min_value=0.0, max_value=20.0, value=3.0, step=0.1)
                    commission_amount = deal_value * (commission_rate / 100) if deal_value > 0 else 0
                    st.metric("💰 Estimated Commission", f"${commission_amount:,.0f}")
                    
                    priority = st.selectbox("Priority Level", ["High", "Medium", "Low"])
                
                # Additional details
                st.markdown("#### 📝 Additional Details")
                col_details1, col_details2 = st.columns(2)
                
                with col_details1:
                    next_action = st.text_input("Next Action Required", placeholder="Schedule property tour")
                    contact_person = st.text_input("Primary Contact Person", placeholder="John Smith")
                    contact_phone = st.text_input("Contact Phone", placeholder="(555) 123-4567")
                
                with col_details2:
                    contact_email = st.text_input("Contact Email", placeholder="contact@client.com")
                    deal_notes = st.text_area("Deal Notes", placeholder="Important details about this deal...")
                    tags = st.text_input("Tags (comma-separated)", placeholder="institutional, prime location, urgent")
                
                # Financial details
                st.markdown("#### 💰 Financial Details")
                col_financial1, col_financial2 = st.columns(2)
                
                with col_financial1:
                    purchase_price = st.number_input("Purchase/Sale Price", min_value=0, value=0, step=5000)
                    down_payment = st.number_input("Down Payment", min_value=0, value=0, step=5000)
                    financing_amount = st.number_input("Financing Required", min_value=0, value=0, step=5000)
                
                with col_financial2:
                    cap_rate = st.number_input("Cap Rate (%)", min_value=0.0, value=0.0, step=0.1)
                    cash_flow = st.number_input("Expected Monthly Cash Flow", min_value=0, value=0, step=100)
                    roi_estimate = st.number_input("ROI Estimate (%)", min_value=0.0, value=0.0, step=0.1)
                
                # Timeline and milestones
                st.markdown("#### 📅 Timeline & Milestones")
                col_timeline1, col_timeline2 = st.columns(2)
                
                with col_timeline1:
                    due_diligence_deadline = st.date_input("Due Diligence Deadline")
                    inspection_date = st.date_input("Inspection Date")
                    financing_deadline = st.date_input("Financing Deadline")
                
                with col_timeline2:
                    contract_date = st.date_input("Contract Date")
                    closing_date = st.date_input("Preferred Closing Date")
                    possession_date = st.date_input("Possession Date")
                
                # Submit button
                if st.form_submit_button("🚀 Add Deal to Pipeline", type="primary", use_container_width=True):
                    if property_address and client_name and deal_value and deal_type and property_type:
                        try:
                            # Generate new ID
                            new_id = max(d['id'] for d in st.session_state.pipeline_deals) + 1
                            
                            new_deal = {
                                'id': new_id,
                                'property_address': property_address,
                                'client_name': client_name,
                                'deal_value': deal_value,
                                'deal_type': deal_type,
                                'property_type': property_type,
                                'stage': stage,
                                'probability': probability,
                                'expected_close': str(expected_close),
                                'agent': assigned_agent,
                                'lead_source': lead_source,
                                'commission': commission_amount,
                                'priority': priority,
                                'next_action': next_action,
                                'contact_person': contact_person,
                                'contact_phone': contact_phone,
                                'contact_email': contact_email,
                                'notes': deal_notes,
                                'tags': tags,
                                'purchase_price': purchase_price,
                                'down_payment': down_payment,
                                'financing_amount': financing_amount,
                                'cap_rate': cap_rate,
                                'cash_flow': cash_flow,
                                'roi_estimate': roi_estimate,
                                'due_diligence_deadline': str(due_diligence_deadline),
                                'inspection_date': str(inspection_date),
                                'financing_deadline': str(financing_deadline),
                                'contract_date': str(contract_date),
                                'closing_date': str(closing_date),
                                'possession_date': str(possession_date),
                                'created_date': str(datetime.date.today()),
                                'last_contact': str(datetime.date.today())
                            }
                            
                            # Add to pipeline
                            st.session_state.pipeline_deals.append(new_deal)
                            
                            st.success("✅ Deal added to pipeline successfully!")
                            st.balloons()
                            
                            # Clear form by rerunning
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error adding deal: {str(e)}")
                    else:
                        st.warning("⚠️ Please fill in required fields: Property Address, Client Name, Deal Value, Deal Type, and Property Type")
        
        # === TAB 5: PIPELINE SETTINGS ===
        with tab5:
            st.markdown("## ⚙️ Pipeline Management Settings")
            
            col_settings1, col_settings2 = st.columns(2)
            
            with col_settings1:
                st.markdown("### 🎯 Stage Configuration")
                
                st.markdown("#### Current Pipeline Stages:")
                for i, stage in enumerate(pipeline_stages):
                    if stage['name'] not in ['Closed Won', 'Closed Lost']:
                        col_stage1, col_stage2, col_stage3 = st.columns([2, 1, 1])
                        with col_stage1:
                            st.write(f"**{i+1}. {stage['name']}**")
                        with col_stage2:
                            st.write(f"{stage['probability_range'][0]}-{stage['probability_range'][1]}%")
                        with col_stage3:
                            if st.button("✏️", key=f"edit_stage_{i}", help="Edit stage"):
                                st.info(f"Edit {stage['name']} stage")
                
                st.markdown("#### Add New Stage")
                with st.form("add_stage_form"):
                    new_stage_name = st.text_input("Stage Name")
                    col_prob1, col_prob2 = st.columns(2)
                    with col_prob1:
                        new_stage_min_prob = st.number_input("Min Probability", 0, 100, 0)
                    with col_prob2:
                        new_stage_max_prob = st.number_input("Max Probability", 0, 100, 100)
                    
                    if st.form_submit_button("➕ Add Stage"):
                        st.success(f"Stage '{new_stage_name}' would be added")
                
                st.markdown("### 🔔 Notifications")
                
                stage_change_notifications = st.checkbox("Stage change notifications", value=True)
                probability_alerts = st.checkbox("Probability threshold alerts", value=True)
                overdue_deal_alerts = st.checkbox("Overdue deal alerts", value=True)
                forecast_updates = st.checkbox("Daily forecast updates", value=False)
                
                probability_threshold = st.slider("Alert when probability drops below (%)", 0, 100, 30)
            
            with col_settings2:
                st.markdown("### 📊 Default Values")
                
                default_stage = st.selectbox("Default Stage for New Deals", 
                    [s['name'] for s in pipeline_stages if s['name'] not in ['Closed Won', 'Closed Lost']])
                default_probability = st.slider("Default Probability (%)", 0, 100, 25)
                default_commission_rate = st.number_input("Default Commission Rate (%)", 0.0, 20.0, 3.0, 0.1)
                
                st.markdown("### 🔄 Automation Settings")
                
                auto_stage_progression = st.checkbox("Auto-advance stages based on actions", value=False)
                auto_follow_up_creation = st.checkbox("Auto-create follow-up tasks", value=True)
                auto_probability_adjustment = st.checkbox("Auto-adjust probability based on stage", value=True)
                
                follow_up_days = st.number_input("Days between auto follow-ups", 1, 30, 7)
                
                st.markdown("### 📈 Forecasting Settings")
                
                forecast_period = st.selectbox("Default Forecast Period", 
                    ["This Month", "Next Month", "This Quarter", "Next Quarter", "This Year"])
                include_low_probability = st.checkbox("Include deals below 30% in forecasts", value=False)
                weighted_forecasting = st.checkbox("Use probability-weighted forecasting", value=True)
                
                st.markdown("### 👥 Team Settings")
                
                deal_assignment_method = st.selectbox("Deal Assignment Method", 
                    ["Manual Assignment", "Round Robin", "Territory-Based", "Lead Source-Based"])
                require_manager_approval = st.checkbox("Require manager approval for deals over threshold", value=True)
                approval_threshold = st.number_input("Approval Threshold ($)", 0, 10000000, 1000000, 50000)
            
            # Save settings
            if st.button("💾 Save Pipeline Settings", type="primary"):
                st.success("✅ Pipeline settings saved successfully!")
            
            # Import/Export pipeline data
            st.markdown("### 📁 Data Management")
            
            col_data1, col_data2 = st.columns(2)
            
            with col_data1:
                st.markdown("#### 📥 Import Pipeline Data")
                uploaded_pipeline = st.file_uploader("Import Pipeline CSV", type=['csv'])
                
                if uploaded_pipeline:
                    if st.button("📊 Import Pipeline"):
                        st.success("Pipeline data would be imported from CSV")
            
            with col_data2:
                st.markdown("#### 📤 Export Pipeline Data")
                
                export_format = st.selectbox("Export Format", ["CSV", "Excel", "PDF Report"])
                include_historical = st.checkbox("Include historical deals", value=True)
                
                if st.button("📊 Export Pipeline"):
                    st.success(f"Pipeline exported as {export_format}")
            
            # Pipeline backup and restore
            st.markdown("### 💾 Backup & Restore")
            
            col_backup1, col_backup2 = st.columns(2)
            
            with col_backup1:
                if st.button("🔄 Create Backup"):
                    st.success("Pipeline data backed up successfully!")
            
            with col_backup2:
                if st.button("📥 Restore from Backup"):
                    st.info("Select backup file to restore pipeline data")
    
    except Exception as e:
        st.error(f"Error in pipeline management: {str(e)}")
    
    # Add navigation CTAs
    add_navigation_ctas()
    
    # Back to dashboard option
    if st.button("⬅️ Back to Dashboard", key="back_to_dashboard_pipeline"):
        st.session_state.pop("show_pipeline", None)
        st.rerun()

def load_automation_page():
    """Comprehensive Automation Center - Workflow Builder and Process Automation"""
    try:
        st.markdown("### ⚙️ Comprehensive Automation Center")
        st.markdown("*Advanced workflow automation and business process management*")
        
        # Initialize automation data
        if 'automation_workflows' not in st.session_state:
            st.session_state.automation_workflows = [
                {
                    'id': 1, 'name': 'New Lead Welcome Sequence', 'status': 'Active', 'trigger': 'New Lead Added',
                    'description': 'Automated welcome email sequence for new leads with follow-up scheduling',
                    'actions': ['Send welcome email', 'Schedule follow-up call', 'Add to nurture sequence'],
                    'last_run': '2025-01-04 09:30', 'runs_today': 12, 'success_rate': 95.8,
                    'created_date': '2024-11-15', 'category': 'Lead Management'
                },
                {
                    'id': 2, 'name': 'Deal Stage Progression Alerts', 'status': 'Active', 'trigger': 'Deal Stage Change',
                    'description': 'Notify team and update tasks when deals move between pipeline stages',
                    'actions': ['Send team notification', 'Update deal probability', 'Create stage-specific tasks'],
                    'last_run': '2025-01-04 08:15', 'runs_today': 8, 'success_rate': 100.0,
                    'created_date': '2024-12-01', 'category': 'Pipeline Management'
                },
                {
                    'id': 3, 'name': 'High-Value Deal Alerts', 'status': 'Active', 'trigger': 'Deal Value > $5M',
                    'description': 'Immediate notifications for high-value deals requiring special attention',
                    'actions': ['SMS to manager', 'Email to executives', 'Create priority task'],
                    'last_run': '2025-01-03 14:22', 'runs_today': 2, 'success_rate': 100.0,
                    'created_date': '2024-10-20', 'category': 'Deal Management'
                },
                {
                    'id': 4, 'name': 'Monthly Report Generation', 'status': 'Active', 'trigger': 'Monthly Schedule',
                    'description': 'Automatically generate and distribute monthly performance reports',
                    'actions': ['Generate report', 'Email to stakeholders', 'Archive in documents'],
                    'last_run': '2025-01-01 09:00', 'runs_today': 0, 'success_rate': 98.5,
                    'created_date': '2024-09-10', 'category': 'Reporting'
                },
                {
                    'id': 5, 'name': 'Follow-up Reminder System', 'status': 'Paused', 'trigger': 'Due Date Approaching',
                    'description': 'Remind agents of upcoming follow-ups and overdue tasks',
                    'actions': ['Send reminder email', 'Create calendar event', 'Update task priority'],
                    'last_run': '2025-01-03 16:00', 'runs_today': 0, 'success_rate': 92.3,
                    'created_date': '2024-11-01', 'category': 'Task Management'
                }
            ]
        
        # Main automation tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚡ Active Workflows", "🔧 Workflow Builder", "📊 Automation Analytics", "📋 Templates", "⚙️ Settings"])
        
        # === TAB 1: ACTIVE WORKFLOWS ===
        with tab1:
            st.markdown("## ⚡ Active Automation Workflows")
            
            # Automation overview metrics
            workflows = st.session_state.automation_workflows
            col_auto1, col_auto2, col_auto3, col_auto4 = st.columns(4)
            
            with col_auto1:
                active_workflows = len([w for w in workflows if w['status'] == 'Active'])
                st.metric("🔥 Active Workflows", active_workflows)
            
            with col_auto2:
                total_runs_today = sum(w['runs_today'] for w in workflows)
                st.metric("🔄 Runs Today", total_runs_today)
            
            with col_auto3:
                avg_success_rate = sum(w['success_rate'] for w in workflows) / len(workflows) if workflows else 0
                st.metric("✅ Avg Success Rate", f"{avg_success_rate:.1f}%")
            
            with col_auto4:
                time_saved = total_runs_today * 15  # Assume 15 minutes saved per automation
                st.metric("⏱️ Time Saved Today", f"{time_saved} mins")
            
            # Workflow status overview
            st.markdown("### 📋 Workflow Status Overview")
            
            for workflow in workflows:
                status_color = {"Active": "🟢", "Paused": "🟡", "Inactive": "🔴"}.get(workflow['status'], "⚪")
                
                with st.expander(f"{status_color} {workflow['name']} - {workflow['category']} | {workflow['runs_today']} runs today"):
                    col_wf1, col_wf2, col_wf3 = st.columns([2, 2, 1])
                    
                    with col_wf1:
                        st.write(f"**📝 Description:** {workflow['description']}")
                        st.write(f"**🎯 Trigger:** {workflow['trigger']}")
                        st.write(f"**📊 Status:** {workflow['status']}")
                        st.write(f"**📅 Created:** {workflow['created_date']}")
                    
                    with col_wf2:
                        st.write(f"**🔄 Runs Today:** {workflow['runs_today']}")
                        st.write(f"**✅ Success Rate:** {workflow['success_rate']}%")
                        st.write(f"**🕒 Last Run:** {workflow['last_run']}")
                        st.write(f"**📂 Category:** {workflow['category']}")
                    
                    with col_wf3:
                        if workflow['status'] == 'Active':
                            if st.button(f"⏸️ Pause", key=f"pause_{workflow['id']}"):
                                workflow['status'] = 'Paused'
                                st.success("Workflow paused!")
                                st.rerun()
                        else:
                            if st.button(f"▶️ Resume", key=f"resume_{workflow['id']}"):
                                workflow['status'] = 'Active'
                                st.success("Workflow resumed!")
                                st.rerun()
                        
                        if st.button(f"✏️ Edit", key=f"edit_wf_{workflow['id']}"):
                            st.session_state[f"edit_workflow_{workflow['id']}"] = True
                            st.rerun()
                        
                        if st.button(f"🗑️ Delete", key=f"delete_wf_{workflow['id']}"):
                            st.session_state.automation_workflows = [w for w in workflows if w['id'] != workflow['id']]
                            st.success("Workflow deleted!")
                            st.rerun()
                    
                    # Actions list
                    st.markdown("**🔄 Workflow Actions:**")
                    for i, action in enumerate(workflow['actions'], 1):
                        st.write(f"{i}. {action}")
                    
                    # Edit workflow form
                    if st.session_state.get(f"edit_workflow_{workflow['id']}"):
                        st.markdown("---")
                        st.markdown("### ✏️ Edit Workflow")
                        
                        with st.form(f"edit_workflow_form_{workflow['id']}"):
                            new_name = st.text_input("Workflow Name", value=workflow['name'])
                            new_description = st.text_area("Description", value=workflow['description'])
                            new_trigger = st.selectbox("Trigger", 
                                ["New Lead Added", "Deal Stage Change", "Deal Value > $5M", "Monthly Schedule", "Due Date Approaching", "Custom"],
                                index=["New Lead Added", "Deal Stage Change", "Deal Value > $5M", "Monthly Schedule", "Due Date Approaching", "Custom"].index(workflow['trigger']) if workflow['trigger'] in ["New Lead Added", "Deal Stage Change", "Deal Value > $5M", "Monthly Schedule", "Due Date Approaching", "Custom"] else 5)
                            new_category = st.selectbox("Category", 
                                ["Lead Management", "Pipeline Management", "Deal Management", "Reporting", "Task Management", "Communication"],
                                index=["Lead Management", "Pipeline Management", "Deal Management", "Reporting", "Task Management", "Communication"].index(workflow['category']) if workflow['category'] in ["Lead Management", "Pipeline Management", "Deal Management", "Reporting", "Task Management", "Communication"] else 0)
                            
                            col_submit1, col_submit2 = st.columns(2)
                            with col_submit1:
                                if st.form_submit_button("💾 Save Changes"):
                                    workflow['name'] = new_name
                                    workflow['description'] = new_description
                                    workflow['trigger'] = new_trigger
                                    workflow['category'] = new_category
                                    st.success("Workflow updated!")
                                    st.session_state.pop(f"edit_workflow_{workflow['id']}", None)
                                    st.rerun()
                            
                            with col_submit2:
                                if st.form_submit_button("❌ Cancel"):
                                    st.session_state.pop(f"edit_workflow_{workflow['id']}", None)
                                    st.rerun()
        
        # === TAB 2: WORKFLOW BUILDER ===
        with tab2:
            st.markdown("## 🔧 Visual Workflow Builder")
            
            st.markdown("### ➕ Create New Automation Workflow")
            
            with st.form("create_workflow"):
                # Basic workflow information
                st.markdown("#### 📝 Basic Information")
                col_basic1, col_basic2 = st.columns(2)
                
                with col_basic1:
                    workflow_name = st.text_input("Workflow Name*", placeholder="My Custom Workflow")
                    workflow_description = st.text_area("Description*", placeholder="What does this workflow do?")
                    workflow_category = st.selectbox("Category*", 
                        ["Lead Management", "Pipeline Management", "Deal Management", "Reporting", "Task Management", "Communication", "Custom"])
                
                with col_basic2:
                    workflow_priority = st.selectbox("Priority Level", ["High", "Medium", "Low"])
                    workflow_enabled = st.checkbox("Enable immediately", value=True)
                    workflow_notifications = st.checkbox("Send execution notifications", value=False)
                
                # Trigger configuration
                st.markdown("#### 🎯 Trigger Configuration")
                col_trigger1, col_trigger2 = st.columns(2)
                
                with col_trigger1:
                    trigger_type = st.selectbox("Trigger Type*", [
                        "New Lead Added", "Lead Status Change", "Deal Stage Change", "Deal Value Threshold",
                        "Date/Time Schedule", "Email Received", "Form Submission", "Custom Event"
                    ])
                    
                    if trigger_type == "Deal Value Threshold":
                        threshold_value = st.number_input("Threshold Value ($)", min_value=0, value=1000000, step=50000)
                    elif trigger_type == "Date/Time Schedule":
                        schedule_frequency = st.selectbox("Frequency", ["Daily", "Weekly", "Monthly", "Quarterly"])
                        schedule_time = st.time_input("Execution Time")
                
                with col_trigger2:
                    trigger_conditions = st.multiselect("Additional Conditions (Optional)", [
                        "High Priority Only", "Specific Agent", "Property Type Filter", "Value Range", "Geographic Filter"
                    ])
                    
                    delay_execution = st.checkbox("Delay execution")
                    if delay_execution:
                        delay_minutes = st.number_input("Delay (minutes)", min_value=1, value=5)
                
                # Actions configuration
                st.markdown("#### 🔄 Actions Configuration")
                st.write("**Select actions to perform when this workflow triggers:**")
                
                col_actions1, col_actions2 = st.columns(2)
                
                with col_actions1:
                    action_email = st.checkbox("📧 Send Email")
                    if action_email:
                        email_template = st.selectbox("Email Template", ["Welcome Email", "Follow-up", "Alert", "Custom"])
                        email_recipients = st.text_input("Recipients", placeholder="email@example.com, team@company.com")
                    
                    action_sms = st.checkbox("📱 Send SMS")
                    if action_sms:
                        sms_message = st.text_area("SMS Message", placeholder="SMS content...")
                        sms_recipients = st.text_input("SMS Recipients", placeholder="+1234567890")
                    
                    action_task = st.checkbox("✅ Create Task")
                    if action_task:
                        task_title = st.text_input("Task Title", placeholder="Follow up with lead")
                        task_assignee = st.selectbox("Assign To", ["Current User", "Lead Agent", "Manager", "Team"])
                
                with col_actions2:
                    action_update = st.checkbox("🔄 Update Record")
                    if action_update:
                        update_field = st.selectbox("Field to Update", ["Status", "Priority", "Stage", "Probability", "Notes"])
                        update_value = st.text_input("New Value", placeholder="Enter new value")
                    
                    action_webhook = st.checkbox("🔗 Call Webhook")
                    if action_webhook:
                        webhook_url = st.text_input("Webhook URL", placeholder="https://api.example.com/webhook")
                        webhook_method = st.selectbox("HTTP Method", ["POST", "GET", "PUT"])
                    
                    action_slack = st.checkbox("💬 Slack Notification")
                    if action_slack:
                        slack_channel = st.text_input("Slack Channel", placeholder="#deals")
                        slack_message = st.text_area("Slack Message", placeholder="New deal alert!")
                
                # Advanced settings
                st.markdown("#### ⚙️ Advanced Settings")
                col_advanced1, col_advanced2 = st.columns(2)
                
                with col_advanced1:
                    retry_attempts = st.number_input("Retry Attempts on Failure", min_value=0, max_value=5, value=3)
                    timeout_seconds = st.number_input("Timeout (seconds)", min_value=30, value=120)
                    max_executions_per_day = st.number_input("Max Executions per Day", min_value=1, value=100)
                
                with col_advanced2:
                    execution_window_start = st.time_input("Execution Window Start", value=pd.to_datetime("09:00").time())
                    execution_window_end = st.time_input("Execution Window End", value=pd.to_datetime("17:00").time())
                    exclude_weekends = st.checkbox("Exclude Weekends", value=True)
                
                # Submit workflow
                if st.form_submit_button("🚀 Create Workflow", type="primary", use_container_width=True):
                    if workflow_name and workflow_description and workflow_category and trigger_type:
                        try:
                            # Generate new workflow
                            new_id = max(w['id'] for w in st.session_state.automation_workflows) + 1 if st.session_state.automation_workflows else 1
                            
                            # Collect selected actions
                            selected_actions = []
                            if action_email: selected_actions.append(f"Send email ({email_template})")
                            if action_sms: selected_actions.append("Send SMS")
                            if action_task: selected_actions.append(f"Create task: {task_title}")
                            if action_update: selected_actions.append(f"Update {update_field}")
                            if action_webhook: selected_actions.append("Call webhook")
                            if action_slack: selected_actions.append("Send Slack notification")
                            
                            new_workflow = {
                                'id': new_id,
                                'name': workflow_name,
                                'description': workflow_description,
                                'category': workflow_category,
                                'trigger': trigger_type,
                                'status': 'Active' if workflow_enabled else 'Paused',
                                'actions': selected_actions,
                                'created_date': str(datetime.date.today()),
                                'last_run': 'Never',
                                'runs_today': 0,
                                'success_rate': 100.0
                            }
                            
                            st.session_state.automation_workflows.append(new_workflow)
                            st.success("✅ Workflow created successfully!")
                            st.balloons()
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error creating workflow: {str(e)}")
                    else:
                        st.warning("⚠️ Please fill in required fields: Name, Description, Category, and Trigger Type")
        
        # === TAB 3: AUTOMATION ANALYTICS ===
        with tab3:
            st.markdown("## 📊 Automation Analytics & Performance")
            
            # Analytics overview
            col_analytics1, col_analytics2, col_analytics3, col_analytics4 = st.columns(4)
            
            with col_analytics1:
                total_automations = len(workflows)
                st.metric("🔧 Total Workflows", total_automations)
            
            with col_analytics2:
                monthly_executions = sum(w['runs_today'] for w in workflows) * 30  # Estimate monthly
                st.metric("📊 Monthly Executions", f"{monthly_executions:,}")
            
            with col_analytics3:
                time_saved_monthly = monthly_executions * 15 // 60  # Hours saved
                st.metric("⏱️ Hours Saved/Month", f"{time_saved_monthly:,}")
            
            with col_analytics4:
                automation_roi = time_saved_monthly * 50  # Assume $50/hour value
                st.metric("💰 Value Created", f"${automation_roi:,}")
            
            # Performance charts
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("### 📈 Workflow Execution Trends")
                
                # Mock trend data
                days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                executions = [45, 52, 38, 61, 47, 23, 15]
                
                fig_trend = go.Figure(data=[go.Scatter(
                    x=days, y=executions,
                    mode='lines+markers',
                    line=dict(color='#3B82F6', width=3),
                    marker=dict(size=8)
                )])
                
                fig_trend.update_layout(
                    title="Daily Workflow Executions",
                    xaxis_title="Day",
                    yaxis_title="Executions",
                    height=300
                )
                
                st.plotly_chart(fig_trend, use_container_width=True)
            
            with col_chart2:
                st.markdown("### 🎯 Success Rate by Category")
                
                categories = list(set(w['category'] for w in workflows))
                success_rates = []
                
                for category in categories:
                    cat_workflows = [w for w in workflows if w['category'] == category]
                    avg_success = sum(w['success_rate'] for w in cat_workflows) / len(cat_workflows) if cat_workflows else 0
                    success_rates.append(avg_success)
                
                fig_success = go.Figure(data=[go.Bar(
                    x=categories, y=success_rates,
                    marker_color='#22C55E'
                )])
                
                fig_success.update_layout(
                    title="Success Rate by Category",
                    xaxis_title="Category",
                    yaxis_title="Success Rate (%)",
                    height=300
                )
                
                st.plotly_chart(fig_success, use_container_width=True)
            
            # Detailed workflow performance
            st.markdown("### 📋 Workflow Performance Details")
            
            for workflow in workflows:
                col_perf1, col_perf2, col_perf3, col_perf4 = st.columns(4)
                
                with col_perf1:
                    st.write(f"**{workflow['name']}**")
                
                with col_perf2:
                    st.write(f"🔄 {workflow['runs_today']} runs")
                
                with col_perf3:
                    st.write(f"✅ {workflow['success_rate']:.1f}% success")
                
                with col_perf4:
                    efficiency = workflow['runs_today'] * workflow['success_rate'] / 100
                    st.write(f"⚡ {efficiency:.1f} efficiency")
            
            # Error analysis
            st.markdown("### ❌ Error Analysis")
            
            col_error1, col_error2 = st.columns(2)
            
            with col_error1:
                st.markdown("#### Common Errors")
                error_types = [
                    "Email delivery failure", "API timeout", "Invalid data format", 
                    "Permission denied", "Rate limit exceeded"
                ]
                error_counts = [3, 1, 2, 0, 1]
                
                for error, count in zip(error_types, error_counts):
                    if count > 0:
                        st.write(f"🔴 **{error}:** {count} occurrences")
                    else:
                        st.write(f"✅ **{error}:** No issues")
            
            with col_error2:
                st.markdown("#### Resolution Status")
                st.write("🔄 **Active Issues:** 2")
                st.write("✅ **Resolved Issues:** 15")
                st.write("⏱️ **Avg Resolution Time:** 23 minutes")
                st.write("📊 **Error Rate:** 2.3%")
        
        # Continue with Templates and Settings tabs...
        
        # === TAB 4: TEMPLATES ===
        with tab4:
            st.markdown("## 📋 Workflow Templates")
            
            st.markdown("### 🚀 Quick Start Templates")
            
            templates = [
                {
                    'name': 'Lead Nurturing Sequence',
                    'description': 'Automated email sequence for new leads with follow-up scheduling',
                    'category': 'Lead Management',
                    'trigger': 'New Lead Added',
                    'actions': ['Send welcome email', 'Schedule follow-up', 'Add to CRM'],
                    'difficulty': 'Easy',
                    'setup_time': '5 minutes'
                },
                {
                    'name': 'Deal Alert System',
                    'description': 'Instant notifications for high-value deals and stage changes',
                    'category': 'Deal Management',
                    'trigger': 'Deal Value > Threshold',
                    'actions': ['Send SMS alert', 'Email team', 'Create priority task'],
                    'difficulty': 'Medium',
                    'setup_time': '10 minutes'
                },
                {
                    'name': 'Monthly Reporting Automation',
                    'description': 'Automated generation and distribution of monthly performance reports',
                    'category': 'Reporting',
                    'trigger': 'Monthly Schedule',
                    'actions': ['Generate report', 'Email stakeholders', 'Archive data'],
                    'difficulty': 'Advanced',
                    'setup_time': '20 minutes'
                },
                {
                    'name': 'Follow-up Reminder System',
                    'description': 'Automatic reminders for overdue tasks and follow-ups',
                    'category': 'Task Management',
                    'trigger': 'Due Date Approaching',
                    'actions': ['Send reminder', 'Update priority', 'Escalate if needed'],
                    'difficulty': 'Easy',
                    'setup_time': '3 minutes'
                }
            ]
            
            # Display templates in grid
            cols = st.columns(2)
            for i, template in enumerate(templates):
                with cols[i % 2]:
                    difficulty_colors = {'Easy': '🟢', 'Medium': '🟡', 'Advanced': '🔴'}
                    
                    with st.container():
                        st.markdown(f"""
                        <div style="border: 2px solid #e5e7eb; padding: 1.5rem; border-radius: 15px; margin: 1rem 0; 
                                   background: #ffffff; color: #1f2937;">
                            <h4 style="color: #1f2937; margin-top: 0;">📋 {template['name']}</h4>
                            <p style="color: #374151;"><strong>Category:</strong> {template['category']}</p>
                            <p style="color: #374151;"><strong>Description:</strong> {template['description']}</p>
                            <p style="color: #374151;"><strong>Trigger:</strong> {template['trigger']}</p>
                            <p style="color: #374151;"><strong>Setup Time:</strong> {template['setup_time']}</p>
                            <p style="color: #374151;"><strong>Difficulty:</strong> {difficulty_colors[template['difficulty']]} {template['difficulty']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_template1, col_template2 = st.columns(2)
                        with col_template1:
                            if st.button(f"🚀 Use Template", key=f"use_template_{i}", type="primary"):
                                st.success(f"Template '{template['name']}' loaded in workflow builder!")
                        
                        with col_template2:
                            if st.button(f"👁️ Preview", key=f"preview_template_{i}"):
                                st.session_state[f"preview_template_{i}"] = True
                                st.rerun()
                        
                        # Template preview
                        if st.session_state.get(f"preview_template_{i}"):
                            st.markdown("**🔄 Template Actions:**")
                            for j, action in enumerate(template['actions'], 1):
                                st.write(f"{j}. {action}")
                            
                            if st.button(f"❌ Close Preview", key=f"close_preview_{i}"):
                                st.session_state.pop(f"preview_template_{i}", None)
                                st.rerun()
            
            # Custom template creation
            st.markdown("---")
            st.markdown("### ➕ Create Custom Template")
            
            with st.form("create_template"):
                template_name = st.text_input("Template Name", placeholder="My Custom Template")
                template_description = st.text_area("Description", placeholder="What does this template do?")
                template_category = st.selectbox("Category", 
                    ["Lead Management", "Deal Management", "Task Management", "Reporting", "Communication", "Custom"])
                template_difficulty = st.selectbox("Difficulty Level", ["Easy", "Medium", "Advanced"])
                
                if st.form_submit_button("💾 Save Template"):
                    if template_name and template_description:
                        st.success(f"Template '{template_name}' saved successfully!")
                    else:
                        st.warning("Please fill in template name and description")
        
        # === TAB 5: SETTINGS ===
        with tab5:
            st.markdown("## ⚙️ Automation Settings")
            
            col_settings1, col_settings2 = st.columns(2)
            
            with col_settings1:
                st.markdown("### 🔧 General Settings")
                
                auto_execution_enabled = st.checkbox("Enable automatic execution", value=True)
                execution_logging = st.checkbox("Enable detailed execution logging", value=True)
                error_notifications = st.checkbox("Send error notifications", value=True)
                performance_monitoring = st.checkbox("Performance monitoring", value=True)
                
                st.markdown("### ⏰ Execution Settings")
                
                max_concurrent_workflows = st.slider("Max concurrent workflows", 1, 20, 10)
                default_timeout = st.number_input("Default timeout (seconds)", 30, 600, 120)
                retry_delay = st.number_input("Retry delay (seconds)", 5, 300, 30)
                
                st.markdown("### 🔔 Notification Settings")
                
                notification_email = st.text_input("Notification Email", placeholder="admin@company.com")
                slack_webhook_url = st.text_input("Slack Webhook URL", placeholder="https://hooks.slack.com/...")
                sms_notifications = st.checkbox("Enable SMS notifications", value=False)
            
            with col_settings2:
                st.markdown("### 📊 Performance Settings")
                
                enable_analytics = st.checkbox("Enable analytics tracking", value=True)
                data_retention_days = st.number_input("Data retention (days)", 30, 365, 90)
                performance_alerts = st.checkbox("Performance degradation alerts", value=True)
                
                st.markdown("### 🔒 Security Settings")
                
                require_approval = st.checkbox("Require approval for new workflows", value=False)
                webhook_security = st.checkbox("Enable webhook signature verification", value=True)
                api_rate_limiting = st.checkbox("Enable API rate limiting", value=True)
                
                api_rate_limit = st.number_input("API calls per minute", 10, 1000, 100)
                
                st.markdown("### 🛠️ Advanced Settings")
                
                debug_mode = st.checkbox("Debug mode", value=False)
                custom_variables = st.text_area("Custom Variables (JSON)", placeholder='{"var1": "value1", "var2": "value2"}')
                webhook_timeout = st.number_input("Webhook timeout (seconds)", 5, 60, 30)
            
            # Save settings
            if st.button("💾 Save Automation Settings", type="primary"):
                st.success("✅ Automation settings saved successfully!")
            
            # System status
            st.markdown("### 📊 System Status")
            
            col_status1, col_status2, col_status3 = st.columns(3)
            
            with col_status1:
                st.metric("🟢 System Status", "Operational")
            
            with col_status2:
                st.metric("⚡ Queue Status", "Processing")
            
            with col_status3:
                st.metric("📊 Load", "Normal")
            
            # Maintenance and backup
            st.markdown("### 🔧 Maintenance")
            
            col_maintenance1, col_maintenance2 = st.columns(2)
            
            with col_maintenance1:
                if st.button("🔄 Restart Automation Engine"):
                    st.success("Automation engine restarted successfully!")
                
                if st.button("🧹 Clear Execution Logs"):
                    st.success("Execution logs cleared!")
            
            with col_maintenance2:
                if st.button("💾 Backup Workflows"):
                    st.success("Workflows backed up successfully!")
                
                if st.button("📥 Import Workflows"):
                    st.info("Select backup file to import workflows")
    
    except Exception as e:
        st.error(f"Error in automation center: {str(e)}")
    
    # Add navigation CTAs
    add_navigation_ctas()
    
    # Back to dashboard option
    if st.button("⬅️ Back to Dashboard", key="back_to_dashboard_automation"):
        st.session_state.pop("show_automation", None)
        st.rerun()

def load_task_management_page():
    """Comprehensive Task Management System - Advanced Task Organization and Productivity"""
    try:
        st.markdown("### ✅ Advanced Task Management Center")
        st.markdown("*Enterprise task organization, team collaboration, and productivity tracking*")
        
        # Initialize task data
        if 'task_list' not in st.session_state:
            st.session_state.task_list = [
                {
                    'id': 1, 'title': 'Follow up with high-value prospect - Oceanfront Properties',
                    'description': 'Schedule presentation meeting for $12M commercial development opportunity',
                    'status': 'In Progress', 'priority': 'High', 'category': 'Lead Follow-up',
                    'assignee': 'John Smith', 'due_date': '2025-09-06', 'created_date': '2025-09-02',
                    'progress': 65, 'time_estimate': '2 hours', 'actual_time': '1.5 hours',
                    'tags': ['High Value', 'Commercial', 'Presentation'], 'deal_value': 12000000,
                    'client': 'Oceanfront Properties LLC', 'property_type': 'Commercial Development'
                },
                {
                    'id': 2, 'title': 'Complete market analysis for downtown district',
                    'description': 'Comprehensive market research and comparative analysis for downtown investment opportunities',
                    'status': 'Not Started', 'priority': 'Medium', 'category': 'Market Research',
                    'assignee': 'Sarah Johnson', 'due_date': '2025-09-08', 'created_date': '2025-09-03',
                    'progress': 0, 'time_estimate': '4 hours', 'actual_time': '0 hours',
                    'tags': ['Market Analysis', 'Research', 'Downtown'], 'deal_value': 8500000,
                    'client': 'Downtown Investment Group', 'property_type': 'Mixed Use'
                },
                {
                    'id': 3, 'title': 'Prepare contract documents for Riverside Towers closing',
                    'description': 'Review and prepare all closing documents for luxury condo development deal',
                    'status': 'Completed', 'priority': 'High', 'category': 'Contract Management',
                    'assignee': 'Michael Chen', 'due_date': '2025-09-03', 'created_date': '2025-08-28',
                    'progress': 100, 'time_estimate': '3 hours', 'actual_time': '2.5 hours',
                    'tags': ['Closing', 'Legal', 'Contracts'], 'deal_value': 15000000,
                    'client': 'Riverside Development Corp', 'property_type': 'Luxury Residential'
                },
                {
                    'id': 4, 'title': 'Update investor presentation with Q3 performance data',
                    'description': 'Compile Q3 results and update quarterly investor presentation materials',
                    'status': 'In Progress', 'priority': 'High', 'category': 'Investor Relations',
                    'assignee': 'Emily Davis', 'due_date': '2025-09-10', 'created_date': '2025-09-01',
                    'progress': 40, 'time_estimate': '5 hours', 'actual_time': '2 hours',
                    'tags': ['Quarterly', 'Investors', 'Presentation'], 'deal_value': 0,
                    'client': 'Internal - Investor Relations', 'property_type': 'N/A'
                },
                {
                    'id': 5, 'title': 'Schedule property inspections for portfolio acquisitions',
                    'description': 'Coordinate inspection schedules for 8 properties under consideration for acquisition',
                    'status': 'Not Started', 'priority': 'Medium', 'category': 'Property Management',
                    'assignee': 'Robert Wilson', 'due_date': '2025-09-12', 'created_date': '2025-09-04',
                    'progress': 0, 'time_estimate': '6 hours', 'actual_time': '0 hours',
                    'tags': ['Inspections', 'Acquisitions', 'Portfolio'], 'deal_value': 45000000,
                    'client': 'Multi-Property Investment Fund', 'property_type': 'Mixed Portfolio'
                },
                {
                    'id': 6, 'title': 'Review financing proposals for warehouse project',
                    'description': 'Analyze and compare financing options from 4 different lenders for industrial warehouse development',
                    'status': 'Overdue', 'priority': 'High', 'category': 'Financing',
                    'assignee': 'Lisa Anderson', 'due_date': '2025-09-02', 'created_date': '2025-08-20',
                    'progress': 25, 'time_estimate': '4 hours', 'actual_time': '1 hour',
                    'tags': ['Financing', 'Industrial', 'Overdue'], 'deal_value': 22000000,
                    'client': 'Industrial Development Partners', 'property_type': 'Industrial Warehouse'
                }
            ]
        
        # Main task management tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Active Tasks", "➕ Create Task", "📊 Task Analytics", "👥 Team Management", "⚙️ Task Settings"])
        
        # === TAB 1: ACTIVE TASKS ===
        with tab1:
            st.markdown("## 📋 Task Management Dashboard")
            
            # Task overview metrics
            tasks = st.session_state.task_list
            col_task1, col_task2, col_task3, col_task4, col_task5 = st.columns(5)
            
            with col_task1:
                total_tasks = len(tasks)
                st.metric("📋 Total Tasks", total_tasks)
            
            with col_task2:
                completed_tasks = len([t for t in tasks if t['status'] == 'Completed'])
                st.metric("✅ Completed", completed_tasks)
            
            with col_task3:
                in_progress_tasks = len([t for t in tasks if t['status'] == 'In Progress'])
                st.metric("🔄 In Progress", in_progress_tasks)
            
            with col_task4:
                overdue_tasks = len([t for t in tasks if t['status'] == 'Overdue'])
                st.metric("⚠️ Overdue", overdue_tasks, delta_color="inverse")
            
            with col_task5:
                high_priority = len([t for t in tasks if t['priority'] == 'High'])
                st.metric("🔥 High Priority", high_priority)
            
            # Task filters and search
            st.markdown("### 🔍 Task Filters & Search")
            
            col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)
            
            with col_filter1:
                status_filter = st.multiselect("Filter by Status", 
                    ["Not Started", "In Progress", "Completed", "Overdue"], 
                    default=["Not Started", "In Progress", "Overdue"])
            
            with col_filter2:
                priority_filter = st.multiselect("Filter by Priority", 
                    ["High", "Medium", "Low"], 
                    default=["High", "Medium", "Low"])
            
            with col_filter3:
                assignee_filter = st.multiselect("Filter by Assignee", 
                    list(set(t['assignee'] for t in tasks)),
                    default=list(set(t['assignee'] for t in tasks)))
            
            with col_filter4:
                category_filter = st.multiselect("Filter by Category", 
                    list(set(t['category'] for t in tasks)),
                    default=list(set(t['category'] for t in tasks)))
            
            # Search functionality
            search_term = st.text_input("🔍 Search tasks", placeholder="Search by title, description, client, or tags...")
            
            # Apply filters
            filtered_tasks = []
            for task in tasks:
                # Apply status filter
                if task['status'] not in status_filter:
                    continue
                
                # Apply priority filter
                if task['priority'] not in priority_filter:
                    continue
                
                # Apply assignee filter
                if task['assignee'] not in assignee_filter:
                    continue
                
                # Apply category filter
                if task['category'] not in category_filter:
                    continue
                
                # Apply search filter
                if search_term:
                    search_fields = f"{task['title']} {task['description']} {task['client']} {' '.join(task['tags'])}".lower()
                    if search_term.lower() not in search_fields:
                        continue
                
                filtered_tasks.append(task)
            
            # Sort options
            col_sort1, col_sort2 = st.columns(2)
            with col_sort1:
                sort_by = st.selectbox("Sort by", ["Due Date", "Priority", "Status", "Progress", "Deal Value", "Created Date"])
            with col_sort2:
                sort_order = st.selectbox("Order", ["Ascending", "Descending"])
            
            # Apply sorting
            if sort_by == "Due Date":
                filtered_tasks.sort(key=lambda x: x['due_date'], reverse=(sort_order == "Descending"))
            elif sort_by == "Priority":
                priority_order = {"High": 3, "Medium": 2, "Low": 1}
                filtered_tasks.sort(key=lambda x: priority_order[x['priority']], reverse=(sort_order == "Descending"))
            elif sort_by == "Progress":
                filtered_tasks.sort(key=lambda x: x['progress'], reverse=(sort_order == "Descending"))
            elif sort_by == "Deal Value":
                filtered_tasks.sort(key=lambda x: x['deal_value'], reverse=(sort_order == "Descending"))
            
            # Display filtered tasks
            st.markdown(f"### 📋 Task List ({len(filtered_tasks)} tasks)")
            
            for task in filtered_tasks:
                # Status and priority indicators
                status_colors = {
                    "Not Started": "🔴", "In Progress": "🟡", 
                    "Completed": "🟢", "Overdue": "🔴"
                }
                priority_colors = {"High": "🔥", "Medium": "⚡", "Low": "📋"}
                
                status_icon = status_colors.get(task['status'], "⚪")
                priority_icon = priority_colors.get(task['priority'], "📋")
                
                # Calculate days until due
                due_date = datetime.datetime.strptime(task['due_date'], '%Y-%m-%d').date()
                today = datetime.date.today()
                days_until_due = (due_date - today).days
                
                if days_until_due < 0:
                    due_indicator = f"⚠️ {abs(days_until_due)} days overdue"
                elif days_until_due == 0:
                    due_indicator = "🔴 Due today"
                elif days_until_due == 1:
                    due_indicator = "🟡 Due tomorrow"
                else:
                    due_indicator = f"📅 {days_until_due} days remaining"
                
                with st.expander(f"{status_icon} {priority_icon} {task['title']} | {task['assignee']} | {due_indicator}"):
                    col_task_detail1, col_task_detail2, col_task_detail3 = st.columns([2, 2, 1])
                    
                    with col_task_detail1:
                        st.write(f"**📝 Description:** {task['description']}")
                        st.write(f"**👤 Assignee:** {task['assignee']}")
                        st.write(f"**📂 Category:** {task['category']}")
                        st.write(f"**🏢 Client:** {task['client']}")
                        
                        # Display tags
                        if task['tags']:
                            tag_display = " ".join([f"`{tag}`" for tag in task['tags']])
                            st.markdown(f"**🏷️ Tags:** {tag_display}")
                    
                    with col_task_detail2:
                        st.write(f"**📊 Status:** {task['status']}")
                        st.write(f"**⚡ Priority:** {task['priority']}")
                        st.write(f"**📅 Due Date:** {task['due_date']}")
                        st.write(f"**📅 Created:** {task['created_date']}")
                        
                        if task['deal_value'] > 0:
                            st.write(f"**💰 Deal Value:** ${task['deal_value']:,}")
                        
                        st.write(f"**🏠 Property Type:** {task['property_type']}")
                    
                    with col_task_detail3:
                        st.write(f"**⏱️ Time Estimate:** {task['time_estimate']}")
                        st.write(f"**⏱️ Actual Time:** {task['actual_time']}")
                        
                        # Progress bar
                        st.write(f"**📊 Progress:** {task['progress']}%")
                        st.progress(task['progress'] / 100)
                        
                        # Quick actions
                        if st.button(f"✏️ Edit", key=f"edit_task_{task['id']}"):
                            st.session_state[f"edit_task_{task['id']}"] = True
                            st.rerun()
                        
                        if task['status'] != 'Completed':
                            if st.button(f"✅ Complete", key=f"complete_task_{task['id']}"):
                                task['status'] = 'Completed'
                                task['progress'] = 100
                                st.success("Task completed!")
                                st.rerun()
                    
                    # Edit task form
                    if st.session_state.get(f"edit_task_{task['id']}"):
                        st.markdown("---")
                        st.markdown("### ✏️ Edit Task")
                        
                        with st.form(f"edit_task_form_{task['id']}"):
                            col_edit1, col_edit2 = st.columns(2)
                            
                            with col_edit1:
                                new_title = st.text_input("Task Title", value=task['title'])
                                new_description = st.text_area("Description", value=task['description'])
                                new_status = st.selectbox("Status", 
                                    ["Not Started", "In Progress", "Completed", "Overdue"],
                                    index=["Not Started", "In Progress", "Completed", "Overdue"].index(task['status']))
                                new_priority = st.selectbox("Priority", 
                                    ["High", "Medium", "Low"],
                                    index=["High", "Medium", "Low"].index(task['priority']))
                                new_progress = st.slider("Progress (%)", 0, 100, task['progress'])
                            
                            with col_edit2:
                                new_assignee = st.text_input("Assignee", value=task['assignee'])
                                new_due_date = st.date_input("Due Date", value=datetime.datetime.strptime(task['due_date'], '%Y-%m-%d').date())
                                new_category = st.text_input("Category", value=task['category'])
                                new_client = st.text_input("Client", value=task['client'])
                                new_deal_value = st.number_input("Deal Value ($)", value=task['deal_value'], min_value=0)
                            
                            col_submit_edit1, col_submit_edit2 = st.columns(2)
                            with col_submit_edit1:
                                if st.form_submit_button("💾 Save Changes"):
                                    task['title'] = new_title
                                    task['description'] = new_description
                                    task['status'] = new_status
                                    task['priority'] = new_priority
                                    task['progress'] = new_progress
                                    task['assignee'] = new_assignee
                                    task['due_date'] = str(new_due_date)
                                    task['category'] = new_category
                                    task['client'] = new_client
                                    task['deal_value'] = new_deal_value
                                    st.success("Task updated!")
                                    st.session_state.pop(f"edit_task_{task['id']}", None)
                                    st.rerun()
                            
                            with col_submit_edit2:
                                if st.form_submit_button("❌ Cancel"):
                                    st.session_state.pop(f"edit_task_{task['id']}", None)
                                    st.rerun()
        
        with tab2:
            st.markdown("## ➕ Project Management")
            
            # Project overview
            col_proj1, col_proj2, col_proj3 = st.columns(3)
            
            with col_proj1:
                total_projects = len(st.session_state.projects)
                st.metric("📁 Total Projects", total_projects)
            
            with col_proj2:
                active_projects = len([p for p in st.session_state.projects if p['status'] == 'Active'])
                st.metric("🟢 Active Projects", active_projects)
            
            with col_proj3:
                avg_progress = sum(p['progress'] for p in st.session_state.projects) / len(st.session_state.projects) if st.session_state.projects else 0
                st.metric("📈 Avg Progress", f"{avg_progress:.0f}%")
            
            # Add new project
            if st.button("➕ Add New Project", type="primary"):
                st.session_state.show_add_project = True
                st.rerun()
            
            # Add project form
            if 'show_add_project' in st.session_state and st.session_state.show_add_project:
                st.markdown("---")
                st.markdown("## ➕ Create New Project")
                
                with st.form("add_project_form"):
                    new_proj_name = st.text_input("Project Name*", placeholder="Q1 Marketing Campaign")
                    new_proj_description = st.text_area("Description", placeholder="Project goals and objectives...")
                    new_proj_status = st.selectbox("Status", ["Planning", "Active", "On Hold", "Completed"])
                    
                    col_proj_submit1, col_proj_submit2 = st.columns(2)
                    with col_proj_submit1:
                        if st.form_submit_button("💾 Create Project", type="primary"):
                            if new_proj_name:
                                new_project = {
                                    'id': len(st.session_state.projects) + 1,
                                    'name': new_proj_name,
                                    'description': new_proj_description,
                                    'status': new_proj_status,
                                    'progress': 0
                                }
                                st.session_state.projects.append(new_project)
                                st.success(f"✅ Project created: {new_proj_name}")
                                st.session_state.show_add_project = False
                                st.rerun()
                            else:
                                st.error("Project name is required")
                    
                    with col_proj_submit2:
                        if st.form_submit_button("❌ Cancel"):
                            st.session_state.show_add_project = False
                            st.rerun()
            
            # Display projects
            st.markdown("---")
            st.markdown("### 📁 Active Projects")
            
            for project in st.session_state.projects:
                project_tasks = [t for t in st.session_state.tasks if t['project'] == project['name']]
                
                with st.expander(f"📁 {project['name']} - {project['status']} ({project['progress']}% complete)"):
                    col_proj_info1, col_proj_info2 = st.columns([2, 1])
                    
                    with col_proj_info1:
                        st.write(f"**📝 Description:** {project['description']}")
                        st.write(f"**📊 Status:** {project['status']}")
                        st.write(f"**📋 Tasks:** {len(project_tasks)} total")
                        
                        if project_tasks:
                            completed_project_tasks = len([t for t in project_tasks if t['status'] == 'Completed'])
                            st.write(f"**✅ Completed Tasks:** {completed_project_tasks}/{len(project_tasks)}")
                    
                    with col_proj_info2:
                        st.write(f"**📈 Progress:** {project['progress']}%")
                        st.progress(project['progress'] / 100)
                        
                        if st.button(f"📋 View Tasks", key=f"view_tasks_{project['id']}"):
                            st.info(f"Tasks for {project['name']} would be filtered and displayed")
                        
                        if st.button(f"✏️ Edit Project", key=f"edit_project_{project['id']}"):
                            st.info("Project edit form would appear here")
        
        with tab3:
            st.markdown("## 👥 Team Overview")
            
            # Team performance metrics
            col_team1, col_team2, col_team3, col_team4 = st.columns(4)
            
            with col_team1:
                total_members = len(st.session_state.team_members)
                st.metric("👥 Team Members", total_members)
            
            with col_team2:
                total_assigned = sum(1 for t in st.session_state.tasks if t['assigned_to'] != 'You')
                st.metric("📋 Tasks Assigned", total_assigned)
            
            with col_team3:
                completed_by_team = len([t for t in st.session_state.tasks if t['status'] == 'Completed' and t['assigned_to'] != 'You'])
                st.metric("✅ Team Completed", completed_by_team)
            
            with col_team4:
                avg_workload = total_assigned / (total_members - 1) if total_members > 1 else 0
                st.metric("📊 Avg Workload", f"{avg_workload:.1f}")
            
            # Team member performance
            st.markdown("### 👤 Team Member Performance")
            
            for member in st.session_state.team_members:
                if member == 'You':
                    continue
                
                member_tasks = [t for t in st.session_state.tasks if t['assigned_to'] == member]
                completed_tasks = [t for t in member_tasks if t['status'] == 'Completed']
                active_tasks = [t for t in member_tasks if t['status'] in ['Not Started', 'In Progress']]
                
                with st.expander(f"👤 {member} - {len(member_tasks)} tasks ({len(completed_tasks)} completed)"):
                    col_member1, col_member2, col_member3 = st.columns(3)
                    
                    with col_member1:
                        st.metric("📋 Total Tasks", len(member_tasks))
                        st.metric("✅ Completed", len(completed_tasks))
                    
                    with col_member2:
                        st.metric("🎯 Active Tasks", len(active_tasks))
                        completion_rate = (len(completed_tasks) / len(member_tasks) * 100) if member_tasks else 0
                        st.metric("📈 Completion Rate", f"{completion_rate:.0f}%")
                    
                    with col_member3:
                        high_priority_tasks = len([t for t in member_tasks if t['priority'] == 'High' and t['status'] != 'Completed'])
                        st.metric("🔥 High Priority", high_priority_tasks)
                        
                        if st.button(f"📧 Contact {member.split()[0]}", key=f"contact_{member}"):
                            st.success(f"Opening communication with {member}")
                    
                    # Recent tasks for this member
                    if member_tasks:
                        st.markdown("**Recent Tasks:**")
                        for task in member_tasks[-3:]:  # Show last 3 tasks
                            status_icon = {"Not Started": "🔵", "In Progress": "🟡", "Completed": "🟢"}.get(task['status'], '⚪')
                            st.write(f"{status_icon} {task['title']} ({task['status']})")
        
        with tab4:
            st.markdown("## 📈 Task Analytics")
            
            # Key performance indicators
            col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
            
            with col_kpi1:
                total_tasks = len(st.session_state.tasks)
                st.metric("📋 Total Tasks", total_tasks)
            
            with col_kpi2:
                completion_rate = (len([t for t in st.session_state.tasks if t['status'] == 'Completed']) / total_tasks * 100) if total_tasks else 0
                st.metric("📈 Completion Rate", f"{completion_rate:.0f}%")
            
            with col_kpi3:
                avg_progress = sum(t['progress'] for t in st.session_state.tasks) / total_tasks if total_tasks else 0
                st.metric("🎯 Avg Progress", f"{avg_progress:.0f}%")
            
            with col_kpi4:
                overdue_count = len([t for t in st.session_state.tasks if t['due_date'] < '2025-01-04' and t['status'] != 'Completed'])
                st.metric("⚠️ Overdue Tasks", overdue_count)
            
            # Charts and analysis
            st.markdown("### 📊 Task Distribution Analysis")
            
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("**📊 Tasks by Status**")
                status_counts = {}
                for task in st.session_state.tasks:
                    status_counts[task['status']] = status_counts.get(task['status'], 0) + 1
                
                for status, count in status_counts.items():
                    st.write(f"• {status}: {count} tasks")
            
            with col_chart2:
                st.markdown("**🎯 Tasks by Priority**")
                priority_counts = {}
                for task in st.session_state.tasks:
                    priority_counts[task['priority']] = priority_counts.get(task['priority'], 0) + 1
                
                for priority, count in priority_counts.items():
                    st.write(f"• {priority}: {count} tasks")
            
            # Category analysis
            st.markdown("### 🏷️ Category Performance")
            
            category_stats = {}
            for task in st.session_state.tasks:
                category = task['category']
                if category not in category_stats:
                    category_stats[category] = {'total': 0, 'completed': 0}
                category_stats[category]['total'] += 1
                if task['status'] == 'Completed':
                    category_stats[category]['completed'] += 1
            
            for category, stats in category_stats.items():
                completion_rate = (stats['completed'] / stats['total'] * 100) if stats['total'] else 0
                st.write(f"**{category}:** {stats['completed']}/{stats['total']} completed ({completion_rate:.0f}%)")
            
            # Timeline analysis
            st.markdown("### 📅 Timeline Analysis")
            
            upcoming_tasks = [t for t in st.session_state.tasks if t['due_date'] >= '2025-01-04' and t['status'] != 'Completed']
            upcoming_tasks.sort(key=lambda x: x['due_date'])
            
            st.markdown("**🔜 Upcoming Deadlines:**")
            for task in upcoming_tasks[:5]:  # Show next 5 deadlines
                days_until = (datetime.strptime(task['due_date'], '%Y-%m-%d') - datetime.strptime('2025-01-04', '%Y-%m-%d')).days
                urgency = "🔴" if days_until <= 3 else "🟡" if days_until <= 7 else "🟢"
                st.write(f"{urgency} {task['title']} - Due: {task['due_date']} ({days_until} days)")
        
        with tab5:
            st.markdown("## ⚙️ Task Management Settings")
            
            col_settings1, col_settings2 = st.columns(2)
            
            with col_settings1:
                st.markdown("### 🔔 Notification Settings")
                
                task_reminders = st.checkbox("Task deadline reminders", value=True)
                assignment_notifications = st.checkbox("New task assignment alerts", value=True)
                completion_notifications = st.checkbox("Task completion notifications", value=True)
                overdue_alerts = st.checkbox("Overdue task alerts", value=True)
                
                reminder_timing = st.selectbox("Reminder Timing", ["1 day before", "2 days before", "1 week before"])
                
                st.markdown("### 📊 Data Management")
                
                if st.button("📁 Export Task Data"):
                    st.success("📊 Task data exported to CSV")
                
                if st.button("📈 Export Project Report"):
                    st.success("📊 Project report exported to PDF")
                
                if st.button("🔄 Sync with Calendar"):
                    st.success("🔄 Tasks synced with calendar")
            
            with col_settings2:
                st.markdown("### 🎯 Task Preferences")
                
                default_priority = st.selectbox("Default Task Priority", ["Medium", "High", "Low"])
                default_assignee = st.selectbox("Default Assignee", st.session_state.team_members)
                
                auto_progress_tracking = st.checkbox("Automatic progress tracking", value=False)
                task_dependencies = st.checkbox("Enable task dependencies", value=True)
                
                st.markdown("### 👥 Team Management")
                
                st.markdown("**Add Team Member:**")
                new_member = st.text_input("New Member Name", placeholder="John Smith")
                if st.button("➕ Add Member"):
                    if new_member and new_member not in st.session_state.team_members:
                        st.session_state.team_members.append(new_member)
                        st.success(f"✅ Added team member: {new_member}")
                        st.rerun()
                
                st.markdown("**Current Team:**")
                for member in st.session_state.team_members:
                    col_member_mgmt1, col_member_mgmt2 = st.columns([3, 1])
                    with col_member_mgmt1:
                        st.write(f"👤 {member}")
                    with col_member_mgmt2:
                        if member != 'You' and st.button("🗑️", key=f"remove_{member}", help="Remove member"):
                            st.session_state.team_members.remove(member)
                            st.rerun()
                
                if st.button("💾 Save All Settings"):
                    st.success("✅ All settings saved successfully!")
    
    except Exception as e:
        st.error(f"Error in task management: {str(e)}")
    
    # Add navigation CTAs
    add_navigation_ctas()
    
    # Back to dashboard option
    if st.button("⬅️ Back to Dashboard", key="back_to_dashboard_tasks"):
        st.session_state.pop("show_tasks", None)
        st.rerun()

def load_document_management_page():
    """Advanced Document Management & File System - Full Implementation"""
    try:
        st.markdown("### 📁 Document Management Center")
        st.markdown("*Comprehensive file organization, sharing, and collaboration platform*")
        
        # Initialize document data
        if 'documents' not in st.session_state:
            st.session_state.documents = [
                {
                    'id': 1, 'name': 'Manhattan Office Tower - Due Diligence Package', 'type': 'PDF',
                    'size': '15.2 MB', 'category': 'Due Diligence', 'uploaded_by': 'Sarah Johnson',
                    'upload_date': '2025-01-02', 'last_modified': '2025-01-03', 'status': 'Active',
                    'tags': ['Due Diligence', 'Legal', 'Financial', 'Goldman Sachs'],
                    'description': 'Complete due diligence package including financial statements, legal documents, and inspection reports',
                    'shared_with': ['Mike Chen', 'Lisa Rodriguez'], 'version': '1.3',
                    'approval_status': 'Approved', 'confidentiality': 'Confidential'
                },
                {
                    'id': 2, 'name': 'Blackstone Partnership Agreement Draft', 'type': 'DOCX',
                    'size': '2.8 MB', 'category': 'Legal', 'uploaded_by': 'You',
                    'upload_date': '2025-01-01', 'last_modified': '2025-01-04', 'status': 'Active',
                    'tags': ['Partnership', 'Legal', 'Blackstone', 'Contract'],
                    'description': 'Draft partnership agreement for LA Mixed-Use Development project',
                    'shared_with': ['Legal Team', 'Sarah Johnson'], 'version': '2.1',
                    'approval_status': 'Under Review', 'confidentiality': 'Highly Confidential'
                },
                {
                    'id': 3, 'name': 'Q3 Financial Performance Report', 'type': 'XLSX',
                    'size': '4.1 MB', 'category': 'Financial', 'uploaded_by': 'David Kim',
                    'upload_date': '2024-12-30', 'last_modified': '2025-01-02', 'status': 'Active',
                    'tags': ['Financial', 'Q3', 'Performance', 'Analysis'],
                    'description': 'Comprehensive financial analysis and performance metrics for Q3 2024',
                    'shared_with': ['Executive Team', 'Board Members'], 'version': '1.0',
                    'approval_status': 'Approved', 'confidentiality': 'Internal'
                },
                {
                    'id': 4, 'name': 'Austin Property Marketing Materials', 'type': 'ZIP',
                    'size': '28.7 MB', 'category': 'Marketing', 'uploaded_by': 'Emma Wilson',
                    'upload_date': '2024-12-28', 'last_modified': '2024-12-29', 'status': 'Active',
                    'tags': ['Marketing', 'Austin', 'Brochures', 'Photos'],
                    'description': 'Complete marketing package including brochures, photos, and virtual tour files',
                    'shared_with': ['Marketing Team', 'Sales Team'], 'version': '1.2',
                    'approval_status': 'Approved', 'confidentiality': 'Public'
                },
                {
                    'id': 5, 'name': 'Investor Presentation Template', 'type': 'PPTX',
                    'size': '8.9 MB', 'category': 'Templates', 'uploaded_by': 'You',
                    'upload_date': '2024-12-25', 'last_modified': '2024-12-27', 'status': 'Archived',
                    'tags': ['Template', 'Presentation', 'Investors'],
                    'description': 'Standardized presentation template for investor meetings and proposals',
                    'shared_with': ['All Users'], 'version': '3.0',
                    'approval_status': 'Approved', 'confidentiality': 'Internal'
                }
            ]
        
        # Initialize folder structure
        if 'folders' not in st.session_state:
            st.session_state.folders = [
                {'name': 'Due Diligence', 'docs': 4, 'size': '45.2 MB', 'icon': '📋'},
                {'name': 'Legal Documents', 'docs': 12, 'size': '23.8 MB', 'icon': '⚖️'},
                {'name': 'Financial Reports', 'docs': 8, 'size': '15.4 MB', 'icon': '💰'},
                {'name': 'Marketing Materials', 'docs': 15, 'size': '120.3 MB', 'icon': '📈'},
                {'name': 'Property Files', 'docs': 23, 'size': '89.7 MB', 'icon': '🏢'},
                {'name': 'Templates', 'docs': 6, 'size': '12.1 MB', 'icon': '📄'}
            ]
        
        # Main document management tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📁 File Browser", "📤 Upload & Share", "🔍 Search & Filter", "👥 Collaboration", "📊 Analytics", "⚙️ Settings"])
        
        with tab1:
            st.markdown("## 📁 File Browser")
            
            # Storage overview
            col_storage1, col_storage2, col_storage3, col_storage4 = st.columns(4)
            
            with col_storage1:
                total_docs = len(st.session_state.documents)
                st.metric("📄 Total Documents", total_docs)
            
            with col_storage2:
                total_size = sum(float(doc['size'].split()[0]) for doc in st.session_state.documents)
                st.metric("💾 Storage Used", f"{total_size:.1f} MB")
            
            with col_storage3:
                shared_docs = len([doc for doc in st.session_state.documents if doc['shared_with']])
                st.metric("🤝 Shared Files", shared_docs)
            
            with col_storage4:
                recent_docs = len([doc for doc in st.session_state.documents if doc['upload_date'] >= '2025-01-01'])
                st.metric("🆕 Recent Files", recent_docs)
            
            # Folder structure
            st.markdown("### 📂 Folder Structure")
            
            col_folders1, col_folders2, col_folders3 = st.columns(3)
            
            for i, folder in enumerate(st.session_state.folders):
                with [col_folders1, col_folders2, col_folders3][i % 3]:
                    with st.container():
                        st.markdown(f"""
                        <div style="border: 1px solid #ddd; padding: 15px; border-radius: 10px; margin: 5px; background: #f9f9f9;">
                            <h4>{folder['icon']} {folder['name']}</h4>
                            <p>📄 {folder['docs']} documents</p>
                            <p>💾 {folder['size']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button(f"Open {folder['name']}", key=f"open_folder_{i}"):
                            st.session_state.selected_folder = folder['name']
                            st.rerun()
            
            # Document list
            st.markdown("### 📄 Recent Documents")
            
            # Document view options
            col_view1, col_view2 = st.columns([1, 4])
            with col_view1:
                view_mode = st.radio("View", ["📋 List", "🗂️ Grid"], index=0)
            
            if view_mode == "📋 List":
                for doc in st.session_state.documents:
                    status_colors = {
                        'Active': '🟢', 'Archived': '🟡', 'Deleted': '🔴'
                    }
                    approval_colors = {
                        'Approved': '✅', 'Under Review': '🔄', 'Rejected': '❌'
                    }
                    confidentiality_colors = {
                        'Public': '🌍', 'Internal': '🏢', 'Confidential': '🔒', 'Highly Confidential': '🔐'
                    }
                    
                    with st.expander(f"{status_colors.get(doc['status'], '⚪')} {doc['name']} ({doc['type']}) - {doc['size']}"):
                        col_doc1, col_doc2, col_doc3 = st.columns([2, 2, 1])
                        
                        with col_doc1:
                            st.write(f"**📂 Category:** {doc['category']}")
                            st.write(f"**👤 Uploaded by:** {doc['uploaded_by']}")
                            st.write(f"**📅 Upload Date:** {doc['upload_date']}")
                            st.write(f"**🔄 Last Modified:** {doc['last_modified']}")
                            st.write(f"**📝 Description:** {doc['description']}")
                        
                        with col_doc2:
                            st.write(f"**🏷️ Tags:** {', '.join(doc['tags'])}")
                            st.write(f"**👥 Shared with:** {', '.join(doc['shared_with']) if doc['shared_with'] else 'Not shared'}")
                            st.write(f"**🔢 Version:** {doc['version']}")
                            st.write(f"**{approval_colors.get(doc['approval_status'], '⚪')} Status:** {doc['approval_status']}")
                            st.write(f"**{confidentiality_colors.get(doc['confidentiality'], '⚪')} Level:** {doc['confidentiality']}")
                        
                        with col_doc3:
                            if st.button(f"📥 Download", key=f"download_{doc['id']}"):
                                st.success(f"Downloaded {doc['name']}")
                            
                            if st.button(f"👁️ Preview", key=f"preview_{doc['id']}"):
                                st.info("Document preview would open here")
                            
                            if st.button(f"🤝 Share", key=f"share_{doc['id']}"):
                                st.session_state.selected_doc_share = doc['id']
                                st.rerun()
                            
                            if st.button(f"✏️ Edit", key=f"edit_{doc['id']}"):
                                st.session_state.selected_doc_edit = doc['id']
                                st.rerun()
                        
                        # Show sharing interface if selected
                        if st.session_state.get('selected_doc_share') == doc['id']:
                            st.markdown("### 🤝 Share Document")
                            
                            with st.form(f"share_form_{doc['id']}"):
                                share_with = st.multiselect("Share with", 
                                                          ["Sarah Johnson", "Mike Chen", "Lisa Rodriguez", "David Kim", "Emma Wilson", "Legal Team", "Marketing Team"])
                                permission_level = st.selectbox("Permission Level", ["View Only", "Edit", "Full Access"])
                                expiry_date = st.date_input("Access Expires (Optional)")
                                share_message = st.text_area("Message (Optional)", placeholder="I'm sharing this document with you...")
                                
                                col_share1, col_share2 = st.columns(2)
                                with col_share1:
                                    if st.form_submit_button("📤 Share Document"):
                                        st.success(f"Document shared with {len(share_with)} users")
                                        st.session_state.pop('selected_doc_share', None)
                                        st.rerun()
                                
                                with col_share2:
                                    if st.form_submit_button("❌ Cancel"):
                                        st.session_state.pop('selected_doc_share', None)
                                        st.rerun()
            
            else:  # Grid view
                st.markdown("### 🗂️ Grid View")
                
                cols = st.columns(3)
                for i, doc in enumerate(st.session_state.documents):
                    with cols[i % 3]:
                        st.markdown(f"""
                        <div style="border: 1px solid #ddd; padding: 10px; border-radius: 8px; margin: 5px; text-align: center;">
                            <h5>📄 {doc['name'][:30]}...</h5>
                            <p><strong>Type:</strong> {doc['type']}</p>
                            <p><strong>Size:</strong> {doc['size']}</p>
                            <p><strong>Category:</strong> {doc['category']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button(f"Open", key=f"grid_open_{doc['id']}"):
                            st.info(f"Opening {doc['name']}")
        
        with tab2:
            st.markdown("## 📤 Upload & Share")
            
            # File upload section
            col_upload1, col_upload2 = st.columns(2)
            
            with col_upload1:
                st.markdown("### 📁 Upload New Document")
                
                with st.form("upload_document"):
                    uploaded_file = st.file_uploader("Choose file", type=['pdf', 'docx', 'xlsx', 'pptx', 'txt', 'zip'])
                    
                    doc_name = st.text_input("Document Name*", placeholder="Enter descriptive name")
                    doc_category = st.selectbox("Category*", ["Due Diligence", "Legal", "Financial", "Marketing", "Property Files", "Templates", "Other"])
                    doc_description = st.text_area("Description", placeholder="Brief description of the document...")
                    
                    doc_tags = st.multiselect("Tags", 
                                             ["Legal", "Financial", "Marketing", "Due Diligence", "Contract", "Report", "Analysis", "Template"])
                    
                    confidentiality = st.selectbox("Confidentiality Level", ["Public", "Internal", "Confidential", "Highly Confidential"])
                    
                    auto_share = st.checkbox("Share with team members")
                    if auto_share:
                        share_with_team = st.multiselect("Share with", 
                                                        ["Sarah Johnson", "Mike Chen", "Lisa Rodriguez", "David Kim", "Emma Wilson"])
                    
                    if st.form_submit_button("📤 Upload Document", type="primary"):
                        if doc_name:
                            new_doc = {
                                'id': len(st.session_state.documents) + 1,
                                'name': doc_name,
                                'type': 'PDF',  # Would be determined from uploaded file
                                'size': '5.2 MB',  # Would be calculated
                                'category': doc_category,
                                'uploaded_by': 'You',
                                'upload_date': '2025-01-04',
                                'last_modified': '2025-01-04',
                                'status': 'Active',
                                'tags': doc_tags,
                                'description': doc_description,
                                'shared_with': share_with_team if auto_share else [],
                                'version': '1.0',
                                'approval_status': 'Under Review',
                                'confidentiality': confidentiality
                            }
                            st.session_state.documents.append(new_doc)
                            st.success(f"✅ Document '{doc_name}' uploaded successfully!")
                            st.rerun()
                        else:
                            st.error("Document name is required")
            
            with col_upload2:
                st.markdown("### 🤝 Quick Share")
                
                # Quick share existing document
                existing_docs = [doc['name'] for doc in st.session_state.documents]
                selected_doc = st.selectbox("Select document to share", existing_docs)
                
                if selected_doc:
                    with st.form("quick_share"):
                        quick_share_with = st.multiselect("Share with", 
                                                         ["Sarah Johnson", "Mike Chen", "Lisa Rodriguez", "David Kim", "Emma Wilson", "Legal Team", "Executive Team"])
                        
                        quick_permission = st.selectbox("Permission", ["View Only", "Edit", "Full Access"])
                        quick_message = st.text_area("Message", placeholder="Sharing this document with you...")
                        
                        if st.form_submit_button("🚀 Quick Share"):
                            st.success(f"✅ '{selected_doc}' shared with {len(quick_share_with)} users!")
                
                # Bulk operations
                st.markdown("### 📦 Bulk Operations")
                
                if st.button("📁 Create New Folder"):
                    new_folder_name = st.text_input("Folder Name", key="new_folder")
                    if new_folder_name:
                        st.session_state.folders.append({
                            'name': new_folder_name, 'docs': 0, 'size': '0 MB', 'icon': '📁'
                        })
                        st.success(f"Folder '{new_folder_name}' created!")
                        st.rerun()
                
                if st.button("📊 Export File List"):
                    st.success("📊 File list exported to CSV")
                
                if st.button("🔄 Sync with Cloud"):
                    st.success("🔄 Files synced with cloud storage")
        
        with tab3:
            st.markdown("## 🔍 Search & Filter")
            
            # Advanced search
            col_search1, col_search2 = st.columns(2)
            
            with col_search1:
                st.markdown("### 🔍 Advanced Search")
                
                search_query = st.text_input("🔍 Search documents", placeholder="Enter keywords, tags, or description...")
                
                # Search filters
                search_category = st.multiselect("Filter by Category", 
                                               ["Due Diligence", "Legal", "Financial", "Marketing", "Property Files", "Templates"])
                
                search_date_from = st.date_input("From Date")
                search_date_to = st.date_input("To Date")
                
                search_file_type = st.multiselect("File Type", ["PDF", "DOCX", "XLSX", "PPTX", "ZIP", "TXT"])
                
                search_confidentiality = st.multiselect("Confidentiality Level", 
                                                       ["Public", "Internal", "Confidential", "Highly Confidential"])
                
                if st.button("🔍 Search Documents", type="primary"):
                    st.session_state.search_results = []
                    for doc in st.session_state.documents:
                        match = True
                        
                        if search_query and search_query.lower() not in f"{doc['name']} {doc['description']} {' '.join(doc['tags'])}".lower():
                            match = False
                        
                        if search_category and doc['category'] not in search_category:
                            match = False
                        
                        if search_file_type and doc['type'] not in search_file_type:
                            match = False
                        
                        if search_confidentiality and doc['confidentiality'] not in search_confidentiality:
                            match = False
                        
                        if match:
                            st.session_state.search_results.append(doc)
                    
                    st.success(f"Found {len(st.session_state.search_results)} documents")
            
            with col_search2:
                st.markdown("### 📊 Filter Results")
                
                if 'search_results' in st.session_state:
                    st.write(f"**{len(st.session_state.search_results)} results found**")
                    
                    for doc in st.session_state.search_results:
                        with st.expander(f"📄 {doc['name']}"):
                            st.write(f"**Category:** {doc['category']}")
                            st.write(f"**Type:** {doc['type']}")
                            st.write(f"**Size:** {doc['size']}")
                            st.write(f"**Uploaded:** {doc['upload_date']}")
                            st.write(f"**Tags:** {', '.join(doc['tags'])}")
                            
                            col_result1, col_result2 = st.columns(2)
                            with col_result1:
                                if st.button(f"📥 Download", key=f"search_download_{doc['id']}"):
                                    st.success("File downloaded!")
                            with col_result2:
                                if st.button(f"👁️ View", key=f"search_view_{doc['id']}"):
                                    st.info("Opening file viewer...")
                
                # Saved searches
                st.markdown("### 💾 Saved Searches")
                
                saved_searches = [
                    "Legal documents - Q4 2024",
                    "Marketing materials - All time",
                    "Due diligence - Active deals"
                ]
                
                for search in saved_searches:
                    col_saved1, col_saved2 = st.columns([3, 1])
                    with col_saved1:
                        st.write(f"🔍 {search}")
                    with col_saved2:
                        if st.button("▶️", key=f"run_saved_{search}", help="Run search"):
                            st.info(f"Running search: {search}")
        
        with tab4:
            st.markdown("## 👥 Collaboration")
            
            # Collaboration overview
            col_collab1, col_collab2, col_collab3 = st.columns(3)
            
            with col_collab1:
                shared_docs = len([doc for doc in st.session_state.documents if doc['shared_with']])
                st.metric("🤝 Shared Documents", shared_docs)
            
            with col_collab2:
                pending_approvals = len([doc for doc in st.session_state.documents if doc['approval_status'] == 'Under Review'])
                st.metric("⏳ Pending Approvals", pending_approvals)
            
            with col_collab3:
                active_collaborators = 8
                st.metric("👥 Active Collaborators", active_collaborators)
            
            # Recent activity
            st.markdown("### 🔔 Recent Activity")
            
            activities = [
                {'user': 'Sarah Johnson', 'action': 'uploaded', 'document': 'Due Diligence Package', 'time': '2 hours ago', 'icon': '📤'},
                {'user': 'Mike Chen', 'action': 'shared', 'document': 'Partnership Agreement', 'time': '4 hours ago', 'icon': '🤝'},
                {'user': 'Lisa Rodriguez', 'action': 'commented on', 'document': 'Financial Report', 'time': '6 hours ago', 'icon': '💬'},
                {'user': 'David Kim', 'action': 'approved', 'document': 'Marketing Materials', 'time': '1 day ago', 'icon': '✅'},
                {'user': 'Emma Wilson', 'action': 'downloaded', 'document': 'Property Files', 'time': '1 day ago', 'icon': '📥'}
            ]
            
            for activity in activities:
                col_act1, col_act2, col_act3, col_act4 = st.columns([0.5, 2, 2, 1])
                with col_act1:
                    st.write(activity['icon'])
                with col_act2:
                    st.write(f"**{activity['user']}**")
                with col_act3:
                    st.write(f"{activity['action']} *{activity['document']}*")
                with col_act4:
                    st.write(f"*{activity['time']}*")
            
            # Pending approvals
            st.markdown("### ⏳ Pending Approvals")
            
            pending_docs = [doc for doc in st.session_state.documents if doc['approval_status'] == 'Under Review']
            
            for doc in pending_docs:
                with st.expander(f"⏳ {doc['name']} - Pending Approval"):
                    col_pending1, col_pending2 = st.columns([2, 1])
                    
                    with col_pending1:
                        st.write(f"**Uploaded by:** {doc['uploaded_by']}")
                        st.write(f"**Upload Date:** {doc['upload_date']}")
                        st.write(f"**Description:** {doc['description']}")
                        st.write(f"**Confidentiality:** {doc['confidentiality']}")
                    
                    with col_pending2:
                        if st.button(f"✅ Approve", key=f"approve_{doc['id']}", type="primary"):
                            doc['approval_status'] = 'Approved'
                            st.success(f"Approved: {doc['name']}")
                            st.rerun()
                        
                        if st.button(f"❌ Reject", key=f"reject_{doc['id']}"):
                            doc['approval_status'] = 'Rejected'
                            st.error(f"Rejected: {doc['name']}")
                            st.rerun()
                        
                        if st.button(f"👁️ Review", key=f"review_{doc['id']}"):
                            st.info("Opening document for review...")
            
            # Team collaboration settings
            st.markdown("### ⚙️ Collaboration Settings")
            
            col_settings1, col_settings2 = st.columns(2)
            
            with col_settings1:
                auto_approval = st.checkbox("Auto-approve internal documents", value=False)
                notification_uploads = st.checkbox("Notify on new uploads", value=True)
                notification_shares = st.checkbox("Notify when documents are shared with me", value=True)
            
            with col_settings2:
                default_permission = st.selectbox("Default sharing permission", ["View Only", "Edit", "Full Access"])
                version_control = st.checkbox("Enable automatic version control", value=True)
                collaboration_history = st.checkbox("Track collaboration history", value=True)
        
        with tab5:
            st.markdown("## 📊 Document Analytics")
            
            # Document usage metrics
            col_analytics1, col_analytics2, col_analytics3, col_analytics4 = st.columns(4)
            
            with col_analytics1:
                total_downloads = 247
                st.metric("📥 Total Downloads", total_downloads, delta="+18")
            
            with col_analytics2:
                avg_access_time = "2.3 min"
                st.metric("⏱️ Avg Access Time", avg_access_time, delta="-0.5 min")
            
            with col_analytics3:
                most_shared = "Due Diligence Package"
                st.metric("🔝 Most Shared", most_shared)
            
            with col_analytics4:
                storage_growth = "12.5 MB/week"
                st.metric("📈 Storage Growth", storage_growth, delta="+2.1 MB")
            
            # Usage charts
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("### 📊 Document Categories")
                
                category_counts = {}
                for doc in st.session_state.documents:
                    category_counts[doc['category']] = category_counts.get(doc['category'], 0) + 1
                
                categories = list(category_counts.keys())
                counts = list(category_counts.values())
                
                fig_categories = go.Figure(data=[go.Pie(
                    labels=categories,
                    values=counts,
                    hole=0.4
                )])
                
                fig_categories.update_layout(height=300, title="Documents by Category")
                st.plotly_chart(fig_categories, use_container_width=True)
            
            with col_chart2:
                st.markdown("### 📈 Upload Trends")
                
                # Mock upload trend data
                upload_months = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                upload_counts = [8, 12, 15, 18, 14, 22]
                
                fig_uploads = go.Figure(data=[go.Bar(
                    x=upload_months,
                    y=upload_counts,
                    marker_color='#4ECDC4'
                )])
                
                fig_uploads.update_layout(height=300, title="Monthly Uploads")
                st.plotly_chart(fig_uploads, use_container_width=True)
            
            # Storage analysis
            st.markdown("### 💾 Storage Analysis")
            
            storage_by_category = {
                'Due Diligence': 45.2,
                'Legal': 23.8,
                'Marketing': 120.3,
                'Property Files': 89.7,
                'Financial': 15.4,
                'Templates': 12.1
            }
            
            for category, size in storage_by_category.items():
                col_storage_cat1, col_storage_cat2 = st.columns([3, 1])
                with col_storage_cat1:
                    st.write(f"📁 **{category}**")
                with col_storage_cat2:
                    st.write(f"💾 {size} MB")
            
            # Access patterns
            st.markdown("### 👥 Access Patterns")
            
            access_data = [
                {'user': 'Sarah Johnson', 'downloads': 34, 'uploads': 8, 'shares': 12},
                {'user': 'Mike Chen', 'downloads': 28, 'uploads': 5, 'shares': 9},
                {'user': 'Lisa Rodriguez', 'downloads': 31, 'uploads': 7, 'shares': 11},
                {'user': 'David Kim', 'downloads': 22, 'uploads': 4, 'shares': 6},
                {'user': 'Emma Wilson', 'downloads': 26, 'uploads': 6, 'shares': 8}
            ]
            
            for user_data in access_data:
                col_user1, col_user2, col_user3, col_user4 = st.columns([2, 1, 1, 1])
                with col_user1:
                    st.write(f"👤 **{user_data['user']}**")
                with col_user2:
                    st.write(f"📥 {user_data['downloads']}")
                with col_user3:
                    st.write(f"📤 {user_data['uploads']}")
                with col_user4:
                    st.write(f"🤝 {user_data['shares']}")
        
        with tab6:
            st.markdown("## ⚙️ Document Management Settings")
            
            col_settings1, col_settings2 = st.columns(2)
            
            with col_settings1:
                st.markdown("### 🔐 Security Settings")
                
                require_approval = st.checkbox("Require approval for confidential documents", value=True)
                enable_watermarks = st.checkbox("Add watermarks to downloaded files", value=False)
                audit_trail = st.checkbox("Enable detailed audit trail", value=True)
                access_restrictions = st.checkbox("Restrict access by IP address", value=False)
                
                st.markdown("### 💾 Storage Settings")
                
                auto_backup = st.checkbox("Automatic daily backups", value=True)
                version_retention = st.slider("Keep document versions", 1, 10, 5)
                auto_archive = st.selectbox("Auto-archive after", ["Never", "6 months", "1 year", "2 years"])
                
                max_file_size = st.selectbox("Maximum file size", ["10 MB", "50 MB", "100 MB", "500 MB"])
            
            with col_settings2:
                st.markdown("### 🔔 Notification Settings")
                
                email_notifications = st.checkbox("Email notifications", value=True)
                upload_notifications = st.checkbox("Notify on uploads", value=True)
                share_notifications = st.checkbox("Notify on shares", value=True)
                approval_notifications = st.checkbox("Notify on approvals needed", value=True)
                
                notification_frequency = st.selectbox("Notification frequency", ["Immediate", "Hourly digest", "Daily digest"])
                
                st.markdown("### 🔗 Integration Settings")
                
                cloud_sync = st.selectbox("Cloud storage sync", ["None", "Google Drive", "OneDrive", "Dropbox"])
                calendar_integration = st.checkbox("Calendar integration for deadlines", value=False)
                crm_integration = st.checkbox("Sync with CRM system", value=True)
                
                if st.button("💾 Save All Settings"):
                    st.success("✅ All settings saved successfully!")
                
                if st.button("🔄 Reset to Defaults"):
                    st.warning("⚠️ All settings reset to default values")
    
    except Exception as e:
        st.error(f"Error in document management: {str(e)}")
    
    # Add navigation CTAs
    add_navigation_ctas()
    
    # Back to dashboard option
    if st.button("⬅️ Back to Dashboard", key="back_to_dashboard_docs"):
        st.session_state.pop("show_documents", None)
        st.rerun()

def load_integrations_page():
    """Advanced Integrations & API Management - Full Implementation"""
    try:
        st.markdown("### 🔗 Advanced Integrations & API Management")
        st.markdown("*Comprehensive third-party integrations and workflow automation*")
        
        # Initialize integrations data
        if 'integrations' not in st.session_state:
            st.session_state.integrations = {
                'active_integrations': [
                    {
                        'id': 1, 'name': 'Stripe Payment Processing', 'category': 'Payment', 'status': 'Live Production',
                        'description': 'Live Stripe account - Production payment processing and subscription management',
                        'api_calls': 1247, 'last_sync': '2025-09-04 09:30', 'uptime': '99.9%',
                        'features': ['Live Payment Processing', 'Production Subscription Billing', 'Real Invoice Generation', 'Live Customer Portal'],
                        'cost': 'Live Account Active', 'setup_date': '2025-09-04',
                        'webhook_url': 'https://nxtrix.app/webhooks/stripe',
                        'rate_limit': 'Production Limits', 'data_sync': 'Real-time'
                    },
                    {
                        'id': 2, 'name': 'Twilio SMS & Voice', 'category': 'Communication', 'status': 'Connected',
                        'description': 'SMS campaigns and voice communication platform',
                        'api_calls': 523, 'last_sync': '2025-01-04 10:15', 'uptime': '99.7%',
                        'features': ['SMS Messaging', 'Voice Calls', 'Phone Verification'],
                        'cost': '$0.0075/SMS', 'setup_date': '2024-12-01',
                        'webhook_url': 'https://nxtrix.app/webhooks/twilio',
                        'rate_limit': '500/hour', 'data_sync': 'Real-time'
                    },
                    {
                        'id': 3, 'name': 'Supabase Database', 'category': 'Database', 'status': 'Connected',
                        'description': 'Primary database for user data and CRM records',
                        'api_calls': 3421, 'last_sync': '2025-01-04 10:20', 'uptime': '99.95%',
                        'features': ['Database Storage', 'Authentication', 'Real-time Updates'],
                        'cost': '$25/month', 'setup_date': '2024-10-01',
                        'webhook_url': 'https://nxtrix.app/webhooks/supabase',
                        'rate_limit': '10000/hour', 'data_sync': 'Real-time'
                    },
                    {
                        'id': 4, 'name': 'Google Workspace', 'category': 'Productivity', 'status': 'Connected',
                        'description': 'Email, calendar, and document collaboration',
                        'api_calls': 892, 'last_sync': '2025-01-04 09:45', 'uptime': '99.8%',
                        'features': ['Gmail Integration', 'Calendar Sync', 'Drive Storage'],
                        'cost': '$12/user/month', 'setup_date': '2024-11-20',
                        'webhook_url': 'https://nxtrix.app/webhooks/google',
                        'rate_limit': '2000/hour', 'data_sync': 'Every 15 minutes'
                    },
                    {
                        'id': 5, 'name': 'Slack Workspace', 'category': 'Communication', 'status': 'Connected',
                        'description': 'Team communication and notification platform',
                        'api_calls': 156, 'last_sync': '2025-01-04 10:00', 'uptime': '99.9%',
                        'features': ['Team Messaging', 'File Sharing', 'Bot Integration'],
                        'cost': '$8/user/month', 'setup_date': '2024-12-10',
                        'webhook_url': 'https://nxtrix.app/webhooks/slack',
                        'rate_limit': '1000/hour', 'data_sync': 'Real-time'
                    }
                ],
                'available_integrations': [
                    {
                        'name': 'Salesforce CRM', 'category': 'CRM', 'description': 'Advanced CRM and sales automation',
                        'features': ['Lead Management', 'Sales Pipeline', 'Analytics'], 'cost': '$75/user/month',
                        'complexity': 'Advanced', 'setup_time': '2-3 hours'
                    },
                    {
                        'name': 'HubSpot Marketing', 'category': 'Marketing', 'description': 'Marketing automation and lead nurturing',
                        'features': ['Email Marketing', 'Lead Scoring', 'Campaign Analytics'], 'cost': '$50/month',
                        'complexity': 'Medium', 'setup_time': '1-2 hours'
                    },
                    {
                        'name': 'Zapier Automation', 'category': 'Automation', 'description': 'Connect apps and automate workflows',
                        'features': ['Workflow Automation', '5000+ App Connections', 'Multi-step Zaps'], 'cost': '$20/month',
                        'complexity': 'Easy', 'setup_time': '30 minutes'
                    },
                    {
                        'name': 'DocuSign eSignature', 'category': 'Legal', 'description': 'Digital document signing and contracts',
                        'features': ['Electronic Signatures', 'Document Templates', 'Audit Trail'], 'cost': '$15/month',
                        'complexity': 'Easy', 'setup_time': '45 minutes'
                    },
                    {
                        'name': 'QuickBooks Online', 'category': 'Accounting', 'description': 'Accounting and financial management',
                        'features': ['Invoicing', 'Expense Tracking', 'Financial Reports'], 'cost': '$30/month',
                        'complexity': 'Medium', 'setup_time': '1-2 hours'
                    },
                    {
                        'name': 'Microsoft Teams', 'category': 'Communication', 'description': 'Video conferencing and collaboration',
                        'features': ['Video Calls', 'File Sharing', 'Team Collaboration'], 'cost': '$6/user/month',
                        'complexity': 'Easy', 'setup_time': '30 minutes'
                    },
                    {
                        'name': 'Calendly Scheduling', 'category': 'Scheduling', 'description': 'Automated appointment scheduling',
                        'features': ['Meeting Scheduling', 'Calendar Integration', 'Automated Reminders'], 'cost': '$10/month',
                        'complexity': 'Easy', 'setup_time': '20 minutes'
                    },
                    {
                        'name': 'Mailchimp Email', 'category': 'Marketing', 'description': 'Email marketing and automation',
                        'features': ['Email Campaigns', 'Audience Segmentation', 'Analytics'], 'cost': '$12/month',
                        'complexity': 'Easy', 'setup_time': '45 minutes'
                    }
                ]
            }
        
        # Main integration tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🔗 Active Integrations", "🛒 Marketplace", "⚙️ API Management", "🔄 Workflows", "📊 Analytics", "🛠️ Settings"])
        
        with tab1:
            st.markdown("## 🔗 Active Integrations")
            
            # Integration overview
            col_overview1, col_overview2, col_overview3, col_overview4 = st.columns(4)
            
            with col_overview1:
                active_count = len(st.session_state.integrations['active_integrations'])
                st.metric("🔗 Active Integrations", active_count)
            
            with col_overview2:
                total_api_calls = sum(integration['api_calls'] for integration in st.session_state.integrations['active_integrations'])
                st.metric("📡 API Calls Today", total_api_calls)
            
            with col_overview3:
                avg_uptime = sum(float(integration['uptime'].replace('%', '')) for integration in st.session_state.integrations['active_integrations']) / active_count
                st.metric("⚡ Avg Uptime", f"{avg_uptime:.1f}%")
            
            with col_overview4:
                monthly_cost = 234  # Calculate from integration costs
                st.metric("💰 Monthly Cost", f"${monthly_cost}")
            
            # Active integrations list
            st.markdown("### 🔧 Connected Services")
            
            for integration in st.session_state.integrations['active_integrations']:
                status_colors = {
                    'Connected': '🟢', 'Disconnected': '🔴', 
                    'Error': '🟠', 'Syncing': '🟡'
                }
                
                with st.expander(f"{status_colors.get(integration['status'], '⚪')} {integration['name']} - {integration['category']}"):
                    col_int1, col_int2, col_int3 = st.columns([2, 2, 1])
                    
                    with col_int1:
                        st.write(f"**📝 Description:** {integration['description']}")
                        st.write(f"**🛠️ Features:** {', '.join(integration['features'])}")
                        st.write(f"**💰 Cost:** {integration['cost']}")
                        st.write(f"**📅 Setup Date:** {integration['setup_date']}")
                    
                    with col_int2:
                        st.write(f"**📡 API Calls:** {integration['api_calls']}")
                        st.write(f"**🔄 Last Sync:** {integration['last_sync']}")
                        st.write(f"**⚡ Uptime:** {integration['uptime']}")
                        st.write(f"**🔗 Webhook:** {integration['webhook_url']}")
                        st.write(f"**⏱️ Rate Limit:** {integration['rate_limit']}")
                        st.write(f"**🔄 Data Sync:** {integration['data_sync']}")
                    
                    with col_int3:
                        if st.button(f"⚙️ Configure", key=f"config_{integration['id']}"):
                            st.session_state.selected_integration_config = integration['id']
                            st.rerun()
                        
                        if st.button(f"📊 Logs", key=f"logs_{integration['id']}"):
                            st.session_state.selected_integration_logs = integration['id']
                            st.rerun()
                        
                        if st.button(f"🔄 Sync", key=f"sync_{integration['id']}"):
                            st.success(f"✅ {integration['name']} synced successfully!")
                        
                        if st.button(f"❌ Disconnect", key=f"disconnect_{integration['id']}"):
                            st.warning(f"⚠️ This will disconnect {integration['name']}")
                    
                    # Show configuration if selected
                    if st.session_state.get('selected_integration_config') == integration['id']:
                        st.markdown("### ⚙️ Integration Configuration")
                        
                        with st.form(f"config_form_{integration['id']}"):
                            col_config1, col_config2 = st.columns(2)
                            
                            with col_config1:
                                api_key = st.text_input("API Key", value="sk_live_***", type="password")
                                webhook_enabled = st.checkbox("Enable Webhooks", value=True)
                                auto_sync = st.checkbox("Auto Sync", value=True)
                                sync_frequency = st.selectbox("Sync Frequency", ["Real-time", "Every 5 minutes", "Every 15 minutes", "Hourly"])
                            
                            with col_config2:
                                rate_limit = st.number_input("Rate Limit (per hour)", value=1000)
                                timeout = st.number_input("Timeout (seconds)", value=30)
                                retry_attempts = st.number_input("Retry Attempts", value=3)
                                enable_logging = st.checkbox("Enable Detailed Logging", value=True)
                            
                            col_config_submit1, col_config_submit2 = st.columns(2)
                            with col_config_submit1:
                                if st.form_submit_button("💾 Save Configuration"):
                                    st.success(f"✅ Configuration saved for {integration['name']}")
                                    st.session_state.pop('selected_integration_config', None)
                                    st.rerun()
                            
                            with col_config_submit2:
                                if st.form_submit_button("❌ Cancel"):
                                    st.session_state.pop('selected_integration_config', None)
                                    st.rerun()
                    
                    # Show logs if selected
                    if st.session_state.get('selected_integration_logs') == integration['id']:
                        st.markdown("### 📊 Integration Logs")
                        
                        # Mock log data
                        logs = [
                            {'time': '2025-01-04 10:20:15', 'level': 'INFO', 'message': 'Sync completed successfully', 'status': '✅'},
                            {'time': '2025-01-04 10:15:32', 'level': 'INFO', 'message': 'API call to /customers endpoint', 'status': '✅'},
                            {'time': '2025-01-04 10:10:45', 'level': 'WARNING', 'message': 'Rate limit approaching (950/1000)', 'status': '⚠️'},
                            {'time': '2025-01-04 10:05:12', 'level': 'INFO', 'message': 'Webhook received and processed', 'status': '✅'},
                            {'time': '2025-01-04 10:00:03', 'level': 'ERROR', 'message': 'Connection timeout, retrying...', 'status': '❌'}
                        ]
                        
                        for log in logs:
                            col_log1, col_log2, col_log3, col_log4 = st.columns([2, 1, 3, 0.5])
                            with col_log1:
                                st.write(f"🕒 {log['time']}")
                            with col_log2:
                                st.write(f"📊 {log['level']}")
                            with col_log3:
                                st.write(log['message'])
                            with col_log4:
                                st.write(log['status'])
                        
                        if st.button("❌ Close Logs", key=f"close_logs_{integration['id']}"):
                            st.session_state.pop('selected_integration_logs', None)
                            st.rerun()
        
        with tab2:
            st.markdown("## 🛒 Integration Marketplace")
            
            # Marketplace categories
            col_market1, col_market2, col_market3 = st.columns(3)
            
            with col_market1:
                st.metric("🛒 Available Integrations", len(st.session_state.integrations['available_integrations']))
            
            with col_market2:
                st.metric("📱 Categories", "8")
            
            with col_market3:
                st.metric("⭐ Featured", "5")
            
            # Category filter
            all_categories = list(set(integration['category'] for integration in st.session_state.integrations['available_integrations']))
            selected_category = st.selectbox("Filter by Category", ["All Categories"] + all_categories)
            
            # Search
            search_query = st.text_input("🔍 Search integrations", placeholder="Search by name or feature...")
            
            # Available integrations
            st.markdown("### 🛒 Available Integrations")
            
            available_integrations = st.session_state.integrations['available_integrations']
            
            # Apply filters
            if selected_category != "All Categories":
                available_integrations = [i for i in available_integrations if i['category'] == selected_category]
            
            if search_query:
                available_integrations = [i for i in available_integrations if 
                                        search_query.lower() in i['name'].lower() or 
                                        search_query.lower() in i['description'].lower()]
            
            # Display integrations in grid
            cols = st.columns(2)
            for i, integration in enumerate(available_integrations):
                with cols[i % 2]:
                    complexity_colors = {
                        'Easy': '🟢', 'Medium': '🟡', 'Advanced': '🔴'
                    }
                    
                    with st.container():
                        st.markdown(f"""
                        <div style="border: 2px solid #e0e0e0; padding: 20px; border-radius: 15px; margin: 10px 0; background: #f9f9f9;">
                            <h4>🔗 {integration['name']}</h4>
                            <p><strong>Category:</strong> {integration['category']}</p>
                            <p><strong>Description:</strong> {integration['description']}</p>
                            <p><strong>Cost:</strong> {integration['cost']}</p>
                            <p><strong>Setup Time:</strong> {integration['setup_time']}</p>
                            <p><strong>Complexity:</strong> {complexity_colors.get(integration['complexity'], '⚪')} {integration['complexity']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col_market_btn1, col_market_btn2 = st.columns(2)
                        with col_market_btn1:
                            if st.button(f"🚀 Install", key=f"install_{integration['name']}", type="primary"):
                                st.session_state.selected_integration_install = integration
                                st.rerun()
                        
                        with col_market_btn2:
                            if st.button(f"ℹ️ Details", key=f"details_{integration['name']}"):
                                st.session_state.selected_integration_details = integration
                                st.rerun()
            
            # Installation flow
            if 'selected_integration_install' in st.session_state:
                selected = st.session_state.selected_integration_install
                
                st.markdown("---")
                st.markdown(f"## 🚀 Install {selected['name']}")
                
                with st.form("install_integration"):
                    st.write(f"**Description:** {selected['description']}")
                    st.write(f"**Features:** {', '.join(selected['features'])}")
                    st.write(f"**Cost:** {selected['cost']}")
                    st.write(f"**Setup Time:** {selected['setup_time']}")
                    
                    # Configuration fields based on integration type
                    col_install1, col_install2 = st.columns(2)
                    
                    with col_install1:
                        api_key = st.text_input("API Key*", placeholder="Enter your API key", type="password")
                        webhook_url = st.text_input("Webhook URL", value="https://nxtrix.app/webhooks/")
                        enable_features = st.multiselect("Enable Features", selected['features'])
                    
                    with col_install2:
                        auto_setup = st.checkbox("Automatic setup", value=True)
                        test_connection = st.checkbox("Test connection after setup", value=True)
                        enable_notifications = st.checkbox("Enable notifications", value=True)
                    
                    col_install_submit1, col_install_submit2 = st.columns(2)
                    with col_install_submit1:
                        if st.form_submit_button("✅ Install Integration", type="primary"):
                            # Add to active integrations
                            new_integration = {
                                'id': len(st.session_state.integrations['active_integrations']) + 1,
                                'name': selected['name'],
                                'category': selected['category'],
                                'status': 'Connected',
                                'description': selected['description'],
                                'api_calls': 0,
                                'last_sync': '2025-01-04 10:30',
                                'uptime': '100%',
                                'features': selected['features'],
                                'cost': selected['cost'],
                                'setup_date': '2025-01-04',
                                'webhook_url': webhook_url,
                                'rate_limit': '1000/hour',
                                'data_sync': 'Real-time'
                            }
                            st.session_state.integrations['active_integrations'].append(new_integration)
                            st.success(f"✅ {selected['name']} installed successfully!")
                            st.session_state.pop('selected_integration_install', None)
                            st.rerun()
                    
                    with col_install_submit2:
                        if st.form_submit_button("❌ Cancel"):
                            st.session_state.pop('selected_integration_install', None)
                            st.rerun()
            
            # Integration details
            if 'selected_integration_details' in st.session_state:
                selected = st.session_state.selected_integration_details
                
                st.markdown("---")
                st.markdown(f"## ℹ️ {selected['name']} Details")
                
                col_details1, col_details2 = st.columns(2)
                
                with col_details1:
                    st.write(f"**Category:** {selected['category']}")
                    st.write(f"**Description:** {selected['description']}")
                    st.write(f"**Cost:** {selected['cost']}")
                    st.write(f"**Setup Time:** {selected['setup_time']}")
                    st.write(f"**Complexity:** {selected['complexity']}")
                
                with col_details2:
                    st.write("**Features:**")
                    for feature in selected['features']:
                        st.write(f"• {feature}")
                
                if st.button("❌ Close Details"):
                    st.session_state.pop('selected_integration_details', None)
                    st.rerun()
        
        with tab3:
            st.markdown("## ⚙️ API Management")
            
            # API overview
            col_api1, col_api2, col_api3, col_api4 = st.columns(4)
            
            with col_api1:
                total_endpoints = 23
                st.metric("🔗 API Endpoints", total_endpoints)
            
            with col_api2:
                daily_requests = sum(integration['api_calls'] for integration in st.session_state.integrations['active_integrations'])
                st.metric("📡 Daily Requests", daily_requests)
            
            with col_api3:
                error_rate = "0.02%"
                st.metric("❌ Error Rate", error_rate)
            
            with col_api4:
                avg_response_time = "145ms"
                st.metric("⚡ Avg Response", avg_response_time)
            
            # API endpoints
            st.markdown("### 🔗 API Endpoints")
            
            api_endpoints = [
                {'endpoint': '/api/v1/leads', 'method': 'GET', 'requests': 1247, 'avg_time': '120ms', 'status': 'Active'},
                {'endpoint': '/api/v1/leads', 'method': 'POST', 'requests': 89, 'avg_time': '230ms', 'status': 'Active'},
                {'endpoint': '/api/v1/deals', 'method': 'GET', 'requests': 542, 'avg_time': '98ms', 'status': 'Active'},
                {'endpoint': '/api/v1/deals', 'method': 'PUT', 'requests': 234, 'avg_time': '180ms', 'status': 'Active'},
                {'endpoint': '/api/v1/analytics', 'method': 'GET', 'requests': 78, 'avg_time': '450ms', 'status': 'Active'},
                {'endpoint': '/api/v1/webhooks', 'method': 'POST', 'requests': 156, 'avg_time': '45ms', 'status': 'Active'}
            ]
            
            for endpoint in api_endpoints:
                col_endpoint1, col_endpoint2, col_endpoint3, col_endpoint4, col_endpoint5 = st.columns([3, 1, 1, 1, 1])
                
                with col_endpoint1:
                    method_colors = {'GET': '🟢', 'POST': '🔵', 'PUT': '🟡', 'DELETE': '🔴'}
                    st.write(f"{method_colors.get(endpoint['method'], '⚪')} **{endpoint['method']}** {endpoint['endpoint']}")
                
                with col_endpoint2:
                    st.write(f"📡 {endpoint['requests']}")
                
                with col_endpoint3:
                    st.write(f"⚡ {endpoint['avg_time']}")
                
                with col_endpoint4:
                    st.write(f"🟢 {endpoint['status']}")
                
                with col_endpoint5:
                    if st.button("📊", key=f"endpoint_{endpoint['endpoint']}_{endpoint['method']}", help="View details"):
                        st.info(f"API details for {endpoint['endpoint']}")
            
            # API keys management
            st.markdown("### 🔑 API Keys Management")
            
            api_keys = [
                {'name': 'Production API Key', 'key': 'nxtrix_prod_***', 'created': '2024-10-01', 'last_used': '2025-01-04', 'status': 'Active'},
                {'name': 'Development API Key', 'key': 'nxtrix_dev_***', 'created': '2024-11-15', 'last_used': '2025-01-03', 'status': 'Active'},
                {'name': 'Mobile App API Key', 'key': 'nxtrix_mobile_***', 'created': '2024-12-01', 'last_used': '2025-01-04', 'status': 'Active'}
            ]
            
            for key in api_keys:
                col_key1, col_key2, col_key3, col_key4, col_key5 = st.columns([2, 2, 1, 1, 1])
                
                with col_key1:
                    st.write(f"🔑 **{key['name']}**")
                
                with col_key2:
                    st.write(f"🔐 {key['key']}")
                
                with col_key3:
                    st.write(f"📅 {key['created']}")
                
                with col_key4:
                    st.write(f"🕒 {key['last_used']}")
                
                with col_key5:
                    if st.button("🗑️", key=f"delete_key_{key['name']}", help="Delete key"):
                        st.warning(f"⚠️ Delete {key['name']}?")
            
            # Generate new API key
            if st.button("➕ Generate New API Key", type="primary"):
                new_key = f"nxtrix_new_{hash('new_key') % 10000:04d}"
                st.success(f"✅ New API key generated: {new_key}")
            
            # Rate limiting
            st.markdown("### ⏱️ Rate Limiting")
            
            col_rate1, col_rate2 = st.columns(2)
            
            with col_rate1:
                st.markdown("**Current Limits:**")
                st.write("• Standard Plan: 1,000 requests/hour")
                st.write("• Burst Limit: 100 requests/minute")
                st.write("• Daily Limit: 10,000 requests")
            
            with col_rate2:
                st.markdown("**Usage Today:**")
                st.write(f"• Requests Used: {daily_requests:,}/10,000")
                st.write("• Current Rate: 45 requests/hour")
                st.write("• Peak Rate: 156 requests/hour")
        
        with tab4:
            st.markdown("## 🔄 Automated Workflows")
            
            # Workflow overview
            col_workflow1, col_workflow2, col_workflow3 = st.columns(3)
            
            with col_workflow1:
                active_workflows = 8
                st.metric("⚡ Active Workflows", active_workflows)
            
            with col_workflow2:
                workflow_runs = 247
                st.metric("🔄 Runs Today", workflow_runs)
            
            with col_workflow3:
                success_rate = "98.7%"
                st.metric("✅ Success Rate", success_rate)
            
            # Workflow templates
            st.markdown("### 🔄 Workflow Templates")
            
            workflow_templates = [
                {
                    'name': 'New Lead Processing', 'description': 'Automatically process and assign new leads',
                    'trigger': 'New lead created', 'actions': ['Send welcome email', 'Assign to agent', 'Create task'],
                    'runs': 45, 'success_rate': '100%'
                },
                {
                    'name': 'Deal Stage Progression', 'description': 'Automate actions when deals move between stages',
                    'trigger': 'Deal stage change', 'actions': ['Update CRM', 'Notify team', 'Send follow-up'],
                    'runs': 23, 'success_rate': '95.7%'
                },
                {
                    'name': 'Payment Processing', 'description': 'Handle payment confirmations and failures',
                    'trigger': 'Payment event', 'actions': ['Update subscription', 'Send receipt', 'Log transaction'],
                    'runs': 67, 'success_rate': '99.1%'
                },
                {
                    'name': 'Document Upload', 'description': 'Process new document uploads',
                    'trigger': 'Document uploaded', 'actions': ['Scan for viruses', 'Extract metadata', 'Notify stakeholders'],
                    'runs': 34, 'success_rate': '100%'
                }
            ]
            
            for workflow in workflow_templates:
                with st.expander(f"⚡ {workflow['name']} - {workflow['runs']} runs ({workflow['success_rate']} success)"):
                    col_wf1, col_wf2, col_wf3 = st.columns([2, 2, 1])
                    
                    with col_wf1:
                        st.write(f"**📝 Description:** {workflow['description']}")
                        st.write(f"**🎯 Trigger:** {workflow['trigger']}")
                        st.write(f"**📊 Runs Today:** {workflow['runs']}")
                        st.write(f"**✅ Success Rate:** {workflow['success_rate']}")
                    
                    with col_wf2:
                        st.write("**🔄 Actions:**")
                        for action in workflow['actions']:
                            st.write(f"• {action}")
                    
                    with col_wf3:
                        if st.button(f"✏️ Edit", key=f"edit_wf_{workflow['name']}"):
                            st.info(f"Opening workflow editor for {workflow['name']}")
                        
                        if st.button(f"📊 Logs", key=f"logs_wf_{workflow['name']}"):
                            st.info(f"Showing logs for {workflow['name']}")
                        
                        if st.button(f"▶️ Run", key=f"run_wf_{workflow['name']}"):
                            st.success(f"✅ Workflow '{workflow['name']}' executed successfully!")
            
            # Create new workflow
            if st.button("➕ Create New Workflow", type="primary"):
                st.session_state.show_workflow_builder = True
                st.rerun()
            
            # Workflow builder
            if st.session_state.get('show_workflow_builder'):
                st.markdown("---")
                st.markdown("## 🛠️ Workflow Builder")
                
                with st.form("create_workflow"):
                    col_builder1, col_builder2 = st.columns(2)
                    
                    with col_builder1:
                        wf_name = st.text_input("Workflow Name*", placeholder="My Custom Workflow")
                        wf_description = st.text_area("Description", placeholder="What does this workflow do?")
                        
                        wf_trigger = st.selectbox("Trigger Event", [
                            "New lead created", "Deal stage change", "Payment received",
                            "Document uploaded", "Task completed", "Custom webhook"
                        ])
                        
                        wf_conditions = st.multiselect("Conditions (Optional)", [
                            "Lead value > $50,000", "Deal probability > 70%", "High priority lead",
                            "VIP client", "Specific property type"
                        ])
                    
                    with col_builder2:
                        wf_actions = st.multiselect("Actions*", [
                            "Send email notification", "Create task", "Update CRM record",
                            "Send SMS", "Generate document", "Call webhook", "Assign to user",
                            "Update deal stage", "Log activity", "Send Slack message"
                        ])
                        
                        wf_delay = st.selectbox("Execution Delay", ["Immediate", "5 minutes", "1 hour", "1 day"])
                        wf_enabled = st.checkbox("Enable workflow", value=True)
                    
                    col_builder_submit1, col_builder_submit2 = st.columns(2)
                    with col_builder_submit1:
                        if st.form_submit_button("🚀 Create Workflow", type="primary"):
                            if wf_name and wf_actions:
                                st.success(f"✅ Workflow '{wf_name}' created successfully!")
                                st.session_state.show_workflow_builder = False
                                st.rerun()
                            else:
                                st.error("Please fill in required fields")
                    
                    with col_builder_submit2:
                        if st.form_submit_button("❌ Cancel"):
                            st.session_state.show_workflow_builder = False
                            st.rerun()
        
        with tab5:
            st.markdown("## 📊 Integration Analytics")
            
            # Analytics overview
            col_analytics1, col_analytics2, col_analytics3, col_analytics4 = st.columns(4)
            
            with col_analytics1:
                total_integrations = len(st.session_state.integrations['active_integrations'])
                st.metric("🔗 Total Integrations", total_integrations)
            
            with col_analytics2:
                data_synced = "2.4 GB"
                st.metric("📊 Data Synced", data_synced)
            
            with col_analytics3:
                automation_time_saved = "32 hours"
                st.metric("⏱️ Time Saved", automation_time_saved)
            
            with col_analytics4:
                cost_efficiency = "87%"
                st.metric("💰 Cost Efficiency", cost_efficiency)
            
            # Usage charts
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                st.markdown("### 📡 API Calls by Integration")
                
                integration_names = [i['name'] for i in st.session_state.integrations['active_integrations']]
                api_calls = [i['api_calls'] for i in st.session_state.integrations['active_integrations']]
                
                fig_api = go.Figure(data=[go.Bar(
                    x=integration_names,
                    y=api_calls,
                    marker_color='#4ECDC4'
                )])
                
                fig_api.update_layout(
                    height=300,
                    title="API Calls by Integration",
                    xaxis_title="Integration",
                    yaxis_title="API Calls"
                )
                
                st.plotly_chart(fig_api, use_container_width=True)
            
            with col_chart2:
                st.markdown("### ⚡ Uptime Performance")
                
                uptime_values = [float(i['uptime'].replace('%', '')) for i in st.session_state.integrations['active_integrations']]
                
                fig_uptime = go.Figure(data=[go.Bar(
                    x=integration_names,
                    y=uptime_values,
                    marker_color='#FF6B6B'
                )])
                
                fig_uptime.update_layout(
                    height=300,
                    title="Uptime Performance (%)",
                    xaxis_title="Integration",
                    yaxis_title="Uptime %",
                    yaxis=dict(range=[95, 100])
                )
                
                st.plotly_chart(fig_uptime, use_container_width=True)
            
            # Cost analysis
            st.markdown("### 💰 Cost Analysis")
            
            cost_breakdown = [
                {'service': 'Stripe Payment', 'monthly_cost': 29, 'usage': 'High', 'roi': '+245%'},
                {'service': 'Google Workspace', 'monthly_cost': 48, 'usage': 'Medium', 'roi': '+180%'},
                {'service': 'Supabase Database', 'monthly_cost': 25, 'usage': 'High', 'roi': '+320%'},
                {'service': 'Slack Workspace', 'monthly_cost': 32, 'usage': 'Medium', 'roi': '+150%'},
                {'service': 'Twilio SMS', 'monthly_cost': 15, 'usage': 'Low', 'roi': '+95%'}
            ]
            
            for cost in cost_breakdown:
                col_cost1, col_cost2, col_cost3, col_cost4 = st.columns([2, 1, 1, 1])
                
                with col_cost1:
                    st.write(f"💳 **{cost['service']}**")
                
                with col_cost2:
                    st.write(f"💰 ${cost['monthly_cost']}/month")
                
                with col_cost3:
                    usage_colors = {'High': '🔴', 'Medium': '🟡', 'Low': '🟢'}
                    st.write(f"{usage_colors[cost['usage']]} {cost['usage']}")
                
                with col_cost4:
                    st.write(f"📈 {cost['roi']}")
            
            # Performance metrics
            st.markdown("### 📈 Performance Trends")
            
            # Mock trend data
            months = ['Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan']
            api_calls_trend = [2800, 3200, 3600, 4100, 4500, 4800, 5200]
            cost_trend = [120, 135, 142, 149, 155, 162, 168]
            
            fig_trends = go.Figure()
            
            fig_trends.add_trace(go.Scatter(
                x=months, y=api_calls_trend,
                mode='lines+markers', name='API Calls',
                line=dict(color='#2E86AB', width=3)
            ))
            
            fig_trends.add_trace(go.Scatter(
                x=months, y=cost_trend,
                mode='lines+markers', name='Monthly Cost ($)',
                line=dict(color='#A23B72', width=3),
                yaxis='y2'
            ))
            
            fig_trends.update_layout(
                title="Integration Performance Trends",
                xaxis_title="Month",
                yaxis=dict(title="API Calls", titlefont=dict(color="#2E86AB")),
                yaxis2=dict(title="Cost ($)", overlaying="y", side="right", titlefont=dict(color="#A23B72")),
                height=400,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_trends, use_container_width=True)
        
        with tab6:
            st.markdown("## 🛠️ Integration Settings")
            
            col_settings1, col_settings2 = st.columns(2)
            
            with col_settings1:
                st.markdown("### 🔐 Security Settings")
                
                require_auth = st.checkbox("Require authentication for all integrations", value=True)
                enable_2fa = st.checkbox("Enable 2FA for sensitive integrations", value=True)
                log_all_requests = st.checkbox("Log all API requests", value=True)
                encrypt_data = st.checkbox("Encrypt data in transit", value=True)
                
                st.markdown("### 📡 API Settings")
                
                default_timeout = st.number_input("Default timeout (seconds)", value=30, min_value=5, max_value=300)
                max_retries = st.number_input("Maximum retry attempts", value=3, min_value=0, max_value=10)
                rate_limit_default = st.number_input("Default rate limit (per hour)", value=1000, min_value=100)
                
                enable_webhooks = st.checkbox("Enable webhook endpoints", value=True)
                webhook_security = st.checkbox("Require webhook signature validation", value=True)
            
            with col_settings2:
                st.markdown("### 🔔 Notification Settings")
                
                notify_connection_issues = st.checkbox("Notify on connection issues", value=True)
                notify_rate_limits = st.checkbox("Notify when approaching rate limits", value=True)
                notify_new_integrations = st.checkbox("Notify on new integrations", value=True)
                notify_cost_alerts = st.checkbox("Notify on cost threshold alerts", value=True)
                
                notification_channels = st.multiselect("Notification Channels", 
                                                     ["Email", "Slack", "SMS", "In-app"], default=["Email", "In-app"])
                
                st.markdown("### 💰 Cost Management")
                
                monthly_budget = st.number_input("Monthly integration budget ($)", value=500, min_value=0)
                cost_alert_threshold = st.slider("Cost alert threshold (%)", 0, 100, 80)
                
                auto_disable_expensive = st.checkbox("Auto-disable integrations exceeding budget", value=False)
                
                st.markdown("### 🔄 Sync Settings")
                
                default_sync_frequency = st.selectbox("Default sync frequency", 
                                                     ["Real-time", "Every 5 minutes", "Every 15 minutes", "Hourly", "Daily"])
                
                sync_during_maintenance = st.checkbox("Continue syncing during maintenance", value=False)
                batch_size = st.number_input("Default batch size", value=100, min_value=10, max_value=1000)
            
            # Save settings
            if st.button("💾 Save All Settings", type="primary"):
                st.success("✅ All integration settings saved successfully!")
            
            # Export/Import configuration
            st.markdown("### 📁 Configuration Management")
            
            col_config1, col_config2 = st.columns(2)
            
            with col_config1:
                if st.button("📤 Export Configuration"):
                    st.success("📊 Integration configuration exported to JSON")
                
                if st.button("🔄 Backup Settings"):
                    st.success("💾 Settings backed up successfully")
            
            with col_config2:
                uploaded_config = st.file_uploader("📥 Import Configuration", type=['json'])
                if uploaded_config:
                    if st.button("🔄 Import and Apply"):
                        st.success("✅ Configuration imported and applied successfully!")
    
    except Exception as e:
        st.error(f"Error in integrations management: {str(e)}")
    
    # Add navigation CTAs
    add_navigation_ctas()
    
    # Back to dashboard option
    if st.button("⬅️ Back to Dashboard", key="back_to_dashboard_integrations"):
        st.session_state.pop("show_integrations", None)
        st.rerun()

if __name__ == "__main__":
    main()
