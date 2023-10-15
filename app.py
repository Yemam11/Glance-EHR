import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from helpers import error, login_required, find_interaction
import requests
from bs4 import BeautifulSoup



# Configure application
app = Flask(__name__)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#configure the database
db = SQL("sqlite:///records.db")

#Load the drugs from the database into a list
Rx = []
drugdb = db.execute("SELECT drug FROM drugs")
for drug in drugdb:
    drug = drug.values()
    Rx.extend(drug)



@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():

    print(session)

    #initialize variables
    patients = []
    records = []

    #if the user is a physician then gather all of their patients
    if session["client"] == "physician":
        patients = db.execute("SELECT patient_id, first_name, last_name, dob FROM patient_profiles WHERE primary_physician = ?", session["user_id"])

    #if the user is a patient then gather all their records to be presented
    if session["client"] == "patient":
        records = db.execute("SELECT * FROM patient_records WHERE patient_id = ?", session["user_id"])

    return render_template("index.html", session = session, patients = patients, lenpatients = len(patients), records = records)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.pop("user_id", default = None)

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return error("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return error("must provide password", 400)

        username = request.form.get("username")
        password = request.form.get("password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username exists and password is correct
        if len(rows) != 1 or not rows[0]["password"] == password:
            return error("invalid username and/or password", 400)

        if rows[0]["client_type"] != session["client"]:
            return error("Please use the correct login portal", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route by GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html", client_type = session["client"].capitalize())


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/clientselect")


#TO DO - change the login to update the physician info with their physician/patient id number
#TO DO - redirect them to the build a profile page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirm_password")
        client_type = request.form.get("client_type")

        #input checking
        if not username:
            return error("must provide username", 400)
        elif not password:
            return error("must provide password", 400)
        elif not confirmation:
            return error("must confirm password", 400)
        elif confirmation != password:
            return error("Password and confirmation do not match", 400)
        elif not client_type:
            return error ("please enter a client type", 400)
        else:
            #check that the username is unique
            identical_users = db.execute("SELECT * FROM users WHERE username = ?", username)
            if len(identical_users) != 0:
                return error("username must be unique", 400)

            else:
                #once input checking is complete enter their information into the database
                db.execute("INSERT INTO users (username, password, client_type) VALUES (?, ? , ?)", username, password, client_type)


                #add the relevant session info to log them in
                session["user_id"] = db.execute("SELECT * FROM users WHERE username = ?", username)[0]["user_id"]
                session["client"] = db.execute("SELECT * FROM users WHERE username = ?", username)[0]["client_type"]

                #record their patient/physician id and add it to their profile
                if session["client"] == "physician":
                    db.execute("INSERT INTO physician_profiles (physician_id) VALUES (?)", session["user_id"])
                else:
                    db.execute("INSERT INTO patient_profiles (patient_id) VALUES (?)", session["user_id"])

                #REDIRECT THEM TO ADD THIER INFORMATION
                return redirect("/buildprofile")


@app.route("/clientselect", methods = ["GET", "POST"])
def client():

    session.clear()

    if request.method == "GET":
        return render_template("client select.html")

    elif request.method == "POST":

        if request.form.get("client") == "Patient Log In":
            session['client'] = "patient"
        elif request.form.get("client") == "Physician Log In":
            session['client'] = "physician"

        return redirect("/login")


@app.route("/buildprofile", methods = ["GET", "POST"])
@login_required
def buildprofile():
    if request.method == "GET":
        #pass it the data to fill in any known information
        fullname = ""
        if session["client"] == "patient":
            client_info = db.execute("SELECT * FROM patient_profiles WHERE patient_id = ?", session["user_id"])
            if client_info[0]["primary_physician"]:
                fullname = db.execute("SELECT * FROM physician_profiles WHERE physician_id = ?", client_info[0]["primary_physician"])
                fullname = fullname[0]
                fullname = fullname["first_name"] + " " + fullname["last_name"]
                print(fullname)
        else:
            client_info = db.execute("SELECT * FROM physician_profiles WHERE physician_id = ?", session["user_id"])


        #send the data as a dict
        client_info = client_info[0]

        #make sure if the user deletes everything the "" is replaced with None
        for key in client_info:
            if client_info[key] == "":
                client_info[key] = None



        physicians = db.execute("SELECT * FROM physician_profiles")

        #concatenate the first and last names of the doctors
        physicians_list = []
        if len(physicians) > 0:
            for physician in physicians:
                if physician["first_name"]:
                    physicians_list.append(physician["first_name"] + " " + physician["last_name"])


        return render_template("profile.html", client_info = client_info, session = session, physicians = physicians, fullname = fullname, Rx = Rx)

    else:
        if session["client"] == "patient":
            #implement db query to update thier information:
            firstname = request.form.get("firstname")
            lastname = request.form.get("lastname")
            dob = request.form.get("dob")
            address = request.form.get("address")
            existingconditions = request.form.get("existingconditions")
            medications = request.form.get("medications")
            print(medications)
            primaryphysician = request.form.get("primary_physician")

            client_info = db.execute("SELECT * FROM patient_profiles WHERE patient_id = ?", session["user_id"])
            client_info = client_info[0]

            db.execute("UPDATE patient_profiles SET first_name = ?, last_name = ?, dob = ?, address = ?, existing_conditions = ?, medications = ?, primary_physician = ? WHERE patient_id = ?", firstname, lastname, dob, address, existingconditions, medications, primaryphysician, session["user_id"])

            return redirect("/")
        else:
            firstname = request.form.get("firstname")
            lastname = request.form.get("lastname")
            dob = request.form.get("dob")
            address = request.form.get("address")
            specialization = request.form.get("specialization")
            workplace = request.form.get("workplace")

            db.execute("UPDATE physician_profiles SET first_name = ?, last_name = ?, dob = ?, address = ?, specialization = ?, workplace = ? WHERE physician_id = ?", firstname, lastname, dob, address, specialization, workplace, session["user_id"])

            return redirect("/")


@app.route("/viewpatient", methods = ["POST", "GET"])
@login_required
def viewpatient(**kwargs):

    if request.method == "POST":

        #check to see if patient_id was sent
        if "patient_id" not in kwargs:
            patient_id = request.form.get("managepatient")
        else:
            patient_id = kwargs["patient_id"]


        #Finds the relevant information for the patient the physician is trying to view
        client_info = db.execute("SELECT * FROM patient_profiles WHERE patient_id = ?", patient_id)
        client_info = client_info[0]

        #Add a popup to alert the physician of any drug interactions
        medications = client_info["medications"]

        if medications:
            interactions = find_interaction(medications)
        else:
            interactions = []

        return render_template("patient.html", session = session, client_info = client_info, patient_id = patient_id, interactions = interactions, interaction_len = len(interactions), Rx = Rx)

    else:

        interactions = []

        patient_id = request.args.get('managepatient')

        client_info = db.execute("SELECT * FROM patient_profiles WHERE patient_id = ?", patient_id)
        client_info = client_info[0]

        #Add a popup to alert the physician of any drug interactions
        medications = client_info["medications"]


        if medications:
            interactions = find_interaction(medications)
        else:
            interactions = []

        return render_template("patient.html", session = session, client_info = client_info, patient_id = patient_id, interactions = interactions, interaction_len = len(interactions), Rx = Rx)

@app.route("/update", methods = ["POST"])
@login_required
def update():

    if request.method == "POST":
        patient_id = request.form.get("patientid")

        #implement db query to update thier information:
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        dob = request.form.get("dob")
        address = request.form.get("address")
        existingconditions = request.form.get("existingconditions")
        medications = request.form.get("medselect")
        notes = request.form.get("notes")

        #if any of the non required fields are blank replace with null
        if existingconditions == "":
            existingconditions = None

        if notes == "":
            notes = None

        #update the information in the database
        db.execute("UPDATE patient_profiles SET first_name = ?, last_name = ?, dob = ?, address = ?, existing_conditions = ?, medications = ?, notes = ? WHERE patient_id = ?", firstname, lastname, dob, address, existingconditions, medications, notes, patient_id)

        #requerie the database to render the page again with updated information
        client_info = db.execute("SELECT * FROM patient_profiles WHERE patient_id = ?", patient_id)
        client_info = client_info[0]

        return viewpatient(patient_id = patient_id)



#TO DO: Add option to add records
@app.route("/add_record", methods = ["POST"])
@login_required
def add_record():
    patient_id = request.form.get("patientid")

    record = request.files["file"]
    title = request.form.get("title")
    print(title)
    description = request.form.get("description")
    if not description:
        description = None

    path = f'static/uploads/{title}'
    record.save(os.path.join(app.root_path, path))

    binary_data = record.read()

    db.execute("INSERT INTO patient_records(patient_id, title, description, record) VALUES (?, ?, ?, ?)", patient_id, title, description, path)

    return viewpatient(patient_id = patient_id)


@app.route("/viewrecords", methods = ["POST"])
@login_required
def view_record():
    patient_id = request.form.get("patientid")
    records = db.execute("SELECT * FROM patient_records WHERE patient_id = ?", patient_id)
    return render_template("viewrecords.html", session = session, records = records)
