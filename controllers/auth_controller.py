from flask import render_template, request, redirect, url_for, flash, jsonify, session
from models.user import User

class AuthController:
    def __init__(self, auth_service):
        self.auth = auth_service
    
    def homepage(self):
        user = self.auth.get_current_user()
        if not user.is_authenticated():
            return redirect(url_for("login"))
        
        if user.is_admin():
            return redirect(url_for("admin_panel"))
        
        return render_template("user/homepage.html", username=user.username)
    
    def register(self):
        if request.method == "POST":
            username = request.form["username"].strip()
            email = request.form["email"].strip()
            password = request.form["password"].strip()
            confirm_password = request.form.get("confirm_password", "").strip()

            result = self.auth.register(username, email, password, confirm_password)
            
            if result['success']:
                # Auto login setelah register
                login_result = self.auth.login(email, password)
                if login_result['success']:
                    self.auth.set_session(login_result['user'], login_result['token'])
                    flash("Registration successful! Welcome!", "success")
                    return redirect(url_for("homepage"))
                else:
                    flash("Registration successful! Please login.", "success")
                    return redirect(url_for("login"))
            else:
                flash(result['error'], "error")
                return render_template("user/register.html")

        return render_template("user/register.html")
    
    def login(self):
        if request.method == "POST":
            identifier = request.form["email"].strip()
            password = request.form["password"].strip()

            result = self.auth.login(identifier, password)
            
            if result['success']:
                self.auth.set_session(result['user'], result['token'])
                flash(f"Welcome back, {session['username']}!", "success")
                
                if result['user'].is_admin():
                    return redirect(url_for("admin_panel"))
                else:
                    return redirect(url_for("homepage"))
            else:
                flash(result['error'], "danger")
                return render_template("user/login.html")

        return render_template("user/login.html")
    
    def logout(self):
        self.auth.clear_session()
        flash("You have been logged out.", "info")
        return redirect(url_for("login"))
    
    def auth_check(self):
        user = self.auth.get_current_user()
        if user.is_authenticated():
            return jsonify({
                'authenticated': True,
                'user': user.to_dict(),
                'token': session.get('token')
            })
        else:
            return jsonify({'authenticated': False}), 401
    
    def api_login(self):
        data = request.json
        identifier = data.get('identifier', '').strip()
        password = data.get('password', '').strip()

        result = self.auth.login(identifier, password)
        
        if result['success']:
            self.auth.set_session(result['user'], result['token'])
            return jsonify({
                'success': True,
                'user': result['user'].to_dict(),
                'redirect': '/admin' if result['user'].is_admin() else '/homepage'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Invalid credentials')
            }), 401
    
    def api_register(self):
        data = request.json
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()

        result = self.auth.register(username, email, password, password)
        
        if result['success']:
            # Auto login setelah register
            login_result = self.auth.login(email, password)
            if login_result['success']:
                self.auth.set_session(login_result['user'], login_result['token'])
                return jsonify({
                    'success': True,
                    'user': login_result['user'].to_dict(),
                    'redirect': '/homepage'
                })
        
        return jsonify({
            'success': False,
            'error': result.get('error', 'Registration failed')
        }), 400