from dash import Input, Output, State
from flask import session
from models import User, bcrypt, db  # Make sure to import the app instance
from layouts import themes
import dash_bootstrap_components as dbc
import utils as ut
import dash
import re
from dash.exceptions import PreventUpdate
from flask import url_for


# Define a function to register the callback
def register_auth_callbacks(app, server, mail):
    @app.callback(
        [Output('login-status', 'data'),
         Output('login-username-store', 'data'),
         Output('theme-store', 'data', allow_duplicate=True),
         Output('plotly-theme-store', 'data', allow_duplicate=True),
         Output('login-output', 'children'),
         Output('url', 'href')],  # Use href for full URL redirection
        [Input('login-button', 'n_clicks')],
        [State('login-username', 'value'),
         State('login-password', 'value')],
        prevent_initial_call=True
    )
    def handle_login(login_clicks, username, password):
        if login_clicks:
            # Check if username or password fields are empty
            if not username or not password:
                error_message = dbc.Alert("Username and password are required.", color="danger", className="mt-2")
                return (
                    False,  # login-status
                    None,  # login-username-store
                    themes['Lightmode']['dbc'],  # Default theme
                    'plotly_white',  # Default Plotly theme
                    error_message,  # Show error message
                    dash.no_update  # Do not redirect
                )
            
            # Fetch the user from the database
            user = User.query.filter_by(username=username).first()
            
            # Check if the user exists and if the password matches
            if not user or not bcrypt.check_password_hash(user.password, password):
                error_message = dbc.Alert("Invalid username or password.", color="danger", className="mt-2")
                return (
                    False,  # login-status
                    None,  # login-username-store
                    themes['Lightmode']['dbc'],  # Default theme
                    'plotly_white',  # Default Plotly theme
                    error_message,  # Show error message
                    dash.no_update  # Do not redirect
                )
    
            # Check if the email is confirmed
            if not user.confirmed:
                return (
                    False,  # login-status
                    None,  # login-username-store
                    themes['Lightmode']['dbc'],  # Default theme
                    'plotly_white',  # Default Plotly theme
                    dbc.Alert("Please confirm your email address.", color="warning", className="mt-2"),
                    dash.no_update  # Do not redirect
                )
            
            # Successful login, set session values
            session['logged_in'] = True
            session['username'] = username
            session.modified = True
    
            # Handle premium users without payment
            if user.subscription_status == 'premium' and not user.payment_status:
                return (
                    True,  # login-status
                    username,  # login-username-store
                    themes['Lightmode']['dbc'],  # Default theme
                    'plotly_white',  # Default Plotly theme
                    dash.no_update,  # No error message
                    '/create-checkout-session'  # Redirect to payment page
                )
            
            # Handle free users or premium users who have paid
            user_theme = user.theme if user.theme else 'Lightmode'
            plotly_theme = themes.get(user_theme, {}).get('plotly', 'plotly_white')
    
            # Redirect to home page (dashboard)
            return (
                True,  # login-status
                username,  # login-username-store
                themes[user_theme]['dbc'],  # User's selected theme
                plotly_theme,  # User's selected Plotly theme
                dash.no_update,  # No error message
                '/'  # This will redirect to the home page and update the URL
            )
    
        # If the button was not clicked, do not update anything
        raise PreventUpdate()



    app.clientside_callback(
        """
        function(free_clicks) {
            if (free_clicks) {
                return '/register-free';
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output('url-redirect', 'href',allow_duplicate=True),
        Input('free-signup-button', 'n_clicks'),
        prevent_initial_call=True
    )
    
    app.clientside_callback(
        """
        function(paid_clicks, login_status, username) {
            if (paid_clicks) {
                if (login_status && username) {
                    return '/create-checkout-session';
                } else {
                    return '/register-paid';
                }
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output('url-redirect', 'href'),
        [Input('paid-signup-button', 'n_clicks')],
        [State('login-status', 'data'), State('login-username-store', 'data')],
        prevent_initial_call=True
    )




    @app.callback(
    Output('register-output', 'children'),
    [Input('register-button', 'n_clicks')],
    [State('username', 'value'),
     State('email', 'value'),
     State('password', 'value'),
     State('confirm_password', 'value'),
     State('selected-plan', 'data')],  # Capture the selected plan
    prevent_initial_call=True
    )
    def register_user(n_clicks, username, email, password, confirm_password, selected_plan):
        if n_clicks:
            if not username:
                return dbc.Alert("Username is required.", color="danger")
            if not email:
                return dbc.Alert("Email is required.", color="danger")
            if not password:
                return dbc.Alert("Password is required.", color="danger")
            if password != confirm_password:
                return dbc.Alert("Passwords do not match.", color="danger")
    
            # Validate the password
            password_error = ut.validate_password(password)
            if password_error:
                return dbc.Alert(password_error, color="danger")
    
            # Check if email already exists
            if User.query.filter_by(email=email).first():
                return dbc.Alert("Email already registered.", color="danger")
    
            # Hash the password and store the user's selected plan
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(username=username, email=email, password=hashed_password, subscription_status=selected_plan, payment_status=False)
    
            try:
                db.session.add(new_user)
                db.session.commit()
    
                # Generate confirmation token
                token = ut.generate_confirmation_token(email, server)
    
                # Send email confirmation
                ut.send_confirmation_email(email, token, mail)
    
                # Send welcome email
                ut.send_welcome_email(email, username, mail)
                
                ut.schedule_watchlist_email(email, username,mail,app)

    
                return dbc.Alert("Registration successful! Please confirm your email.", color="success")
            except Exception as e:
                return dbc.Alert(f"Error: {str(e)}", color="danger")
        return dash.no_update
    
    
    import logging

    logging.basicConfig(level=logging.INFO)
    
    @app.callback(
        Output('reset-output', 'children'),
        [Input('reset-button', 'n_clicks')],
        [State('reset-email', 'value')],
        prevent_initial_call=True
    )
    def send_reset_link(n_clicks, email):
        if n_clicks:
            logging.info(f"Reset link requested for email: {email}")
            # Make email comparison case-insensitive
            user = User.query.filter(db.func.lower(User.email) == db.func.lower(email)).first()
            
            if not user:
                logging.warning(f"No user found with email: {email}")
                return dbc.Alert("This email is not registered.", color="danger")
        
            logging.info(f"User found: {user.username}, sending reset link.")
            # Generate reset token
            token = ut.generate_confirmation_token(email, server)
            reset_url = url_for('reset_password', token=token, _external=True)
        
            # Send reset email
            ut.send_reset_email(email, reset_url, mail)
        
            return dbc.Alert("A password reset link has been sent to your email.", color="success")
        
        raise PreventUpdate


    @app.callback(
        [Output('req-length', 'className'),
         Output('req-uppercase', 'className'),
         Output('req-lowercase', 'className'),
         Output('req-digit', 'className'),
         # Output('req-special', 'className')
         ],
        Input('password', 'value')
    )
    def update_password_requirements(password):
        if password is None:
            password = ""

        length_class = 'text-muted' if len(password) < 8 else 'text-success'
        uppercase_class = 'text-muted' if not re.search(r"[A-Z]", password) else 'text-success'
        lowercase_class = 'text-muted' if not re.search(r"[a-z]", password) else 'text-success'
        digit_class = 'text-muted' if not re.search(r"\d", password) else 'text-success'
        # special_class = 'text-muted' if not re.search(r"[!@#$%^&*(),.?\":{}|<>_]", password) else 'text-success'

        return length_class, uppercase_class, lowercase_class, digit_class
    

    @app.callback(
        [Output('profile-req-length', 'className'),
         Output('profile-req-uppercase', 'className'),
         Output('profile-req-lowercase', 'className'),
         Output('profile-req-digit', 'className'),
         # Output('profile-req-special', 'className')
         ],
        Input('profile-password', 'value')
    )
    def update_profile_password_requirements(password):
        return update_password_requirements(password)
    
    
    @app.callback(
    [Output('login-status', 'data', allow_duplicate=True),
     Output('login-link', 'style', allow_duplicate=True),
     Output('logout-button', 'style', allow_duplicate=True),
     Output('individual-stocks-store', 'data', allow_duplicate=True),
     Output('theme-store', 'data', allow_duplicate=True),
     Output('plotly-theme-store', 'data', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],  # Redirect on logout
    [Input('logout-button', 'n_clicks')],
    prevent_initial_call=True
    )
    def handle_logout(logout_clicks):
        if logout_clicks:
            # Clear session and user-specific data
            session.pop('logged_in', None)
            session.pop('username', None)
    
            # Ensure the session is saved/updated
            session.modified = True
    
            # Reset to default values after logout
            return (
                False,  # login-status reset
                {"display": "block"},  # Show login link
                {"display": "none"},  # Hide logout button
                ['AAPL', 'MSFT'],  # Reset individual stocks store to default
                dbc.themes.SPACELAB,  # Reset theme to default
                'plotly_white',  # Reset plotly theme to default
                '/'  # Redirect to login page
            )
    
        # No updates if logout button was not clicked
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    

    @app.callback(
        Output('login-status-display', 'children'),
        Input('login-status', 'data')
    )
    def display_login_status(login_status):
        return f"Login status: {'Logged In' if login_status else 'Logged Out'}"
    


    app.clientside_callback(
        """
        function(login_status) {
            // If login_status is true (logged in), enable the dropdown
            // If login_status is false (logged out), disable the dropdown
            return !login_status;
        }
        """,
        Output('theme-dropdown', 'disabled'),
        Input('login-status', 'data')
    )

    


