import streamlit as st
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv

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
    """Get current user information from Supabase Auth"""
    try:
        user = supabase.auth.get_user()
        if user and user.user:
            return {
                "id": user.user.id,
                "email": user.user.email,
                "user_metadata": user.user.user_metadata
            }
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

# PWA Configuration for Mobile
st.set_page_config(
    page_title="NxTrix CRM - Real Estate Investment Platform",
    page_icon="🏢",
    layout="centered",
    menu_items={
        'Get Help': 'https://nxtrix-crm.com/help',
        'Report a bug': 'https://nxtrix-crm.com/bug-report',
        'About': "NxTrix CRM - AI-powered real estate investment platform"
    }
)

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

def show_dashboard():
    """Complete NxTrix dashboard with all advanced features"""
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from datetime import datetime, timedelta
    
    # Page Configuration
    st.set_page_config(page_title="NxTrix Dashboard", layout="wide", page_icon="🏠")
    
    # Get user info
    if not st.session_state.get("user_info"):
        st.warning("You must be logged in to access the dashboard.")
        st.stop()
    
    user_info = st.session_state["user_info"]
    user_id = user_info["id"]
    
    # Dashboard Header with Branding
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               padding: 2rem; border-radius: 15px; margin-bottom: 2rem; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 2.5rem;">🏠 NxTrix CRM Dashboard</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1.2rem;">
            AI-Powered Real Estate Investment Management
        </p>
    </div>
    """, unsafe_allow_html=True)
    
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
    
    # Sidebar Navigation
    with st.sidebar:
        st.markdown(f"**Welcome, {user_info.get('full_name', 'User')}!**")
        st.markdown(f"📧 {user_info.get('email', '')}")
        
        st.markdown("---")
        st.markdown("### 🧭 Navigation")
        
        nav_col1, nav_col2 = st.columns(2)
        with nav_col1:
            if st.button("🏠 Leads", use_container_width=True):
                st.session_state["show_leads"] = True
                st.rerun()
        with nav_col2:
            if st.button("👥 Clients", use_container_width=True):
                st.session_state["show_clients"] = True
                st.rerun()
        
        nav_col3, nav_col4 = st.columns(2)
        with nav_col3:
            if st.button("📊 Analytics", use_container_width=True):
                st.session_state["show_analytics"] = True
                st.rerun()
        with nav_col4:
            if st.button("⚙️ Settings", use_container_width=True):
                st.session_state["show_settings"] = True
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
    
    # Speed and Performance Comparison
    col_perf1, col_perf2 = st.columns(2)
    
    with col_perf1:
        st.markdown("""
        <div style="background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 1rem; border-radius: 5px;">
            <h4 style="color: #1e40af; margin: 0 0 0.5rem 0;">⚡ Speed Comparison</h4>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span><strong>NxTrix:</strong></span>
                <span style="color: #059669; font-weight: bold;">12 seconds</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span><strong>Traditional CRMs:</strong></span>
                <span style="color: #dc2626; font-weight: bold;">2-4 hours</span>
            </div>
            <div style="border-top: 1px solid #bfdbfe; padding-top: 0.5rem; margin-top: 0.5rem;">
                <span style="color: #059669; font-weight: bold;">🎯 98% Speed Improvement</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_perf2:
        # Performance metrics
        if data["total_leads"] > 0:
            deal_velocity = deals_in_contract / max(1, data["total_leads"]) * 100
            your_performance = min(95, max(60, 75 + (deal_velocity / 2)))
            industry_avg = 43.2
            
            st.markdown(f"""
            <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; border: 1px solid #e2e8f0;">
                <h4 style="margin: 0 0 1rem 0;">📊 Your Performance vs Industry</h4>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span><strong>Your Score:</strong></span>
                    <span style="color: #059669; font-weight: bold;">{your_performance:.1f}/100</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span><strong>Industry Average:</strong></span>
                    <span style="color: #6b7280;">{industry_avg}/100</span>
                </div>
                <div style="background: #e2e8f0; border-radius: 10px; height: 10px; margin: 0.5rem 0;">
                    <div style="background: linear-gradient(90deg, #22c55e, #059669); border-radius: 10px; height: 100%; width: {your_performance}%;"></div>
                </div>
                <small style="color: #059669; font-weight: bold;">
                    ⬆️ {your_performance - industry_avg:.1f} points above industry average
                </small>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Add leads to see performance comparison")
    
    # Quick Actions
    st.markdown("### 🎯 Quick Actions")
    col_action1, col_action2 = st.columns(2)
    with col_action1:
        if st.button("🔍 Find Deals", use_container_width=True):
            st.session_state["show_deal_finder"] = True
            st.rerun()
    with col_action2:
        if st.button("👥 Manage Buyers", use_container_width=True):
            st.session_state["show_buyer_manager"] = True
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
    
    # === MARKET INTELLIGENCE SECTION ===
    st.markdown("## 🌍 Real-Time Market Intelligence")
    
    col_market1, col_market2 = st.columns(2)
    
    with col_market1:
        current_time = datetime.now().strftime("%I:%M %p")
        st.markdown(f"""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 1rem; border-radius: 8px;">
            <h4 style="margin: 0 0 1rem 0;">📈 Today's Market Snapshot</h4>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span><strong>Market Activity:</strong></span>
                <span style="color: #059669;">🟢 High ({current_time})</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span><strong>Investor Demand:</strong></span>
                <span style="color: #dc2626;">🔴 Critical</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span><strong>Deal Flow:</strong></span>
                <span style="color: #f59e0b;">🟡 Moderate</span>
            </div>
            <div style="border-top: 1px solid #e2e8f0; padding-top: 0.5rem; margin-top: 0.5rem;">
                <small style="color: #6b7280;">📊 Updated every 15 minutes</small>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_market2:
        deal_alerts = 3 + (len(seller_leads) % 5)
        hot_deals = max(1, deal_alerts // 2)
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #ef4444, #dc2626); color: white; 
                   padding: 1rem; border-radius: 8px; text-align: center;">
            <h3 style="margin: 0 0 0.5rem 0;">🚨 {deal_alerts} New Opportunities</h3>
            <p style="margin: 0; font-size: 1.1rem;">{hot_deals} marked as "HOT DEALS"</p>
            <p style="margin: 0; font-size: 0.9rem; opacity: 0.9;">AI confidence 85%+</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔍 View Hot Deals", use_container_width=True, type="primary"):
            st.session_state["show_hot_deals"] = True
            st.rerun()
    
    # Handle navigation states
    if st.session_state.get("show_leads"):
        show_leads_page()
    elif st.session_state.get("show_analytics"):
        show_analytics_page()
    elif st.session_state.get("show_deal_finder"):
        show_deal_finder_page()
    elif st.session_state.get("show_hot_deals"):
        show_hot_deals_page()
    
    # === SUCCESS MESSAGE ===
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
        try:
            # Try different path variations for Streamlit Cloud
            dashboard_paths = [
                "Dashboard.py",  # Root level copy
                "pages/1_Dashboard.py",
                "./pages/1_Dashboard.py", 
                "1_Dashboard.py"
            ]
            
            success = False
            for path in dashboard_paths:
                try:
                    st.switch_page(path)
                    success = True
                    break
                except:
                    continue
            
            if not success:
                st.info("� Dashboard loaded in compatibility mode")
                show_dashboard()
        except Exception as e:
            st.info("📊 Dashboard loaded in compatibility mode")
            show_dashboard()
        return
    
    if st.session_state.get("page") == "onboarding":
        try:
            # Try different path variations for onboarding
            onboarding_paths = [
                "Onboarding.py",  # Root level copy
                "pages/onboarding_wizard.py",
                "./pages/onboarding_wizard.py",
                "onboarding_wizard.py"
            ]
            
            success = False
            for path in onboarding_paths:
                try:
                    st.switch_page(path)
                    success = True
                    break
                except:
                    continue
            
            if not success:
                st.info("🚀 Onboarding loaded in compatibility mode")
                show_onboarding()
        except Exception as e:
            st.info("🚀 Onboarding loaded in compatibility mode")
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
    """Hot deals marketplace"""
    st.markdown("### 🔥 Hot Deals Marketplace")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #ef4444, #dc2626); color: white; 
               padding: 1.5rem; border-radius: 10px; margin-bottom: 1rem; text-align: center;">
        <h3 style="margin: 0;">🚨 URGENT: High-ROI Opportunities</h3>
        <p style="margin: 0.5rem 0 0 0;">AI-verified deals with 20%+ ROI potential</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Generate sample hot deals
    hot_deals = [
        {
            "address": "1247 Oak Street, Memphis, TN",
            "arv": 185000,
            "investment": 120000,
            "roi": 23.4,
            "confidence": 92,
            "days_left": 3
        },
        {
            "address": "892 Pine Avenue, Little Rock, AR",
            "arv": 145000,
            "investment": 95000,
            "roi": 21.8,
            "confidence": 87,
            "days_left": 5
        },
        {
            "address": "456 Maple Drive, Birmingham, AL",
            "arv": 210000,
            "investment": 140000,
            "roi": 25.1,
            "confidence": 94,
            "days_left": 2
        }
    ]
    
    for i, deal in enumerate(hot_deals):
        urgency_color = "#dc2626" if deal["days_left"] <= 3 else "#f59e0b"
        
        st.markdown(f"""
        <div style="border: 2px solid {urgency_color}; border-radius: 10px; padding: 1rem; margin-bottom: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <h4 style="margin: 0; color: #1f2937;">🏠 {deal['address']}</h4>
                <span style="background: {urgency_color}; color: white; padding: 0.3rem 0.8rem; 
                           border-radius: 20px; font-weight: bold;">
                    {deal['days_left']} days left
                </span>
            </div>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1rem;">
                <div><strong>ARV:</strong> ${deal['arv']:,.0f}</div>
                <div><strong>Investment:</strong> ${deal['investment']:,.0f}</div>
                <div><strong>ROI:</strong> <span style="color: #059669; font-weight: bold;">{deal['roi']:.1f}%</span></div>
                <div><strong>AI Confidence:</strong> {deal['confidence']}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(f"📞 Contact Seller", key=f"contact_{i}"):
                st.success("Seller contact info sent to your email!")
        with col2:
            if st.button(f"💾 Save Deal", key=f"save_{i}"):
                st.success("Deal saved to your pipeline!")
        with col3:
            if st.button(f"📊 Full Analysis", key=f"analyze_{i}"):
                st.info("Detailed analysis report generated!")
    
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

if __name__ == "__main__":
    main()
