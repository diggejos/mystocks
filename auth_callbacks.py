from dash import Input, Output, State, no_update
from flask import session
from models import User, bcrypt, db  # Make sure to import the app instance
from layouts import themes, login_layout, dashboard_layout
import dash_bootstrap_components as dbc
import utils as ut
import dash
import re
from dash.exceptions import PreventUpdate



# Define a function to register the callback
def register_auth_callbacks(app, server, mail):
    @app.callback(
        [Output('login-status', 'data', allow_duplicate=True),
         Output('login-username-store', 'data', allow_duplicate=True),
         Output('login-link', 'style', allow_duplicate=True),
         Output('logout-button', 'style', allow_duplicate=True),
         Output('profile-link', 'style', allow_duplicate=True),
         Output('theme-store', 'data', allow_duplicate=True),
         Output('plotly-theme-store', 'data', allow_duplicate=True),
         Output('page-content', 'children'),  # Redirect by changing the content
         Output('url', 'pathname')],  # Use this to redirect on login success
        [Input('login-button', 'n_clicks')],
        [State('login-username', 'value'),
         State('login-password', 'value')],
        prevent_initial_call=True
    )
    def handle_login(login_clicks, username, password):
        if login_clicks:
            user = User.query.filter_by(username=username).first()
            if user and bcrypt.check_password_hash(user.password, password):
                if not user.confirmed:
                    return (
                        False,  # login-status
                        None,  # login-username-store
                        {"display": "block"},  # login-link
                        {"display": "none"},  # logout-button
                        {"display": "none"},  # profile-link
                        themes['MATERIA']['dbc'],  # theme-store
                        'plotly_white',  # plotly-theme-store
                        login_layout,  # page-content
                        dash.no_update  # url.pathname
                    )
    
                # Set session values and return dashboard content + redirection
                session['logged_in'] = True
                session['username'] = username
    
                user_theme = user.theme if user.theme else 'MATERIA'
                plotly_theme = themes.get(user_theme, {}).get('plotly', 'plotly_white')
    
                return (
                    True,  # login-status
                    username,  # login-username-store
                    {"display": "none"},  # login-link
                    {"display": "block"},  # logout-button
                    {"display": "block"},  # profile-link
                    themes[user_theme]['dbc'],  # theme-store
                    plotly_theme,  # plotly-theme-store
                    dashboard_layout,  # page-content
                    '/'  # url.pathname
                )
            else:
                return (
                    False,  # login-status
                    None,  # login-username-store
                    {"display": "block"},  # login-link
                    {"display": "none"},  # logout-button
                    {"display": "none"},  # profile-link
                    themes['MATERIA']['dbc'],  # theme-store
                    'plotly_white',  # plotly-theme-store
                    login_layout,  # page-content
                    dash.no_update  # url.pathname
                )
    
        # If no clicks yet, prevent updates
        raise PreventUpdate

    @app.callback(
        Output('register-output', 'children'),
        [Input('register-button', 'n_clicks')],
        [State('username', 'value'),
         State('email', 'value'),
         State('password', 'value'),
         State('confirm_password', 'value')]
    )
    def register_user(n_clicks, username, email, password, confirm_password):
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

            # If validation passes, hash the password and save the user
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(username=username, email=email, password=hashed_password)

            try:
                db.session.add(new_user)
                db.session.commit()

                # Generate confirmation token
                token = ut.generate_confirmation_token(email, server)

                # Send email confirmation
                ut.send_confirmation_email(email, token, mail)

                return dbc.Alert("Registration successful! Please confirm your email.", color="success")
            except Exception as e:
                return dbc.Alert(f"Error: {str(e)}", color="danger")
        return dash.no_update
       
    # @app.callback(
    #     [Output('login-status', 'data', allow_duplicate=True),
    #      Output('login-username-store', 'data', allow_duplicate=True),
    #      Output('login-link', 'style', allow_duplicate=True),
    #      Output('logout-button', 'style', allow_duplicate=True),
    #      Output('profile-link', 'style', allow_duplicate=True),
    #      Output('theme-store', 'data', allow_duplicate=True),
    #      Output('plotly-theme-store', 'data', allow_duplicate=True),
    #      Output('page-content', 'children'),  # Redirect by changing the content
    #      Output('url', 'pathname')],  # Use this to redirect on login success
    #     [Input('login-button', 'n_clicks')],
    #     [State('login-username', 'value'),
    #      State('login-password', 'value')],
    #     prevent_initial_call=True
    # )
    # def handle_login(login_clicks, username, password):
    #     if login_clicks:
    #         user = User.query.filter_by(username=username).first()
    #         if user and bcrypt.check_password_hash(user.password, password):
    #             # Set session values and return dashboard content + redirection
    #             session['logged_in'] = True
    #             session['username'] = username

    #             user_theme = user.theme if user.theme else 'MATERIA'
    #             plotly_theme = themes.get(user_theme, {}).get('plotly', 'plotly_white')

    #             return (True, username, {"display": "none"}, {"display": "block"}, {"display": "block"},
    #                     themes[user_theme]['dbc'], plotly_theme, dashboard_layout, '/')  # Redirect to '/'
    #         else:
    #             return (False, None, {"display": "block"}, {"display": "none"}, {"display": "none"},
    #                     themes['MATERIA']['dbc'], 'plotly_white', login_layout, no_update)

    #     # If no clicks yet, ensure to return 9 values:
    #     return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
    
    # @app.callback(
    #     Output('register-output', 'children'),
    #     [Input('register-button', 'n_clicks')],
    #     [State('username', 'value'),
    #       State('email', 'value'),
    #       State('password', 'value'),
    #       State('confirm_password', 'value')]
    # )
    # def register_user(n_clicks, username, email, password, confirm_password):
    #     if n_clicks:
    #         if not username:
    #             return dbc.Alert("Username is required.", color="danger")
    #         if not email:
    #             return dbc.Alert("Email is required.", color="danger")
    #         if not password:
    #             return dbc.Alert("Password is required.", color="danger")
    #         if password != confirm_password:
    #             return dbc.Alert("Passwords do not match.", color="danger")
            
    #         # Validate the password
    #         password_error = ut.validate_password(password)
    #         if password_error:
    #             return dbc.Alert(password_error, color="danger")

    #         # If validation passes, hash the password and save the user
    #         hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    #         new_user = User(username=username, email=email, password=hashed_password)

    #         try:
    #             db.session.add(new_user)
    #             db.session.commit()
    #             return dbc.Alert("Registration successful!", color="success")
    #         except Exception as e:
    #             return dbc.Alert(f"Error: {str(e)}", color="danger")
    #     return dash.no_update
    

    




    @app.callback(
        [Output('req-length', 'className'),
          Output('req-uppercase', 'className'),
          Output('req-lowercase', 'className'),
          Output('req-digit', 'className'),
          Output('req-special', 'className')],
        Input('password', 'value')
    )
    def update_password_requirements(password):
        if password is None:
            password = ""

        length_class = 'text-muted' if len(password) < 8 else 'text-success'
        uppercase_class = 'text-muted' if not re.search(r"[A-Z]", password) else 'text-success'
        lowercase_class = 'text-muted' if not re.search(r"[a-z]", password) else 'text-success'
        digit_class = 'text-muted' if not re.search(r"\d", password) else 'text-success'
        special_class = 'text-muted' if not re.search(r"[!@#$%^&*(),.?\":{}|<>_]", password) else 'text-success'

        return length_class, uppercase_class, lowercase_class, digit_class, special_class
    
    
    @app.callback(
        [Output('profile-req-length', 'className'),
         Output('profile-req-uppercase', 'className'),
         Output('profile-req-lowercase', 'className'),
         Output('profile-req-digit', 'className'),
         Output('profile-req-special', 'className')],
        Input('profile-password', 'value')
    )
    def update_profile_password_requirements(password):
        return update_password_requirements(password)
    
    
    @app.callback(
        [Output('login-status', 'data', allow_duplicate=True),
         Output('login-link', 'style', allow_duplicate=True),
         Output('logout-button', 'style', allow_duplicate=True),
         Output('profile-link', 'style', allow_duplicate=True),
         Output('individual-stocks-store', 'data', allow_duplicate=True),
         Output('theme-store', 'data', allow_duplicate=True),
         Output('plotly-theme-store', 'data', allow_duplicate=True),
         Output('url', 'pathname', allow_duplicate=True)],  # Redirect on logout
        [Input('logout-button', 'n_clicks')],
        prevent_initial_call=True
    )
    def handle_logout(logout_clicks):
        if logout_clicks:
            session.pop('logged_in', None)
            session.pop('username', None)
            return False, {"display": "block"}, {"display": "none"}, {"display": "none"}, ['AAPL','MSFT'], dbc.themes.MATERIA, 'plotly_white', '/login'  # Redirect to login
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


    @app.callback(
        [Output('login-status', 'data'),
         Output('login-username-store', 'data'),
         Output('login-link', 'style'),
         Output('logout-button', 'style'),
         Output('profile-link', 'style')],  # Add output for profile link
        [Input('url', 'pathname')]
    )
    def check_session(pathname):
        logged_in = session.get('logged_in', False)
        username = session.get('username', None)

        if logged_in and username:
            return True, username, {"display": "none"}, {"display": "block"}, {"display": "block"}  # Show profile link
        else:
            return False, None, {"display": "block"}, {"display": "none"}, {"display": "none"}  # Hide profile link
        
    @app.callback(
        Output('login-overlay', 'is_open'),
        [Input('theme-dropdown-wrapper', 'n_clicks'),
          Input('create-watchlist-button', 'n_clicks'),
          Input('delete-watchlist-button', 'n_clicks')],
        [State('login-status', 'data')]
    )
    def show_overlay_if_logged_out(theme_n_clicks, create_n_clicks, delete_n_clicks, login_status):
        # Ensure no NoneType errors
        theme_n_clicks = theme_n_clicks or 0
        create_n_clicks = create_n_clicks or 0
        delete_n_clicks = delete_n_clicks or 0

        # Show the overlay if the user is not logged in and clicks on either element
        if (theme_n_clicks > 0  or create_n_clicks > 0 or delete_n_clicks > 0) and not login_status:
            return True  # Show overlay
        return False  # Don't show overlay

    @app.callback(
        [
         Output('create-watchlist-button', 'className'),
         Output('delete-watchlist-button', 'className')],
        Input('login-status', 'data')
    )
    def style_save_button(login_status):
        if not login_status:
            return 'grayed-out','grayed-out'  # Apply the grayed-out class when logged out
        return 'small-button','small-button'  # No class when logged in
    
    
    @app.callback(
        Output('theme-dropdown', 'disabled'),
        Input('login-status', 'data')
    )
    def update_dropdown_status(login_status):
        return not login_status  # Disable dropdown if not logged in







