import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from dash.exceptions import PreventUpdate
from dash_extensions import DeferScript
from flask import session
from flask_session import Session
import layouts as ly
from layouts import themes
import utils as ut
from models import db, bcrypt, User  # Import User model and bcrypt instance
#from layouts import login_layout, dashboard_layout, about_layout,profile_layout, forgot_layout, subscription_page, create_register_layout,create_subscription_selection_layout, faq_layout, blog_layout
from flask_mail import Mail
import auth_callbacks
from flask import request
import data_callbacks
import stripe
from flask import redirect, url_for
from flask import render_template
import logging
from flask_caching import Cache
from flask_minify import Minify
from flask_compress import Compress
from flask import render_template, abort
import secrets
from flask import send_from_directory


# Initialize the Dash app with a default Bootstrap theme
app = dash.Dash(__name__,  use_pages=True, external_stylesheets=[
                dbc.themes.SPACELAB, "https://cdnjs.cloudflare.com/ajax/libs/bootstrap-icons/1.5.0/font/bootstrap-icons.min.css"], suppress_callback_exceptions=True)
server = app.server

from pages.home import layout as homepage_layout
from layouts import login_layout, dashboard_layout, about_layout,profile_layout, forgot_layout, subscription_page, create_register_layout,create_subscription_selection_layout, faq_layout, blog_layout


app.server.config['COMPRESS_ALGORITHM'] = 'br'
app.server.config['COMPRESS_LEVEL'] = 9  # Set compression level (1-9, default is 6)
app.server.config['COMPRESS_MIN_SIZE'] = 500  # Minimum size (in bytes) to trigger compression
# app.server.config['COMPRESS_MIMETYPES'] = ['text/html', 'text/css', 'application/javascript', 'application/json','font/woff','font/woff2', 'image/gif']  # File types to compress
compress = Compress()
compress.init_app(server)

Minify(app=server, html=True, js=True, cssless=True)

from flask import send_file
@server.route('/sitemap.xml')
def sitemap_xml():
    sitemap_path = os.path.join(os.getcwd(), 'static', 'sitemap.xml')
    if not os.path.exists(sitemap_path):
        print(f"sitemap.xml not found at: {sitemap_path}")
        abort(404)  # Return 404 if file not found
    return send_file(sitemap_path)
    
@server.route('/robots.txt')
def robots_txt():
    try:
        robots_path = os.path.join(os.getcwd(), 'static', 'robots.txt')
        if not os.path.exists(robots_path):
            abort(404)  # Return 404 if the file is not found
        return send_file(robots_path, mimetype='text/plain')
    except Exception as e:
        # Log the error and return a 500 Internal Server Error response
        current_app.logger.error(f"Error serving robots.txt: {str(e)}")
        abort(500)

from flask import send_from_directory

@server.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(os.getcwd(), 'assets'),
                               'logo_with_transparent_background_favicon.png', mimetype='image/png')

import logging
from flask import render_template


server.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure the session
load_dotenv()
app.server.config['SECRET_KEY'] =  os.getenv('FLASK_SECRET_KEY') # Use a strong, unique secret key
app.server.config['SESSION_TYPE'] = 'filesystem' 
app.server.config['SESSION_PERMANENT'] = True  # Make session permanent to last across sessions
app.server.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Customize session lifetime (e.g., 7 days)

app.server.config['CACHE_TYPE'] = 'SimpleCache'  # You can also use 'RedisCache', 'FileSystemCache', etc.
app.server.config['CACHE_DEFAULT_TIMEOUT'] = 600  # Cache timeout in seconds (10 minutes)

# Initialize Cache object
cache = Cache(app.server)

Session(app.server)

# Email configuration
server.config['MAIL_SERVER'] = 'smtp.gmail.com'
server.config['MAIL_PORT'] = 587
server.config['MAIL_USE_TLS'] = True
server.config['MAIL_USERNAME'] = 'mystocks.monitoring@gmail.com'
server.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')


# Google OAuth Configuration-----------------------------------------------------------------------------
from authlib.integrations.flask_client import OAuth

oauth = OAuth(app.server)

# Google OAuth Configuration
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid profile email'}
)

@app.server.before_request
def ensure_flask_routes_are_handled():
    # Skip handling for any routes that start with /login to let Flask handle them
    if request.path.startswith("/login"):
        return None  # Flask will handle these routes


# Google login route
@server.route('/login/google')
def google_login():
    nonce = secrets.token_urlsafe(16)  # Generate a random nonce
    session['oauth_nonce'] = nonce  # Store nonce in session
    
    redirect_uri = url_for('google_callback', _external=True)
    print(f"Redirecting to Google for authentication, callback: {redirect_uri}")
    
    # Include nonce in the request
    return oauth.google.authorize_redirect(redirect_uri, nonce=nonce)

@server.route('/logout')
def logout():
    # Clear the session
    session.clear()
    return redirect('/')


# Google callback route
@server.route('/login/callback')
def google_callback():
    token = oauth.google.authorize_access_token()
    print(f"Token received: {token}")
    
    try:
        nonce = session.get('oauth_nonce')
        if not nonce:
            raise Exception("Missing nonce in session")
        
        # Parse the ID token and verify nonce
        user_info = oauth.google.parse_id_token(token, nonce=nonce)
        print(f"User Info received: {user_info}")
        
        email = user_info['email']
        google_id = user_info['sub']
        base_username = user_info.get('name', 'Unknown')

        # Check if a user already exists with the given Google ID or email
        user = User.query.filter((User.google_id == google_id) | (User.email == email)).first()

        if not user:
            # Retrieve the selected plan from the session
            selected_plan = session.get('selected_plan', 'free')  # Default to 'free' if not set

            # Generate a unique username if the user does not exist
            username = ut.generate_unique_username(base_username)

            # Set the subscription status based on the selected plan
            subscription_status = 'premium' if selected_plan == 'premium' else 'free'

            # If user doesn't exist, create a new user with the correct subscription status
            user = User(
                username=username,
                email=email,
                google_id=google_id,
                subscription_status=subscription_status,  # Set subscription status based on plan
                confirmed=True  # Google users are automatically confirmed
            )
            ut.send_welcome_email(email, username, mail)
            ut.send_watchlist_email(email, username,mail,app)
            db.session.add(user)
            db.session.commit()
            print(f"New user created: {user.username} with {subscription_status} plan.")
        else:
            print(f"User exists: {user.username}")

        # Log the user in by setting session
        session['user_id'] = user.id
        session['username'] = user.username  # Store username in session for convenience
        session['logged_in'] = True  # Set logged_in flag
        print(f"User logged in: {user.username}")

        # If the user has an active premium subscription, do not trigger Stripe again
        if user.subscription_status == 'premium' and user.stripe_subscription_id:
            print(f"User {user.username} already has an active premium subscription.")
            # Redirect to the dashboard or home page for premium users
            return redirect('/')
        
        # If the plan is premium and no active subscription, redirect to the Stripe checkout session
        if user.subscription_status == 'premium':
            return redirect(url_for('create_checkout_session'))
        
        # Redirect to home ("/") after successful login for free users
        return redirect('/')

    except Exception as e:
        print(f"Error during Google OAuth: {str(e)}")
        return "Login failed, please try again."



# Add a route for profile to ensure redirect works
@server.route('/profile')
def profile():
    # Check if the user is logged in by checking the session
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    # Fetch user details from the database
    user = User.query.get(user_id)
    return f"Welcome, {user.username}!"


#----------------------------------------------------------------------------------------------------------

# Initialize the database with Flask app context
db.init_app(app.server)
bcrypt.init_app(app.server)
mail = Mail(app.server)

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
SUBSCRIPTION_PRICE_ID = os.getenv('SUBSCRIPTION_PRICE_ID')


# Create the database tables
with app.server.app_context():
    db.create_all()


app.layout = html.Div([
    # Store to keep the conversation history

    dcc.Store(id='conversation-store', data=[]),
    dcc.Store(id='individual-stocks-store', data=['AAPL', 'MSFT'], storage_type='session'),
    dcc.Store(id='theme-store', data=dbc.themes.SPACELAB),
    dcc.Store(id='plotly-theme-store', data='plotly_white'),
    dcc.Store(id='login-status', data=False),  # Store to track login status
    # Store to persist the username
    dcc.Store(id='login-username-store', data=None),
    html.Link(id='theme-switch', rel='stylesheet', href=dbc.themes.BOOTSTRAP),
    ly.create_navbar(themes),  # Navbar
    ly.create_overlay(),  # Access Restricted Overlay
    dcc.Location(id='url', refresh=True),
    dbc.Container(dash.page_container, id='page-content', fluid=True) , # Render pages dynamically

    dcc.Store(id='active-tab', data='📈 Prices'),
    # dcc.Location(id='url-refresh', refresh=True),
    dcc.Location(id='url-redirect', refresh=True),
    ly.create_floating_chatbot_button(),  # Floating Chatbot Button
    ly.create_chatbot_modal(),  # Chatbot Modal
    ly.create_financials_modal(),  # Financials Modal
    html.Div(ly.create_sticky_footer_mobile(), id="sticky-footer-container"),
    ly.create_footer(),  # Footer
    ly.create_modal_register(),
    dcc.Store(id='device-type', data='desktop'),  # Default to desktop
    DeferScript(src='assets/script.js'),
    # Loads Plotly script after rendering
    DeferScript(src="/assets/plotly.js"),
    DeferScript(src="/assets/dash_bootstrap_components.v1_6_0.min.js"),
    # Store to keep track of the active tab globally
    dcc.Store(id='active-tab-store', data='prices-tab'),  # Default active tab
    # Initialize the forecast attempts at 0
    # dcc.Store(id='forecast-attempt-store', data=0),
    dcc.Store(id='last-known-path', data='/prices'),
    dcc.Store(id='forecast-attempt-store', data=0, storage_type= 'session')

])

# Serve Static Assets
@server.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory('assets', path)

# Catch-All Route for Multipage App
@server.route('/', defaults={'path': ''})
@server.route('/<path:path>')
def serve_dash_app(path):
    # Always serve Dash's `index.html` for unmatched routes
    return send_from_directory('', 'index.html')


auth_callbacks.register_auth_callbacks(app, server, mail)
data_callbacks.get_data_callbacks(app, server, cache)


@server.route('/check-session')
def check_session():
    logged_in = session.get('logged_in', False)
    username = session.get('username', None)
    return f"Logged In: {logged_in}, Username: {username}"


@app.server.route('/confirm/<token>')
def confirm_email(token):
    try:
        # Validate the token and retrieve the user's email
        email = ut.confirm_token(token, server)
    except:
        return render_template('email_confirmation.html', message="The confirmation link is invalid or has expired.")

    # Find the user by email
    user = User.query.filter_by(email=email).first_or_404()

    if user.confirmed:
        return render_template('email_confirmation.html', message="Account already confirmed. Please log in.")
    else:
        # Mark the user as confirmed
        user.confirmed = True
        user.confirmed_on = datetime.now()
        db.session.commit()

        # For premium users, redirect to checkout
        if user.subscription_status == 'premium':
            # Ensure session has the username
            session['username'] = user.username
            return redirect(url_for('create_checkout_session'))

        # For free users, show confirmation message and redirect to login after 5 seconds
        return '''
            <html>
                <head>
                    <meta http-equiv="refresh" content="5; url=/login" />
                </head>
                <body>
                    <h1>Email Confirmed!</h1>
                    <p>Your email has been confirmed. You will be redirected to the login page in 5 seconds.</p>
                    <p>If you are not redirected, click <a href="/login">here</a>.</p>
                </body>
            </html>
        '''


@app.server.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = ut.confirm_token(token, server)
    except:
        return render_template('password_reset.html', message="The reset link is invalid or has expired.", show_login_link=False)

    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            return render_template('password_reset.html', message="Passwords do not match.", show_login_link=False)

        # Reset the password
        user = User.query.filter_by(email=email).first_or_404()
        hashed_password = bcrypt.generate_password_hash(
            password).decode('utf-8')
        user.password = hashed_password
        db.session.commit()

        return render_template('password_reset.html', message="Your password has been reset successfully. You can now ", show_login_link=True)
    else:
        return render_template('password_reset.html', message=None, show_login_link=False)


# SUBSCRIBER ROUTES---------------------------

@server.route('/create-checkout-session', methods=['POST', 'GET'])
def create_checkout_session():
    try:
        # Get the logged-in user's username from the session
        username = session.get('username')

        if not username:
            # If no user is logged in, redirect to login
            return redirect('/login')

        # Fetch the user from the database
        user = User.query.filter_by(username=username).first()

        if not user:
            # If the user is not found, redirect to login
            return redirect('/login')

        # Create the checkout session for Stripe, using the user's email from the database
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': SUBSCRIPTION_PRICE_ID,  # Price ID for premium plan
                'quantity': 1,
            }],
            mode='subscription',
            customer_email=user.email,  # Pass the user's email to Stripe
            success_url=url_for(
                'subscription_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('subscription_cancel', _external=True),
        )
        return redirect(checkout_session.url, code=303)

    except Exception as e:
        return str(e)


@app.server.route('/cancel-subscription', methods=['POST', 'GET'])
def cancel_subscription():
    # Get the logged-in user's information
    username = session.get('username')

    if not username:
        return redirect('/login')

    # Fetch the user from the database
    user = User.query.filter_by(username=username).first()

    if not user or user.subscription_status != 'premium':
        return "No active subscription found."

    try:
        if user.stripe_subscription_id:
            try:
                # Attempt to retrieve the subscription from Stripe
                stripe_subscription = stripe.Subscription.retrieve(
                    user.stripe_subscription_id)
                logging.info(f"Subscription retrieved: {stripe_subscription}")
            except stripe.error.InvalidRequestError as e:
                if 'resource_missing' in str(e):
                    logging.warning(f"Subscription already deleted: {str(e)}")
                    # Assume the subscription has been deleted and update the database
                    user.subscription_status = 'free'
                    user.stripe_subscription_id = None
                    db.session.commit()
                    # Redirect without error
                    return '''
                        <html>
                            <head>
                                <meta http-equiv="refresh" content="5; url=/" />
                            </head>
                            <body>
                                <h1>Subscription canceled successfully!</h1>
                                <p>You will be redirected to the home page in 5 seconds.</p>
                            </body>
                        </html>
                    '''
                else:
                    # In case it's another Stripe error
                    logging.error(f"Stripe Error: {str(e)}")
                    return '''
                        <html>
                            <head>
                                <meta http-equiv="refresh" content="5; url=/" />
                            </head>
                            <body>
                                <h1>Subscription canceled successfully!</h1>
                                <p>You will be redirected to the home page in 5 seconds.</p>
                            </body>
                        </html>
                    '''

            if stripe_subscription.status == 'canceled':
                # If subscription is already canceled
                user.subscription_status = 'free'
                user.stripe_subscription_id = None
                db.session.commit()
                return '''
                    <html>
                        <head>
                            <meta http-equiv="refresh" content="5; url=/" />
                        </head>
                        <body>
                            <h1>Subscription already canceled!</h1>
                            <p>You will be redirected to the home page in 5 seconds.</p>
                        </body>
                    </html>
                '''

            if stripe_subscription.status == 'active':
                try:
                    # Cancel the subscription
                    stripe.Subscription.delete(stripe_subscription.id)
                    logging.info(
                        f"Subscription deleted: {stripe_subscription.id}")

                    # Update the database immediately
                    user.subscription_status = 'free'
                    user.stripe_subscription_id = None
                    db.session.commit()

                    return '''
                        <html>
                            <head>
                                <meta http-equiv="refresh" content="5; url=/" />
                            </head>
                            <body>
                                <h1>Subscription canceled successfully!</h1>
                                <p>You will be redirected to the home page in 5 seconds.</p>
                            </body>
                        </html>
                    '''
                except stripe.error.StripeError as e:
                    logging.error(f"Stripe Error during deletion: {str(e)}")
                    # Completely ignore resource_missing errors and proceed
                    if 'resource_missing' in str(e):
                        logging.info("Subscription already deleted in Stripe.")
                        user.subscription_status = 'free'
                        user.stripe_subscription_id = None
                        db.session.commit()
                        return '''
                            <html>
                                <head>
                                    <meta http-equiv="refresh" content="5; url=/" />
                                </head>
                                <body>
                                    <h1>Subscription canceled successfully!</h1>
                                    <p>You will be redirected to the home page in 5 seconds.</p>
                                </body>
                            </html>
                        '''
                    return '''
                        <html>
                            <head>
                                <meta http-equiv="refresh" content="5; url=/" />
                            </head>
                            <body>
                                <h1>Subscription canceled successfully!</h1>
                                <p>You will be redirected to the home page in 5 seconds.</p>
                            </body>
                        </html>
                    '''

        else:
            return "No Stripe subscription ID found."

    except stripe.error.StripeError as e:
        logging.error(f"Stripe Error: {str(e)}")
        # Ignore the error and redirect
        return '''
            <html>
                <head>
                    <meta http-equiv="refresh" content="5; url=/" />
                </head>
                <body>
                    <h1>Subscription canceled successfully!</h1>
                    <p>You will be redirected to the home page in 5 seconds.</p>
                </body>
            </html>
        '''

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        # Ignore the error and redirect
        return '''
            <html>
                <head>
                    <meta http-equiv="refresh" content="5; url=/" />
                </head>
                <body>
                    <h1>Subscription canceled successfully!</h1>
                    <p>You will be redirected to the home page in 5 seconds.</p>
                </body>
            </html>
        '''


@app.server.route('/subscription-cancel')
def subscription_cancel():
    return """
    <html>
        <body>
            <h1>Subscription was canceled.</h1>
            <p>You have canceled the subscription process. Please try again if you wish to upgrade.</p>
        </body>
    </html>
    """


@app.server.route('/subscription-success')
def subscription_success():
    session_id = request.args.get('session_id')

    try:
        # Retrieve the Stripe session using the session_id
        stripe_session = stripe.checkout.Session.retrieve(session_id)

        # Retrieve customer details from the Stripe session
        customer_email = stripe_session['customer_details']['email']
        user = User.query.filter_by(email=customer_email).first()

        if user:
            # Log the session info for debugging
            logging.info(
                f"User {user.username} successfully subscribed. Stripe Session: {stripe_session}")

            # Retrieve the Stripe subscription from the session and save it to the user
            stripe_subscription = stripe.Subscription.retrieve(
                stripe_session['subscription'])
            # Save the latest subscription ID
            user.stripe_subscription_id = stripe_subscription.id

            # Mark the user's payment status as complete in the database
            user.payment_status = True
            user.subscription_status = 'premium'
            db.session.commit()

            # Update session to reflect that the user is now a premium subscriber
            session['subscription_status'] = 'premium'
        else:
            # Log an error if no user was found
            logging.error(f"No user found with email {customer_email}")

    except stripe.error.StripeError as e:
        # Log Stripe API errors
        logging.error(f"Stripe Error: {str(e)}")
        return f"Stripe Error: {str(e)}"

    except Exception as e:
        # Log other general errors
        logging.error(f"An error occurred: {str(e)}")
        return f"Error: {str(e)}"

    # Redirect to the dashboard after success
    return """
    <html>
        <head>
            <meta http-equiv="refresh" content="5; url=/" />
        </head>
        <body>
            <h1>Subscription successful! Thank you for subscribing.</h1>
            <p>You will be redirected to the dashboard in 5 seconds.</p>
        </body>
    </html>
    """


@app.callback(
    Output('url-redirect', 'pathname'),
    [Input('free-signup-button', 'n_clicks'),
     Input('paid-signup-button', 'n_clicks')]
)
def handle_plan_selection(free_clicks, paid_clicks):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Handle plan selection and store the selected plan in the session
    if button_id == 'free-signup-button' and free_clicks:
        session['selected_plan'] = 'free'
        return '/register-free'
    elif button_id == 'paid-signup-button' and paid_clicks:
        session['selected_plan'] = 'premium'
        return '/register-paid'

    raise PreventUpdate
    
    

@app.callback(
    Output("date-range-container", "style"),
    [Input("url", "pathname")]  # Assuming you have dcc.Location(id="url") in your app layout
)
def toggle_date_range_container(pathname):
    # Define paths where the date range container should be shown
    show_on_paths = ["/prices", "/compare"]  # Adjust paths as needed

    if pathname in show_on_paths:
        return {'display': 'block'}
    else:
        return {'display': 'none'}



app.clientside_callback(
    """
    function(n_clicks, is_open, current_class) {
        if (n_clicks) {
            is_open = !is_open;
            if (is_open) {
                // Show the "X" close icon when the navbar is open
                return [is_open, "order-2 me-3 toggler-icon open"];
            } else {
                // Show the hamburger icon when the navbar is closed
                return [is_open, "order-2 me-3 toggler-icon"];
            }
        }
        return [is_open, current_class];
    }
    """,
    [Output("navbar-collapse", "is_open"),
     Output("navbar-toggler", "className")],
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open"),
     State("navbar-toggler", "className")]
)


@server.errorhandler(404)
def page_not_found(e):
    # logging.error(f"404 error: {str(e)}")
    return render_template('404.html'), 404

@app.callback(
    [
        Output('page-content', 'children'),
        Output('login-status', 'data', allow_duplicate=True),
        Output('login-username-store', 'data', allow_duplicate=True),
        Output('login-link', 'style'),
        Output('logout-button', 'style'),
        Output('profile-link', 'style'),
        Output('register-link', 'style'),
        Output('sticky-footer-container', 'style')
    ],
    [Input('url', 'pathname')],
    prevent_initial_call=True
)
def display_page_and_update_ui(pathname):
    ctx = dash.callback_context

    # Avoid triggering callback if non-existent elements are referenced
    if not ctx.triggered:
        raise PreventUpdate

    # Get session info
    logged_in = session.get('logged_in', False)
    username = session.get('username', None)
    footer_style = {"display": "block"}  # Default to showing the footer

    # Initialize subscription status
    is_free_user = False
    is_premium_user = False

    # Default layout for non-logged-in users
    layout_values = {
        "login-link": {"display": "block"},
        "logout-button": {"display": "none"},
        "profile-link": {"display": "none"},
        "register-link": {"display": "block"}
    }

    # Adjust layout if the user is logged in
    if logged_in and username:
        user = User.query.filter_by(username=username).first()  # Fetch user info
        if user:
            is_free_user = user.subscription_status == 'free'
            is_premium_user = user.subscription_status == 'premium'

        # Show/hide links based on subscription type
        layout_values = {
            "login-link": {"display": "none"},
            "logout-button": {"display": "block"},
            "profile-link": {"display": "block"},
            "register-link": {"display": "block"} if is_free_user else {"display": "none"}
        }

    # Pages where the footer should be hidden
    pages_without_footer = ['/about', '/login', '/register', '/profile', '/forgot-password',
                            '/subscription', '/register-free', '/register-paid', '/blog', '/demo', '/']
    if pathname in pages_without_footer:
        footer_style = {"display": "none"}

    # Return layout based on the path and login state
    if pathname == '/':
        return homepage_layout, logged_in, username, layout_values['login-link'], layout_values['logout-button'], layout_values['profile-link'], layout_values['register-link'], footer_style


    elif pathname in ['/about', '/demo']:
        return about_layout, logged_in, username, layout_values['login-link'], layout_values['logout-button'], layout_values['profile-link'], layout_values['register-link'], footer_style
    elif pathname == '/faqs':
        return faq_layout, logged_in, username, layout_values['login-link'], layout_values['logout-button'], layout_values['profile-link'], layout_values['register-link'], footer_style
    elif pathname == '/blog':
        return blog_layout, logged_in, username, layout_values['login-link'], layout_values['logout-button'], layout_values['profile-link'], layout_values['register-link'], footer_style
    elif pathname in ['/register', '/subscription']:
        return create_subscription_selection_layout(is_free_user), logged_in, username, layout_values['login-link'], layout_values['logout-button'], layout_values['profile-link'], layout_values['register-link'], {"display": "none"}
    elif pathname == '/register-free':
        return create_register_layout('free'), logged_in, username, layout_values['login-link'], layout_values['logout-button'], layout_values['profile-link'], layout_values['register-link'], footer_style
    elif pathname == '/register-paid':
        return create_register_layout('premium'), logged_in, username, layout_values['login-link'], layout_values['logout-button'], layout_values['profile-link'], layout_values['register-link'], footer_style
    elif pathname == '/login' and not logged_in:
        return login_layout, logged_in, username, layout_values['login-link'], layout_values['logout-button'], layout_values['profile-link'], layout_values['register-link'], {"display": "none"}
    elif pathname == '/profile' and logged_in:
        return profile_layout, logged_in, username, layout_values['login-link'], layout_values['logout-button'], layout_values['profile-link'], layout_values['register-link'], footer_style
    elif pathname == '/forgot-password':
        return forgot_layout, logged_in, username, layout_values['login-link'], layout_values['logout-button'], layout_values['profile-link'], layout_values['register-link'], footer_style
    elif pathname  in ['/prices', '/forecast', '/compare', '/news', '/recommendations', '/simulation', '/hotstocks']:
        return dashboard_layout, logged_in, username, layout_values['login-link'], layout_values['logout-button'], layout_values['profile-link'], layout_values['register-link'], footer_style

    # Default to dashboard if no specific path matches
    return homepage_layout, logged_in, username, layout_values['login-link'], layout_values['logout-button'], layout_values['profile-link'], layout_values['register-link'], footer_style


            
app.clientside_callback(
    """
    function(value) {
        return value;
    }
    """,
    Output('active-tab', 'data'),
    Input('tabs', 'value')
)



app.clientside_callback(
    """
    function(n_intervals, n_clicks, login_status, modal_shown, is_open) {
        // Show modal after 30 seconds if not logged in and modal hasn't been shown yet
        if (n_intervals > 0 && !login_status && !modal_shown) {
            return true;  // Open the modal
        }
        
        // Close modal when "Register" button is clicked
        if (n_clicks) {
            return false;  // Close the modal
        }
        
        // Keep modal open or closed based on current state
        return is_open;
    }
    """,
    Output('register-modal', 'is_open'),
    [Input('register-modal-timer', 'n_intervals'),
     Input('close-register-modal-button', 'n_clicks')],
    [State('login-status', 'data'),
     State('modal-shown-store', 'data'),
     State('register-modal', 'is_open')]
)

app.clientside_callback(
    """
    function(is_open, modal_shown) {
        if (is_open && !modal_shown) {
            return true;  // Mark that the modal has been shown
        }
        return modal_shown;  // Keep the current state
    }
    """,
    Output('modal-shown-store', 'data'),
    [Input('register-modal', 'is_open')],
    [State('modal-shown-store', 'data')]
)


from dash.dependencies import Input, Output, State


@app.callback(
    [
        Output('new-watchlist-name', 'disabled'),
        Output('saved-watchlists-dropdown', 'disabled'),
        Output('saved-watchlists-dropdown', 'clearable'),
        Output('create-watchlist-button', 'disabled'),
        Output('delete-watchlist-button', 'disabled'),
        Output('create-watchlist-button', 'className'),
        Output('delete-watchlist-button', 'className')
    ],
    [
        Input('login-status', 'data'),
        Input('saved-watchlists-dropdown', 'value')  # Check selected watchlist
    ]
)
def update_watchlist_management_layout(login_status, selected_watchlist_id):
    if login_status:
        delete_button_disabled = selected_watchlist_id is None  # Disable delete button if no watchlist is selected
        return (
            False,  # Enable new watchlist name input
            False,  # Enable saved watchlists dropdown
            True,   # Make dropdown clearable
            False,  # Enable create watchlist button
            delete_button_disabled,  # Conditionally disable delete button
            "small-button",  # Class for create button
            "small-button"   # Class for delete button
        )
    else:
        return (
            True,  # Disable new watchlist name input
            True,  # Disable saved watchlists dropdown
            True,  # Make dropdown clearable (irrelevant when disabled)
            True,  # Disable create watchlist button
            True,  # Disable delete button
            dash.no_update,  # No update to create button class
            dash.no_update   # No update to delete button class
        )



app.clientside_callback(
    """
    function(click_n_clicks, login_status, is_overlay_open) {
        // Initialize click_n_clicks to avoid NoneType error
        click_n_clicks = click_n_clicks || 0;

        // If not logged in and the area is clicked, show the overlay
        if (!login_status && click_n_clicks > 0) {
            return true;
        }

        // Keep the overlay open if it’s already open
        if (is_overlay_open) {
            return true;
        }

        // Otherwise, don't show the overlay
        return false;
    }
    """,
    Output('login-overlay', 'is_open'),
    [Input('clickable-watchlist-area', 'n_clicks')],
    [State('login-status', 'data'),
     State('login-overlay', 'is_open')]
)



@app.callback(
    [Output('recommendation-blur-overlay', 'children'),
     Output('recommendation-blur-overlay', 'style')],
    [Input('login-status', 'data'),
     Input('login-username-store', 'data')]
)
def update_recommendation_visibility(login_status, username):
    if not login_status or not username:
        # Case: User is logged out, show the 'logged out' paywall
        paywall = ly.paywall_recommendation()
        blur_style = {
            'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%',
            'background-color': 'rgba(255, 255, 255, 0.5)', 'display': 'flex',
            'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
            'backdrop-filter': 'blur(2px)'
        }
        return paywall, blur_style

    # Case: User is logged in, fetch user from the database
    user = User.query.filter_by(username=username).first()

    if user and user.subscription_status == 'free':
        # Case: Premium user, no paywall and no blur
        blur_style = {'display': 'none'}
        return '', blur_style

    elif user and user.subscription_status == 'premium':
        # Case: Premium user, no paywall and no blur
        blur_style = {'display': 'none'}
        return '', blur_style

    # Fallback: Treat as logged-out if user role is undefined
    paywall = ly.paywall_recommendation()
    blur_style = {
        'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%',
        'background-color': 'rgba(255, 255, 255, 0.5)', 'display': 'flex',
        'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
        'backdrop-filter': 'blur(2px)'
    }
    return paywall, blur_style




@app.callback(
    [Output('topshots-blur-overlay', 'children'),
     Output('topshots-blur-overlay', 'style')],
    [Input('login-status', 'data'),
     Input('login-username-store', 'data')]
)
def update_topshots_visibility(login_status, username):
    if not login_status or not username:
        # Case: User is logged out, show the 'logged out' paywall
        paywall = ly.paywall_logged_out()
        blur_style = {
            'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%',
            'background-color': 'rgba(255, 255, 255, 0.5)', 'display': 'flex',
            'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
            'backdrop-filter': 'blur(2px)'
        }
        return paywall, blur_style

    # Case: User is logged in, fetch user from the database
    user = User.query.filter_by(username=username).first()

    if user and user.subscription_status == 'free':
        # Case: Free user, show the 'free user' paywall
        paywall = ly.paywall_free_user()
        blur_style = {
            'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%',
            'background-color': 'rgba(255, 255, 255, 0.5)', 'display': 'flex',
            'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
            'backdrop-filter': 'blur(2px)'
        }
        return paywall, blur_style

    elif user and user.subscription_status == 'premium':
        # Case: Premium user, no paywall and no blur
        blur_style = {'display': 'none'}
        return '', blur_style

    # Fallback: Treat as logged-out if user role is undefined
    paywall = ly.paywall_logged_out()
    blur_style = {
        'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%',
        'background-color': 'rgba(255, 255, 255, 0.5)', 'display': 'flex',
        'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
        'backdrop-filter': 'blur(2px)'
    }
    return paywall, blur_style



# Register the callback for toggling the watchlist summary with burger icon logic
app.clientside_callback(
    """
    function(n_clicks, is_open, button_class) {
        var isMobile = window.innerWidth < 768;

        if (isMobile) {
            if (n_clicks) {
                var new_is_open = !is_open;

                // Toggle the button class between hamburger and "X" icon
                if (new_is_open) {
                    button_class = "mobile-only toggler-icon open";  // Add the "open" class
                } else {
                    button_class = "mobile-only toggler-icon";  // Remove the "open" class
                }

                return [new_is_open, button_class];
            }
            return [is_open, button_class];
        }
        return [true, button_class];  // Always open on desktop
    }
    """,
    [Output('watchlist-collapse', 'is_open'),
     Output('toggle-watchlist-button', 'className')],
    [Input('toggle-watchlist-button', 'n_clicks')],
    [State('watchlist-collapse', 'is_open'),
     State('toggle-watchlist-button', 'className')]
)



                
@server.route('/')
def index():
    if 'forecast_attempts' not in session:
        session['forecast_attempts'] = 0  # Initialize the attempt count in Flask session
    return render_template('index.html')  # Or the Dash app



@app.callback(
    [Output('forecast-blur-overlay', 'children'),
     Output('forecast-blur-overlay', 'style')],
    [Input('login-status', 'data'),
     Input('login-username-store', 'data'),
     Input('forecast-attempt-store', 'data')],
    prevent_initial_call=True
)
def update_forecast_visibility(login_status, username, forecast_attempt):
    blur_style = {'display': 'none'}  # Default: hide the overlay

    # Case 1: Logged-out user or session-based (no username)
    if not login_status or not username:
        forecast_attempt = forecast_attempt or 0
        print(f"Logged-out user attempt count: {forecast_attempt}")

        # Show paywall for logged-out users after 2 attempts
        if forecast_attempt >= 2:
            print("Triggering paywall for logged-out user")
            paywall = ly.paywall_logged_out_forecast()
            blur_style.update({
                'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%',
                'background-color': 'rgba(255, 255, 255, 0.3)', 'display': 'flex',
                'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
                'backdrop-filter': 'blur(2px)'
            })
            return paywall, blur_style
        else:
            return '', blur_style  # No overlay if attempts are under the limit

    # Case 2: Logged-in user
    user = User.query.filter_by(username=username).first()
    if user and user.subscription_status == 'free':
        print(f"Logged-in free user attempt count: {user.forecast_attempts}")
        # Show paywall for free users after 2 attempts
        if user.forecast_attempts >= 2:
            print("Triggering paywall for free logged-in user")
            paywall = ly.paywall_free_user_forecast()
            blur_style.update({
                'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%',
                'background-color': 'rgba(255, 255, 255, 0.3)', 'display': 'flex',
                'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
                'backdrop-filter': 'blur(2px)'
            })
            return paywall, blur_style
        else:
            return '', blur_style  # No overlay if attempts are under the limit

    # Case 3: Premium user (no overlay required)
    elif user and user.subscription_status == 'premium':
        print("Premium user - no overlay")
        return dash.no_update, {'display': 'none'}

    # Fallback: Treat as logged-out if user role is undefined
    print("Fallback case - triggering logged-out paywall")
    paywall = ly.paywall_logged_out_forecast()
    blur_style.update({
        'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%',
        'background-color': 'rgba(255, 255, 255, 0.3)', 'display': 'flex',
        'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
        'backdrop-filter': 'blur(2px)'
    })
    return paywall, blur_style


            
          
@app.callback(
    [Output('profile-username', 'value'),
      Output('profile-email', 'value'),
      Output('profile-subscription', 'children')],
    [Input('url', 'pathname')],
    [State('login-status', 'data'),
      State('login-username-store', 'data')]
)
def display_profile(pathname, login_status, username):
    if pathname == '/profile':
        if login_status and username:
            user = User.query.filter_by(username=username).first()
            if user:
                subscription_status = user.subscription_status.title() if user.subscription_status else "free"
                return user.username, user.email, subscription_status
        return dash.no_update, dash.no_update, dash.no_update
    raise PreventUpdate


@app.callback(
    [
        Output('profile-username', 'disabled'),
        Output('profile-email', 'disabled'),
        Output('profile-current-password', 'disabled'),
        Output('profile-password', 'disabled'),
        Output('profile-confirm-password', 'disabled'),
        Output('edit-profile-button', 'style'),
        Output('save-profile-button', 'style'),
        Output('cancel-edit-button', 'style'),
        Output('profile-req-length', 'style'),
        Output('profile-req-uppercase', 'style'),
        Output('profile-req-lowercase', 'style'),
        Output('profile-req-digit', 'style'),
        # Removed special character requirement
        Output('toggle-password-fields', 'style'),
        Output('password-fields-container', 'style'),
        Output('profile-output', 'children')
    ],
    [
        Input('edit-profile-button', 'n_clicks'),
        Input('save-profile-button', 'n_clicks'),
        Input('cancel-edit-button', 'n_clicks'),
        Input('toggle-password-fields', 'n_clicks')
    ],
    [
        State('profile-username', 'value'),
        State('profile-email', 'value'),
        State('profile-current-password', 'value'),
        State('profile-password', 'value'),
        State('profile-confirm-password', 'value'),
        State('login-username-store', 'data')
    ],
    prevent_initial_call=True
)
def handle_profile_actions(edit_clicks, save_clicks, cancel_clicks, toggle_pw_clicks, 
                            username, email, current_password, new_password, confirm_password, current_username):

    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'edit-profile-button':
        return (False, True, True, True, True,  # Disable email
                {"display": "none"},  # Hide Edit button
                {"display": "inline-block"},  # Show Save button
                {"display": "inline-block"},  # Show Cancel button
                {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"},  # Show requirements
                {"display": "inline-block"},  # Show Change Password button
                {"display": "none"},  # Hide password fields by default
                "")

    elif triggered_id == 'save-profile-button':
        # Handle validation and saving logic
        if not username or not email:
            return (False, True, True, True, True,  # Disable email
                    {"display": "inline-block"},  # Show Edit button
                    {"display": "none"},  # Hide Save button
                    {"display": "none"},  # Hide Cancel button
                    {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"},  # Hide requirements
                    {"display": "none"},  # Hide Change Password button
                    {"display": "none"},  # Hide password fields
                    dbc.Alert("Username and Email are required.", color="danger"))

        user = User.query.filter_by(username=current_username).first()
        if user and not bcrypt.check_password_hash(user.password, current_password):
            return (False, True, True, True, True,
                    {"display": "none"}, {"display": "inline-block"}, {"display": "inline-block"},
                    {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"},
                    {"display": "inline-block"}, {"display": "none"},
                    dbc.Alert("Current password is incorrect.", color="danger"))

        if new_password and new_password != confirm_password:
            return (False, True, True, True, True,
                    {"display": "none"}, {"display": "inline-block"}, {"display": "inline-block"},
                    {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"},
                    {"display": "inline-block"}, {"display": "none"},
                    dbc.Alert("New passwords do not match.", color="danger"))

        if new_password:
            password_error = ut.validate_password(new_password)
            if password_error:
                return (False, True, True, True, True,
                        {"display": "none"}, {"display": "inline-block"}, {"display": "inline-block"},
                        {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"},
                        {"display": "inline-block"}, {"display": "none"},
                        dbc.Alert(password_error, color="danger"))

        # Save updated user details
        if user:
            user.username = username
            user.email = email
            if new_password:
                user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            db.session.commit()
            session['username'] = username
            return (True, True, True, True, True,
                    {"display": "inline-block"}, {"display": "none"}, {"display": "none"},
                    {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}, 
                    {"display": "none"}, {"display": "none"},
                    dbc.Alert("Profile updated successfully!", color="success"))

    elif triggered_id == 'cancel-edit-button':
        return (True, True, True, True, True,
                {"display": "inline-block"}, {"display": "none"}, {"display": "none"},
                {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}, 
                {"display": "none"}, {"display": "none"}, "")

    elif triggered_id == 'toggle-password-fields':
        if toggle_pw_clicks % 2 == 1:
            return (False, True, True, False, False,  # Enable password fields
                    {"display": "none"}, {"display": "inline-block"}, {"display": "inline-block"},
                    {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"},  # Show requirements
                    {"display": "inline-block"}, {"display": "block"},  # Show password fields
                    "")
        return (False, True, True, True, True,  # Disable password fields
                {"display": "none"}, {"display": "inline-block"}, {"display": "inline-block"},
                {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"},  # Show requirements
                {"display": "inline-block"}, {"display": "none"},  # Hide password fields
                "")

    raise PreventUpdate




@app.callback(
    Output("cancel-subscription-modal", "is_open"),
    [Input("cancel-subscription-btn", "n_clicks"),
     Input("close-cancel-modal-btn", "n_clicks"),
     Input("confirm-cancel-btn", "n_clicks")],
    [State("cancel-subscription-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_cancel_modal(open_click, close_click, confirm_click, is_open):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Open the modal when the user clicks the Cancel Subscription button
    if triggered_id == "cancel-subscription-btn":
        return not is_open
    
    # Close the modal when the user clicks the "No" button
    elif triggered_id == "close-cancel-modal-btn":
        return False

    # If "Yes" is confirmed, trigger the cancellation
    elif triggered_id == "confirm-cancel-btn":
        return False  # Close modal after confirmation
    
    return is_open



@app.callback(
    Output('cancel-subscription-btn', 'style'),
    [Input('url', 'pathname')],
    [State('login-username-store', 'data')]
)
def toggle_cancel_subscription_button(pathname, username):
    if pathname == '/profile' and username:
        user = User.query.filter_by(username=username).first()
        if user and user.subscription_status == 'premium':
            return {"display": "block"}  # Show the button for premium users
        else:
            return {"display": "none"}  # Hide the button for free or inactive users
    return {"display": "none"}  # Default to hidden if not on profile page


@app.callback(
    Output('subscription-status', 'children'),
    Input('confirm-cancel-btn', 'n_clicks'),
    prevent_initial_call=True
)
def cancel_subscription(n_clicks):
    if n_clicks:
        return dcc.Location(href='/cancel-subscription', id='redirect')
    raise PreventUpdate



@app.callback(
    Output('stock-suggestions-input', 'options'),
    Input('stock-suggestions-input', 'search_value')  # Triggers as the user types
)
def update_stock_suggestions(company_name):
    if not company_name:
        raise PreventUpdate

    try:
        # Get a list of ticker suggestions (multiple tickers)
        tickers = ut.get_ticker(company_name)
        
        # Format the suggestions for dcc.Dropdown
        if tickers:
            return [{'label': f"{ticker} ({company_name.title()})", 'value': ticker} for ticker in tickers]
        else:
            # No tickers found
            return [{'label': 'No matching stocks found', 'value': ''}]
    
    except Exception as e:
        # Handle cases where the API request fails or other issues
        return [{'label': 'Error retrieving stock suggestions', 'value': ''}]


@app.callback(
    [Output('theme-store', 'data'),
     Output('plotly-theme-store', 'data')],
    [Input(f'theme-{theme}', 'n_clicks') for theme in themes.keys()],
    [State('login-status', 'data'),
     State('login-username-store', 'data')]
)
def update_theme(*args, login_status=None, username=None):
    ctx = dash.callback_context

    if ctx.triggered:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        theme = button_id.split('-')[1]
        print(f"Selected theme: {theme}")
        print(f"DBC Theme: {themes[theme]['dbc']}, Plotly Theme: {themes[theme]['plotly']}")
        return themes[theme]['dbc'], themes[theme]['plotly']

    if login_status and username:
        user = User.query.filter_by(username=username).first()
        if user and user.theme:
            print(f"User's saved theme: {user.theme}")
            return themes[user.theme]['dbc'], themes[user.theme]['plotly']

    print("Using default theme")
    return dbc.themes.SPACELAB, 'plotly_white'



@app.callback(
    Output('theme-switch', 'href'),
    Input('theme-store', 'data')
)
def update_stylesheet(theme):
    return theme


app.clientside_callback(
    """
    function(n_clicks) {
        return window.dash_clientside.clientside.toggleFullScreen(n_clicks);
    }
    """,
    Output("trigger-fullscreen", "data"),
    [Input("fullscreen-button", "n_clicks")]
)


app.index_string = '''
<!DOCTYPE html>
<html lang="en">
    <head>
        {%metas%}
        <title>Stocks Dashboard, Save Your Watchlist Today - WatchMyStocks</title>
        
        <!-- Preload styles and favicon -->
        <link rel="preload" href="https://raw.githubusercontent.com/diggejos/mystocks/1f733f3776983b8fb277f7347c7d784686d36b4d/assets/styles.css" as="style">
        <link rel="stylesheet" href="https://raw.githubusercontent.com/diggejos/mystocks/1f733f3776983b8fb277f7347c7d784686d36b4d/assets/styles.css?v=1.0">
        <link rel="preload" href="https://cdn.jsdelivr.net/.../bootstrap.min.css" as="style">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/.../bootstrap.min.css">
        <link rel="icon" href="https://raw.githubusercontent.com/diggejos/mystocks/1f733f3776983b8fb277f7347c7d784686d36b4d/assets/logo_with_transparent_background_favicon.png" type="image/png">
        
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="description" content="Track and forecast your favorite stocks, visualize trends, get stock recommendations, and chat with an AI financial advisor. Save your watchlist today!">
        <meta name="keywords" content="stock, stocks, stocks dashboard, finance, stocks forecasting, stocks news, stocks monitoring, stocks recommendations, finance, financial advisor, watchlist, watchmystocks, mystocks, apple stock, microsoft stock">
        <meta name="author" content="WatchMyStocks">
        <link rel="canonical" href="https://mystocksportfolio.io/">
        
        <!-- Structured data for SEO -->
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "url": "https://mystocksportfolio.io/",
            "name": "myStocksPortfolio",
            "description": "Track and forecast stock prices, visualize trends, get stock recommendations, and chat with an AI financial advisor.",
            "publisher": {
                "@type": "Organization",
                "name": "MyStocks"
            }
        }
        </script>

        <!-- Lazy-loaded third-party scripts -->
        <script>
            window.addEventListener('load', function () {
                // Google Tag Manager
                (function(w, d, s, l, i) {
                    w[l] = w[l] || [];
                    w[l].push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' });
                    var f = d.getElementsByTagName(s)[0],
                        j = d.createElement(s),
                        dl = l != 'dataLayer' ? '&l=' + l : '';
                    j.async = true;
                    j.src = 'https://www.googletagmanager.com/gtm.js?id=' + i + dl;
                    f.parentNode.insertBefore(j, f);
                })(window, document, 'script', 'dataLayer', 'GTM-T6SPT9FD');

                // Hotjar
                (function(h, o, t, j, a, r) {
                    h.hj = h.hj || function () { (h.hj.q = h.hj.q || []).push(arguments) };
                    h._hjSettings = { hjid: 5148807, hjsv: 6 };
                    a = o.getElementsByTagName('head')[0];
                    r = o.createElement('script');
                    r.async = 1;
                    r.src = t + h._hjSettings.hjid + j + h._hjSettings.hjsv;
                    a.appendChild(r);
                })(window, document, 'https://static.hotjar.com/c/hotjar-', '.js?sv=');
            });
        </script>

        <!-- Defer Dash scripts -->
        <script defer src="https://cdnjs.cloudflare.com/ajax/libs/dash/1.16.3/dash.min.js"></script>
        <script defer src="https://cdnjs.cloudflare.com/ajax/libs/dash-bootstrap-components/0.10.7/dash_bootstrap_components.min.js"></script>

        {%css%}
        
        <!-- Style adjustments for responsiveness -->
        <style>
            .news-row > .col-md-6 {
                flex: 0 0 50%;
                max-width: 50%;
            }
            @media (max-width: 768px) {
                .news-row > .col-md-6 {
                    flex: 0 0 100%;
                    max-width: 100%;
                }
            }
        </style>
    </head>
    <body>
        <!-- Google Tag Manager (noscript fallback) -->
        <noscript>
            <iframe src="https://www.googletagmanager.com/ns.html?id=GTM-T6SPT9FD"
                height="0" width="0" style="display:none;visibility:hidden"></iframe>
        </noscript>

        {%app_entry%}

        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>

'''

if __name__ == "__main__":
    app.run_server(debug=True)

