import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State, ALL, MATCH
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
from layouts import login_layout, dashboard_layout, about_layout,profile_layout, forgot_layout, subscription_page, create_register_layout,create_subscription_selection_layout
from flask_mail import Mail
import auth_callbacks
from flask import request
import data_callbacks
import stripe
from flask import redirect, url_for
from flask import render_template
import logging


# Initialize the Dash app with a default Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.MATERIA, "https://cdnjs.cloudflare.com/ajax/libs/bootstrap-icons/1.5.0/font/bootstrap-icons.min.css"])
server = app.server

@server.route('/sitemap.xml')
def sitemap_xml():
    return send_from_directory(os.path.join(os.getcwd(), 'static'), 'sitemap.xml')

# load robots.txt file for SEO
@server.route('/robots.txt')
def serve_robots_txt():
       return send_from_directory('static', 'robots.txt')
    

# Define a custom 404 error handler
@server.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

server.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure the session
load_dotenv()
app.server.config['SECRET_KEY'] =  os.getenv('FLASK_SECRET_KEY') # Use a strong, unique secret key
app.server.config['SESSION_TYPE'] = 'filesystem' 

Session(app.server)

# Email configuration
server.config['MAIL_SERVER'] = 'smtp.gmail.com'
server.config['MAIL_PORT'] = 587
server.config['MAIL_USE_TLS'] = True
server.config['MAIL_USERNAME'] = 'mystocks.monitoring@gmail.com'
server.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

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
    dcc.Store(id='conversation-store', data=[]),  # Store to keep the conversation history
    dcc.Store(id='individual-stocks-store', data=['AAPL', 'MSFT']),
    dcc.Store(id='theme-store', data=dbc.themes.MATERIA),
    dcc.Store(id='plotly-theme-store', data='plotly_white'),
    dcc.Store(id='login-status', data=False),  # Store to track login status
    dcc.Store(id='login-username-store', data=None),  # Store to persist the username
    html.Link(id='theme-switch', rel='stylesheet', href=dbc.themes.BOOTSTRAP),
    ly.create_navbar(themes),  # Navbar
    ly.create_overlay(),  # Access Restricted Overlay
    dcc.Location(id='url', refresh=False),
    dbc.Container(id='page-content', fluid=True),
    dcc.Store(id='active-tab', data='📰 News'), 
    dcc.Store(id='forecast-data-store'),
    # dcc.Location(id='url-refresh', refresh=True),
    dcc.Location(id='url-redirect', refresh=True),
    DeferScript(src='assets/script.js'),
    ly.create_floating_chatbot_button(),  # Floating Chatbot Button
    ly.create_chatbot_modal(),  # Chatbot Modal
    ly.create_financials_modal(),  # Financials Modal
    html.Div(ly.create_sticky_footer_mobile(), id="sticky-footer-container"),
    ly.create_footer(),  # Footer
    ly.create_modal_register(),
    dcc.Store(id='device-type', data='desktop')  # Default to desktop

])


auth_callbacks.register_auth_callbacks(app, server, mail)
data_callbacks.get_data_callbacks(app, server)


from flask import Flask, render_template_string




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
            session['username'] = user.username  # Ensure session has the username
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
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user.password = hashed_password
        db.session.commit()

        return render_template('password_reset.html', message="Your password has been reset successfully. You can now ", show_login_link=True)
    else:
        return render_template('password_reset.html', message=None, show_login_link=False)
    
    
# SUBSCRIBER ROUTES---------------------------   

@app.server.route('/create-checkout-session', methods=['POST', 'GET'])
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
            success_url=url_for('subscription_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
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
        # Retrieve the Stripe subscription using the subscription ID from the user model
        if user.stripe_subscription_id:
            try:
                stripe_subscription = stripe.Subscription.retrieve(user.stripe_subscription_id)
            except stripe.error.InvalidRequestError as e:
                logging.error(f"Stripe Error: {str(e)}")
                return "Error: No such subscription found. It might have been canceled already."

            # Check the subscription status before canceling
            if stripe_subscription.status == 'canceled':
                return "Subscription is already canceled."

            # If the subscription is still active or incomplete, proceed to cancel it
            if stripe_subscription.status in ['active', 'incomplete']:
                stripe.Subscription.delete(stripe_subscription.id)

                # Update user's subscription status in your database
                user.subscription_status = 'free'
                user.stripe_subscription_id = None
                db.session.commit()

                # Optionally send the cancellation email here
                ut.send_cancellation_email(user.email, user.username, mail)

                # Redirect with a message after 5 seconds
                return '''
                    <html>
                        <head>
                            <meta http-equiv="refresh" content="5; url=/profile" />
                        </head>
                        <body>
                            <h1>Subscription canceled successfully.</h1>
                            <p>You will be redirected to your profile page in 5 seconds.</p>
                        </body>
                    </html>
                '''
            else:
                return "Subscription status is not eligible for cancellation."
        else:
            return "No Stripe subscription ID found."

    except stripe.error.StripeError as e:
        logging.error(f"Stripe Error: {str(e)}")
        return f"Stripe Error: {str(e)}"

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return f"Error: {str(e)}"


    
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
            logging.info(f"User {user.username} successfully subscribed. Stripe Session: {stripe_session}")

            # Retrieve the Stripe subscription from the session and save it to the user
            stripe_subscription = stripe.Subscription.retrieve(stripe_session['subscription'])
            user.stripe_subscription_id = stripe_subscription.id  # Save the latest subscription ID

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
    [Output('login-status', 'data', allow_duplicate=True),
     Output('login-username-store', 'data', allow_duplicate=True),
     Output('login-link', 'style', allow_duplicate=True),
     Output('logout-button', 'style', allow_duplicate=True),
     Output('profile-link', 'style', allow_duplicate=True),
     Output('register-link', 'style', allow_duplicate=True)],
    [Input('url', 'pathname')],
    prevent_initial_call=True
)
def update_ui_on_page_load(pathname):
    # Get session info
    logged_in = session.get('logged_in', False)
    username = session.get('username', None)

    if logged_in and username:
        return True, username, {"display": "none"}, {"display": "block"}, {"display": "block"}, {"display": "none"}
    else:
        return False, None, {"display": "block"}, {"display": "none"}, {"display": "none"}, {"display": "block"}
    
    

@app.callback(
    [Output('page-content', 'children', allow_duplicate=True),
     Output('sticky-footer-container', 'style', allow_duplicate=True),
     Output('register-link', 'style', allow_duplicate=True),  # Add output for register link visibility
     Output('login-link', 'style', allow_duplicate=True),
     Output('logout-button', 'style', allow_duplicate=True),
     Output('profile-link', 'style', allow_duplicate=True)],
    [Input('url', 'pathname'),
     Input('login-status', 'data'),
     Input('login-username-store', 'data')
     ],
    prevent_initial_call=True
)
def display_page(pathname, login_status, username):
    user = User.query.filter_by(username=username).first() if username else None
    is_free_user = user and user.subscription_status == 'free'

    # Pages where the footer should be hidden
    pages_without_footer = ['/about', '/login', '/register', '/profile', '/forgot-password', '/subscription', '/register-free', '/register-paid']
    footer_style = {"display": "block"} if pathname not in pages_without_footer else {"display": "none"}

    # Determine navbar visibility
    if login_status and user:
        # If logged in, adjust navbar based on subscription status
        if user.subscription_status == 'premium':
            return_layout = (dashboard_layout, footer_style, 
                             {"display": "none"},  # Hide sign-up link for premium users
                             {"display": "none"},  # Hide login link
                             {"display": "block"},  # Show logout button
                             {"display": "block"})  # Show profile link
        elif user.subscription_status == 'free':
            return_layout = (dashboard_layout, footer_style,
                             {"display": "block"},  # Show sign-up link for free users
                             {"display": "none"},  # Hide login link
                             {"display": "block"},  # Show logout button
                             {"display": "block"})  # Show profile link
    else:
        # If not logged in, show the default login/register links
        return_layout = (dashboard_layout, footer_style,
                         {"display": "block"},  # Show sign-up link
                         {"display": "block"},  # Show login link
                         {"display": "none"},  # Hide logout button
                         {"display": "none"})  # Hide profile link

    # About page
    if pathname == '/about':
        return about_layout, footer_style, return_layout[2], return_layout[3], return_layout[4], return_layout[5]

    # Subscription page
    elif pathname == '/register' or pathname == '/subscription':
        return create_subscription_selection_layout(is_free_user=is_free_user), footer_style, return_layout[2], return_layout[3], return_layout[4], return_layout[5]

    # Free registration page (grey out if already free)
    elif pathname == '/register-free':
        return create_register_layout('free'), footer_style, return_layout[2], return_layout[3], return_layout[4], return_layout[5]

    # Paid registration page
    elif pathname == '/register-paid':
        return create_register_layout('premium'), footer_style, return_layout[2], return_layout[3], return_layout[4], return_layout[5]

    # Login page
    elif pathname == '/login' and not login_status:
        return login_layout, footer_style, return_layout[2], return_layout[3], return_layout[4], return_layout[5]

    # Profile page
    elif pathname == '/profile' and login_status:
        return profile_layout, footer_style, return_layout[2], return_layout[3], return_layout[4], return_layout[5]

    # Forgot Password page
    elif pathname == '/forgot-password':
        return forgot_layout, footer_style, return_layout[2], return_layout[3], return_layout[4], return_layout[5]

    # Default to dashboard
    else:
        return return_layout


@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")]
)
def toggle_navbar(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open



# Add a callback to update the active-tab store
@app.callback(
    Output('active-tab', 'data'),
    Input('tabs', 'value')
)
def update_active_tab(value):
    return value


@app.callback(
    Output('register-modal', 'is_open'),
    [Input('register-modal-timer', 'n_intervals'),
     Input('close-register-modal-button', 'n_clicks')],
    [State('login-status', 'data'),
     State('modal-shown-store', 'data'),
     State('register-modal', 'is_open')],
    prevent_initial_call=True
)
def control_modal(n_intervals, n_clicks, login_status, modal_shown, is_open):
    # Show modal after 30 seconds if not logged in and modal hasn't been shown yet
    if n_intervals > 0 and not login_status and not modal_shown:
        return True  # Open the modal
    
    # Close modal when "Register" button is clicked
    if n_clicks:
        return False  # Close the modal
    
    # Keep modal open or closed based on current state
    return is_open


@app.callback(
    Output('modal-shown-store', 'data'),
    [Input('register-modal', 'is_open')],
    [State('modal-shown-store', 'data')]
)
def update_modal_shown(is_open, modal_shown):
    if is_open and not modal_shown:
        return True  # Mark that the modal has been shown
    return modal_shown  # Keep the current state



@app.callback(
    Output('login-overlay', 'is_open'),
    [Input('theme-dropdown-wrapper', 'n_clicks'),
     Input('create-watchlist-button', 'n_clicks'),
     Input('delete-watchlist-button', 'n_clicks')],
    [State('login-status', 'data'),
     State('login-overlay', 'is_open')]
 )
def show_overlay_if_logged_out(theme_n_clicks, create_n_clicks, delete_n_clicks, login_status, is_overlay_open):
        logging.info(
            f"Login status: {login_status}, theme_n_clicks: {theme_n_clicks}, create_n_clicks: {create_n_clicks}, delete_n_clicks: {delete_n_clicks}")
        theme_n_clicks = theme_n_clicks or 0
        create_n_clicks = create_n_clicks or 0
        delete_n_clicks = delete_n_clicks or 0

        if not login_status and (theme_n_clicks > 0 or create_n_clicks > 0 or delete_n_clicks > 0):
            logging.info("Showing overlay")
            return True

        if is_overlay_open:
            logging.info("Overlay already open")
            return True

        logging.info("Overlay not shown")
        return False


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
            'background-color': 'rgba(255, 255, 255, 0.8)', 'display': 'flex',
            'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
            'backdrop-filter': 'blur(5px)'
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
        'background-color': 'rgba(255, 255, 255, 0.8)', 'display': 'flex',
        'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
        'backdrop-filter': 'blur(5px)'
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
            'background-color': 'rgba(255, 255, 255, 0.8)', 'display': 'flex',
            'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
            'backdrop-filter': 'blur(5px)'
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
        'background-color': 'rgba(255, 255, 255, 0.8)', 'display': 'flex',
        'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
        'backdrop-filter': 'blur(5px)'
    }
    return paywall, blur_style




@app.callback(
    [Output('forecast-stock-input', 'options'),
      Output('simulation-stock-input', 'options')],
    Input('individual-stocks-store', 'data')
)
def update_forecast_simulation_dropdown(individual_stocks):
    if not individual_stocks:
        return [], []
    
    options = [{'label': stock, 'value': stock} for stock in individual_stocks]
    return options, options




@app.callback(
    [Output('filters-collapse', 'is_open'),
     Output('mobile-overlay', 'style'),
     Output('toggle-filters-button', 'children')],
    [Input('toggle-filters-button', 'n_clicks')],
    [State('filters-collapse', 'is_open')]
)
def toggle_sidebar(n_clicks, is_open):
    if n_clicks:
        # Toggle the sidebar and the overlay
        new_is_open = not is_open
        overlay_style = {"display": "block"} if new_is_open else {"display": "none"}
        
        # Update the emoji depending on the open/closed state
        emoji = "🔼" if new_is_open else "🔽"
        button_text = html.Span([
            f"{emoji} Stock ",
            html.Span("Selection", className="bg-primary text-white rounded px-2 fs-5")
        ], className="fs-5")

        return new_is_open, overlay_style, button_text

    # If no clicks yet, keep default values
    return is_open, {"display": "none"}, html.Span([
        "🔽 Stock ",
        html.Span("Selection", className="bg-primary text-white rounded px-2 fs-5")
    ], className="fs-5")



@app.callback(
    [Output('tabs', 'active_tab', allow_duplicate=True),  # Allow duplicates for multiple clicks
     Output('footer-news-tab', 'className'),
     Output('footer-prices-tab', 'className'),
     Output('footer-compare-tab', 'className'),
     Output('footer-forecast-tab', 'className'),
     Output('footer-simulate-tab', 'className'),
     Output('footer-recommendations-tab', 'className'),
     Output('footer-topshots-tab', 'className')],
    [Input('footer-news-tab', 'n_clicks'),
     Input('footer-prices-tab', 'n_clicks'),
     Input('footer-compare-tab', 'n_clicks'),
     Input('footer-forecast-tab', 'n_clicks'),
     Input('footer-simulate-tab', 'n_clicks'),
     Input('footer-recommendations-tab', 'n_clicks'),
     Input('footer-topshots-tab', 'n_clicks')],
    [State('tabs', 'active_tab'),
     State('device-type', 'data')]  ,# Add the device-type state
    prevent_initial_call=True
)
def switch_tabs_footer_to_tabs(n_clicks_footer_news, n_clicks_footer_prices, n_clicks_footer_compare,
                               n_clicks_footer_forecast, n_clicks_footer_simulate, 
                               n_clicks_footer_recommendations, n_clicks_footer_topshots, 
                               current_tab, device_type):
    ctx = dash.callback_context
    active_class = 'footer-tab active'
    inactive_class = 'footer-tab'

    # Check if we're on mobile
    if device_type == 'mobile':
        # On mobile, don't try to update the tabs component, as it doesn't exist
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if triggered_id == 'footer-news-tab':
            return dash.no_update, active_class, inactive_class, inactive_class, inactive_class, inactive_class, inactive_class, inactive_class
        elif triggered_id == 'footer-prices-tab':
            return dash.no_update, inactive_class, active_class, inactive_class, inactive_class, inactive_class, inactive_class, inactive_class
        elif triggered_id == 'footer-compare-tab':
            return dash.no_update, inactive_class, inactive_class, active_class, inactive_class, inactive_class, inactive_class, inactive_class
        elif triggered_id == 'footer-forecast-tab':
            return dash.no_update, inactive_class, inactive_class, inactive_class, active_class, inactive_class, inactive_class, inactive_class
        elif triggered_id == 'footer-simulate-tab':
            return dash.no_update, inactive_class, inactive_class, inactive_class, inactive_class, active_class, inactive_class, inactive_class
        elif triggered_id == 'footer-recommendations-tab':
            return dash.no_update, inactive_class, inactive_class, inactive_class, inactive_class, inactive_class, active_class, inactive_class
        elif triggered_id == 'footer-topshots-tab':
            return dash.no_update, inactive_class, inactive_class, inactive_class, inactive_class, inactive_class, inactive_class, active_class

        # Default return in case nothing is triggered
        return dash.no_update, inactive_class, inactive_class, inactive_class, inactive_class, inactive_class, inactive_class, inactive_class

    # We're on desktop, so we can update the 'tabs' component
    if ctx.triggered:
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if triggered_id == 'footer-news-tab':
            return 'news-tab', active_class, inactive_class, inactive_class, inactive_class, inactive_class, inactive_class, inactive_class
        elif triggered_id == 'footer-prices-tab':
            return 'prices-tab', inactive_class, active_class, inactive_class, inactive_class, inactive_class, inactive_class, inactive_class
        elif triggered_id == 'footer-compare-tab':
            return 'compare-tab', inactive_class, inactive_class, active_class, inactive_class, inactive_class, inactive_class, inactive_class
        elif triggered_id == 'footer-forecast-tab':
            return 'forecast-tab', inactive_class, inactive_class, inactive_class, active_class, inactive_class, inactive_class, inactive_class
        elif triggered_id == 'footer-simulate-tab':
            return 'simulate-tab', inactive_class, inactive_class, inactive_class, inactive_class, active_class, inactive_class, inactive_class
        elif triggered_id == 'footer-recommendations-tab':
            return 'recommendations-tab', inactive_class, inactive_class, inactive_class, inactive_class, inactive_class, active_class, inactive_class
        elif triggered_id == 'footer-topshots-tab':
            return 'topshots-tab', inactive_class, inactive_class, inactive_class, inactive_class, inactive_class, inactive_class, active_class

    # Default return if nothing is triggered
    return dash.no_update, inactive_class, inactive_class, inactive_class, inactive_class, inactive_class, inactive_class, inactive_class



@app.callback(
    [Output('forecast-blur-overlay', 'children'),
     Output('forecast-blur-overlay', 'style')],
    [Input('login-status', 'data'),
     Input('login-username-store', 'data')]
)
def update_forecast_visibility(login_status, username):
    if not login_status or not username:
        # Case: User is logged out, show the 'logged out' paywall
        paywall = ly.paywall_logged_out_forecast()
        blur_style = {
            'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%',
            'background-color': 'rgba(255, 255, 255, 0.8)', 'display': 'flex',
            'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
            'backdrop-filter': 'blur(5px)'
        }
        return paywall, blur_style

    # Case: User is logged in, fetch user from the database
    user = User.query.filter_by(username=username).first()

    if user and user.subscription_status == 'free':
        # Case: Free user, show the 'free user' paywall
        paywall = ly.paywall_free_user_forecast()
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
    paywall = ly.paywall_logged_out_forecast()
    blur_style = {
        'position': 'absolute', 'top': 0, 'left': 0, 'width': '100%', 'height': '100%',
        'background-color': 'rgba(255, 255, 255, 0.8)', 'display': 'flex',
        'justify-content': 'center', 'align-items': 'center', 'z-index': 1000,
        'backdrop-filter': 'blur(5px)'
    }
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
                subscription_status = user.subscription_status.title() if user.subscription_status else "Free"
                return user.username, user.email, subscription_status
        return dash.no_update, dash.no_update, dash.no_update
    raise PreventUpdate


@app.callback(
    [Output('profile-username', 'disabled'),
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
     Output('profile-req-special', 'style'),
     Output('profile-output', 'children')],
    [Input('edit-profile-button', 'n_clicks'),
     Input('save-profile-button', 'n_clicks'),
     Input('cancel-edit-button', 'n_clicks')],
    [State('profile-username', 'value'),
     State('profile-email', 'value'),
     State('profile-current-password', 'value'),
     State('profile-password', 'value'),
     State('profile-confirm-password', 'value'),
     State('login-username-store', 'data')]
)
def handle_profile_actions(edit_clicks, save_clicks, cancel_clicks, username, email, current_password, new_password, confirm_password, current_username):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'edit-profile-button':
        return (False, False, True, True, True, {"display": "none"}, {"display": "inline-block"}, {"display": "inline-block"},
                {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"}, "")

    elif triggered_id == 'save-profile-button':
        if not username or not email:
            return (False, False, True, True, True, {"display": "inline-block"}, {"display": "none"}, {"display": "none"},
                    {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"},
                    dbc.Alert("Username and Email are required.", color="danger"))

        user = User.query.filter_by(username=current_username).first()
        if user and not bcrypt.check_password_hash(user.password, current_password):
            return (False, False, True, True, True, {"display": "none"}, {"display": "inline-block"}, {"display": "inline-block"},
                    {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"},
                    dbc.Alert("Current password is incorrect.", color="danger"))

        if new_password and new_password != confirm_password:
            return (False, False, True, True, True, {"display": "none"}, {"display": "inline-block"}, {"display": "inline-block"},
                    {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"},
                    dbc.Alert("New passwords do not match.", color="danger"))

        if new_password:
            password_error = ut.validate_password(new_password)
            if password_error:
                return (False, False, True, True, True, {"display": "none"}, {"display": "inline-block"}, {"display": "inline-block"},
                        {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"}, {"display": "block"},
                        dbc.Alert(password_error, color="danger"))

        if user:
            user.username = username
            user.email = email
            if new_password:
                user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            db.session.commit()
            session['username'] = username
            return (True, True, True, True, True, {"display": "inline-block"}, {"display": "none"}, {"display": "none"},
                    {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"},
                    dbc.Alert("Profile updated successfully!", color="success"))

    elif triggered_id == 'cancel-edit-button':
        return (True, True, True, True, True, {"display": "inline-block"}, {"display": "none"}, {"display": "none"},
                {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}, {"display": "none"}, "")

    raise PreventUpdate
    
    
@app.callback(
    [Output('profile-username', 'disabled', allow_duplicate=True),
     Output('profile-email', 'disabled', allow_duplicate=True),  # Email stays disabled
     Output('profile-current-password', 'disabled', allow_duplicate=True),
     Output('profile-password', 'disabled', allow_duplicate=True),
     Output('profile-confirm-password', 'disabled', allow_duplicate=True),
     Output('toggle-password-fields', 'style', allow_duplicate=True),  # Control visibility of the Change Password button
     Output('edit-profile-button', 'style', allow_duplicate=True),
     Output('save-profile-button', 'style', allow_duplicate=True),
     Output('cancel-edit-button', 'style', allow_duplicate=True)],
    [Input('edit-profile-button', 'n_clicks'),
     Input('save-profile-button', 'n_clicks'),
     Input('cancel-edit-button', 'n_clicks')],
    [State('profile-username', 'value')],
    prevent_initial_call=True
)
def toggle_edit_mode(edit_clicks, save_clicks, cancel_clicks, username):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'edit-profile-button':
        # Enable fields and show the Change Password button
        return (False, True, True, True, True,  # Keep email disabled
                {"display": "inline-block"},  # Show the Change Password button
                {"display": "none"},  # Hide the Edit button
                {"display": "inline-block"},  # Show the Save button
                {"display": "inline-block"})  # Show the Cancel button
    
    elif triggered_id == 'save-profile-button' or triggered_id == 'cancel-edit-button':
        # Disable fields and hide the Change Password button
        return (True, True, True, True, True,  # Keep email disabled
                {"display": "none"},  # Hide the Change Password button
                {"display": "inline-block"},  # Show the Edit button
                {"display": "none"},  # Hide the Save button
                {"display": "none"})  # Hide the Cancel button

    raise PreventUpdate


@app.callback(
    Output('toggle-password-fields', 'style', allow_duplicate=True),
    [Input('edit-profile-button', 'n_clicks')],
    prevent_initial_call=True
)
def toggle_password_button_visibility(edit_clicks):
    if edit_clicks:
        return {"display": "inline-block"}
    raise PreventUpdate


@app.callback(
    [Output('password-fields-container', 'style',allow_duplicate=True),
     Output('profile-current-password', 'disabled',allow_duplicate=True),
     Output('profile-password', 'disabled',allow_duplicate=True),
     Output('profile-confirm-password', 'disabled',allow_duplicate=True)],
    [Input('toggle-password-fields', 'n_clicks')],
    prevent_initial_call=True
)
def toggle_password_fields(n_clicks):
    if n_clicks % 2 == 1:
        return ({"display": "block"}, False, False, False)
    return ({"display": "none"}, True, True, True)


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



from dash import no_update




@app.callback(
    [Output('new-watchlist-name', 'disabled', allow_duplicate=True),
     Output('saved-watchlists-dropdown', 'disabled', allow_duplicate=True),
     Output('saved-watchlists-dropdown', 'clearable', allow_duplicate=True),  # Control clearable property
     Output('create-watchlist-button', 'disabled', allow_duplicate=True),
     Output('delete-watchlist-button', 'disabled', allow_duplicate=True),
     Output('create-watchlist-button', 'className'),
     Output('delete-watchlist-button', 'className')
     ],
    [Input('login-status', 'data')],
    prevent_initial_call='initial_duplicate'
)
def update_watchlist_management_layout(login_status):
    if login_status:
        return False, False, True, False, False, "small-button", "small-button"  # Enable components and make the dropdown clearable
    else:
        # return True, True, False, True, True  # Disable components and make the dropdown not clearable
        return no_update, no_update,no_update,no_update,no_update,no_update,no_update



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
    [Output('tab-prices', 'className'),
     Output('tab-news', 'className'),
     Output('tab-comparison', 'className'),
     Output('tab-forecast', 'className'),
     Output('tab-simulation', 'className'),
     Output('tab-reccommendation', 'className')],
    [Input('tabs', 'value')]
)
def update_active_tab_class(current_tab):
    # Determine which tab is active and apply the "active" class accordingly
    return [
        "nav-link active" if current_tab == '📰 News' else "nav-link",
        "nav-link active" if current_tab == '📈 Prices' else "nav-link",
        "nav-link active" if current_tab == '⚖️ Compare' else "nav-link",
        "nav-link active" if current_tab == '🌡️ Forecast' else "nav-link",
        "nav-link active" if current_tab == '📊 Simulate' else "nav-link",
        "nav-link active" if current_tab == '❤️ Reccomendations' else "nav-link"
    ]


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
    return dbc.themes.MATERIA, 'plotly_white'



@app.callback(
    Output('theme-switch', 'href'),
    Input('theme-store', 'data')
)
def update_stylesheet(theme):
    return theme



@app.callback(
    Output('plotly-theme-store', 'data',allow_duplicate=True),
    [Input('theme-store', 'data')],
    prevent_initial_call=True
)
def update_plotly_theme(theme):
    if theme == dbc.themes.CYBORG or theme == dbc.themes.DARKLY:
        return 'plotly_dark'
    elif theme == dbc.themes.SOLAR:
        return 'plotly_dark'
    return 'plotly_white'



app.clientside_callback(
    """
    function(n_clicks) {
        return window.dash_clientside.clientside.toggleFullScreen(n_clicks);
    }
    """,
    Output("trigger-fullscreen", "data"),
    [Input("fullscree
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
        <!-- Hotjar Tracking Code for Site 5148807 (name missing) -->
        <script>
            (function(h,o,t,j,a,r){
                h.hj=h.hj||function(){(h.hj.q=h.hj.q||[]).push(arguments)};
                h._hjSettings={hjid:5148807,hjsv:6};
                a=o.getElementsByTagName('head')[0];
                r=o.createElement('script');r.async=1;
                r.src=t+h._hjSettings.hjid+j+h._hjSettings.hjsv;
                a.appendChild(r);
            })(window,document,'https://static.hotjar.com/c/hotjar-','.js?sv=');
        </script>
        <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-9BR02FMBX1"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
        
          gtag('config', 'G-9BR02FMBX1');
        </script>
        <!-- Google Tag Manager -->
        <script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
        new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
        j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
        'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
        })(window,document,'script','dataLayer','GTM-T6SPT9FD');</script>
        <!-- End Google Tag Manager -->
        {%metas%}
        <title>Stocks monitoring and recommendation made easy - WatchMyStocks</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="description" content="Track and forecast stock prices, visualize trends, get stock recommendations, and chat with an AI financial advisor. Save your watchlist today!">
        <meta name="keywords" content="stock, stocks, stocks dashboard, finance, stocks forecasting, stocks news, stocks monitoring, stocks recommendations, finance, financial advisor, watchlist, watchmystocks, mystocks">
        <meta name="author" content="WatchMyStocks">
        <meta property="og:title" content="Stocks monitoring and recommendation made easy - WatchMyStocks" />
        <meta property="og:description" content="Stocks monitoring, recommendations, news and more" />
        <meta property="og:image" content="https://mystocksportfolio.io/assets/logo_with_transparent_background.png" />
        <meta property="og:url" content="https://mystocksportfolio.io/" />
        <meta name="twitter:card" content="summary_large_image" />
        <link rel="canonical" href="https://mystocksportfolio.io/" />
        <link rel="icon" href="/assets/logo_with_transparent_background_favicon.png" type="image/png">

        {%css%}
        <link id="theme-switch" rel="stylesheet" href="{{ external_stylesheets[0] }}">
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
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "WebSite",
          "url": "https://mystocksportfolio.io/",
          "name": "myStocksportoflio",
          "description": "Track and forecast stock prices, visualize trends, get stock recommendations, and chat with an AI financial advisor.",
          "publisher": {
            "@type": "Organization",
            "name": "MyStocks"
          }
        }
        </script>
        
    </head>
    <body>
        <!-- Google Tag Manager (noscript) -->
        <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-T6SPT9FD"
        height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
        <!-- End Google Tag Manager (noscript) -->
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''
if __name__ == '__main__':
    app.run_server(debug=True, port=8051)

