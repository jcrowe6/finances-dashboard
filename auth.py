from flask import request, redirect, url_for, render_template, flash, session, Response
from config import DASHBOARD_PASSWORD


class SimpleAuth:
    """Simple single-password authentication"""

    def __init__(self, app):
        self.app = app
        self.password = DASHBOARD_PASSWORD
        self._register_routes()
        self._setup_middleware()

    def _register_routes(self):
        """Register authentication routes"""

        @self.app.route("/login", methods=["GET", "POST"])
        def login():
            if request.method == "POST":
                password = request.form.get("password", "").strip()

                if not password:
                    flash("Please enter the password.", "error")
                    return render_template("login.html")

                if password == self.password:
                    session["authenticated"] = True
                    next_page = request.args.get("next")

                    # Simple redirect validation
                    if (
                        next_page
                        and next_page.startswith("/")
                        and not next_page.startswith("//")
                    ):
                        return redirect(next_page)
                    return redirect("/")
                else:
                    flash("Incorrect password.", "error")

            return render_template("login.html")

        @self.app.route("/logout")
        def logout():
            session.pop("authenticated", None)
            flash("You have been logged out.", "info")
            return redirect(url_for("login"))

    def _setup_middleware(self):
        """Setup authentication middleware"""

        @self.app.before_request
        def require_auth():
            # Allow access to these endpoints without authentication
            public_endpoints = ["login", "static"]

            if request.endpoint in public_endpoints:
                return

            # Require authentication for main dashboard
            if not self.is_authenticated():
                if request.path.startswith("/_dash"):
                    return Response("Authentication required", status=401)
                return redirect(url_for("login", next=request.url))

    def is_authenticated(self):
        """Check if current session is authenticated"""
        return session.get("authenticated", False)


def setup_auth(app):
    """Factory function to setup authentication for Flask app"""
    return SimpleAuth(app)


def is_authenticated():
    """Helper function to check if current session is authenticated"""
    return session.get("authenticated", False)
