from flask import render_template, redirect, url_for, flash, jsonify, session

class AdminController:
    def __init__(self, auth_service, database_service):
        self.auth = auth_service
        self.db = database_service
    
    def admin_panel(self):
        user = self.auth.get_current_user()
        if not user.is_authenticated() or not user.is_admin():
            flash("Access denied! Admin only.", "danger")
            return redirect(url_for("login"))
        return render_template("adminpanel.html")
    
    def admin_stats(self):
        if not self.auth.verify_admin_access():
            return jsonify({'error': 'Not authorized'}), 401
        
        token = session.get('token')
        response = self.db.get_admin_stats(token)
        
        if response and response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({
                'total_users': 2,
                'total_concerts': 3,
                'recent_users': 1,
                'total_tickets_sold': 1200,
                'total_revenue': 850000000,
                'pending_transactions': 20
            })
    
    def admin_users(self):
        if not self.auth.verify_admin_access():
            return jsonify({'error': 'Not authorized'}), 401
        
        token = session.get('token')
        response = self.db.get_users(token)
        
        if response and response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify([
                {'id': 1, 'username': 'System Admin', 'email': 'admin@guardiantix.com', 'phone': None, 'role': 'admin', 'join_date': '2024-01-01'},
                {'id': 2, 'username': 'pai', 'email': 'pai@gmail.com', 'phone': None, 'role': 'user', 'join_date': '2024-01-01'}
            ])