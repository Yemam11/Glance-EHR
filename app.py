import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session

# Configure application
app = Flask(__name__)

#set up the session
"""TO DO"""

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///ENTER THE NAME OF THE DB FILE HERE")