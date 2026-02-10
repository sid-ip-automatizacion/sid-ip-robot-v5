"""
Main entry point for the SID-IP Robot application.

This module handles the initial user authentication and launches the
main graphical user interface (UserEnvironment) upon successful login.
"""
import sys
import os

from initialize import AuthenticatedUser  # Import module for authentication
from gui import UserEnvironment  # Import module for the graphical interface

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..'))) # Add parent directory to sys.path for module imports


def main():
    """
    Main execution function.

    Authenticates the user and initializes the UserEnvironment if successful.
    """
    auth = AuthenticatedUser()
    auth.request_authent()
    if auth.authenticated:
        UserEnvironment()
    else:
        print("Authentication failed")
        sys.exit(1)


if __name__ == "__main__":
    #main()
    UserEnvironment()
