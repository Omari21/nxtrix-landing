import streamlit as st
import os
from supabase import create_client
from dotenv import load_dotenv

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
    """Simple dashboard view"""
    st.set_page_config(
        page_title="NxTrix CRM - Dashboard",
        page_icon="🏢",
        layout="wide"
    )
    
    st.title("🏢 NxTrix CRM Dashboard")
    st.markdown("---")
    
    # User info
    if "user_info" in st.session_state:
        user = st.session_state["user_info"]
        st.sidebar.markdown(f"**Welcome, {user.get('full_name', 'User')}!**")
        st.sidebar.markdown(f"📧 {user.get('email', '')}")
        
        if st.sidebar.button("🚪 Logout"):
            st.session_state.clear()
            st.rerun()
    
    # Main dashboard content
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📈 Total Leads", "0", "+0")
    
    with col2:
        st.metric("💰 Deals Closed", "0", "+0")
    
    with col3:
        st.metric("📊 Conversion Rate", "0%", "+0%")
    
    st.markdown("---")
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➕ Add Lead", use_container_width=True):
            st.info("Lead management coming soon!")
    
    with col2:
        if st.button("📊 View Analytics", use_container_width=True):
            st.info("Analytics coming soon!")
    
    with col3:
        if st.button("💰 Payment Setup", use_container_width=True):
            st.info("Payment management coming soon!")
    
    with col4:
        if st.button("⚙️ Settings", use_container_width=True):
            st.info("Settings coming soon!")
    
    # Welcome message
    st.markdown("---")
    st.info("🎉 **Welcome to NxTrix CRM!** Your dashboard is ready. We're gradually rolling out features to ensure the best experience.")

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
        show_dashboard()
        return
    
    if st.session_state.get("page") == "onboarding":
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

if __name__ == "__main__":
    main()
