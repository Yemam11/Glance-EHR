# Glance EHR
#### Video Demo:  <https://youtu.be/60mMsaFw_l8>
####   This is a project that I created called Glance EHR (Electronic Health Records). The inspiration for this project came when I was trying to help my mother access her health records online. I was upset by the fact that her own patient information records and scans were locked behind a paywall, and that the interface was so difficult to use. Hence I decided to create my own rendition of an electronic health record management system. The project enables users to sign up as either a patient or a physician, and enables patients to view any records that their physiscian adds to thier profile. This can include images, or just text descriptions. Physicians can manage and add records for thier patients, as well as update their profiles, prescribe new medications using the medication portfolio tools, as well as create thier own profilies through the applicaiton. This app was built using Python 3.11 with Flask and SQLite3 to create a backend. Information is stored in a database called records.db, so that information can be stored between sessions. The front end was created with HTML, CSS, jinja and JavaScript. Several python libraries were also used in the process. These include the CS50, BeautifulSoup, requests and json libraries. The specific use cases will be outlined below. Henceforth is a brief description into the various funcitons that comprise this applicaiton, and some insight on certain design choices wherein:

### login_required
#### This function serves as a decorator for other funcitons within the app. Its purpose is to determine whether the user is logged in or not. If the user is logged in within the flask session object there should be a key called "user_id". if this exists then the user is logged in, and therefore the funciton that is being decorated will be called. If this key does not exist, then the user is redirected to the login page

### error
####  This function serves to return an error when a user input is invalid. For example if the user tries to register with a username that already exists, an error is returned to them describing the issue:

```
#check that the username is unique
identical_users = db.execute("SELECT * FROM users WHERE username = ?", username)
if len(identical_users) != 0:
    return error("username must be unique", 400)
```

### find_Rxcui
#### This function takes the names of mecications in a list and then uses the National Library of Medicine's API to return a unique idenitfier for each drug in the list. This function works hand in hand with the fund_interaction function to power the medication portfolio tool. the function returns a list of id numbers (RxCuids) in the order which the list of medications was presented

### find_interaction
#### This function takes the names of mecications in a comma separated string and converts them into a list of medications. each medication's Id number is found using find_Rxcui. Once the id's are found the National Library of Medicine's API is used again to search for any known interactions between the medications. The requests library is used to make the querie, and the json library is used to load the interactions as a json.

```
string = f" https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis={drugstring}"
interactions = requests.get(string).content
interactions = json.loads(interactions)
```

#### After this, the json is parsed and the interactions are returned as a list of strings.

### NOTE: The NLM API will be discontinued after Jan 1st 2024.


### parser
#### The parser function takes a url (in this use case it is the url of a database with the names of different medicaitons starting with the letter A) and copies all the medication names and adds them to a list. The URL is then altered for each letter of the alphabet until a comprehensive list of medications is created with names starting from A-Z. This is achieved using the requests library to get the page, and the BeautifulSoup Library to extract the html:

```
#parse through and find the list items (Medication names)
Rx = []
for element in page.find_all("div", {"class": "AZ_results"}):
    for li in element.find_all("li"):
        Rx.append(li.text)

return Rx
```
#### It should be noted that this funciton is only called once, and the information is immediately stored in a SQL database. This is done since webscraping is compuationally intensive, and would slow down the application if it needed to scrape an internet database everytime it was loaded in. This database is used to help create the medication portfolio tool. It is used to populate options for the select menu when physicians/patients are selecting medications.


### Register
#### The register function is called to enable the user to create a new account. They are prompted to enter a username which must be unique, a password and select a client type. the user can either select a patient or physician. This information will be saved to records.db in a table called users. This stores thier unique user identifier, thier client type (patient/physician) as well as their username and password. Upon registration, The user_id (thier unique identifier) and client type will be added to the flask session variable so it can be referenced by the rest of the app. Depending on the user type thier access to different funcitons and what will be displayed to them within the app will change. Upon completion the users are directed to build thier profile.

### buildprofile
#### The buildprofile function is intended to allow the patient to enter thier personal information such as thier name, date of birth, address, existing medical conditons, current medications. the page is slightly different for physicians and patients. Patients enter medical info such as medications and conditions, while physicians would enter specializaiton and workplace. The patient is also prompted to select thier primary physician when building thier profile to allow the physician to manage their account. Once the information is entered and submitted, it is stored in the patient_profiles or physician_profiles table accordingly. Once the profile is updated registration is condisdered complete

### client
#### Client is meant to enable someone logging in to select thier login portal. Patients and physicians have different login portals, and are redirected to the appropriate one accordingly.

### Login
#### Upon choosing their portal the user is prompted to enter their login information. This funciton checks that the information is correct (username matches password, username exists, and that the user has logged in through the right portal). Upon validation the relevant information is added to the session variable (user_id and client_type) and the user is redirected to the homepage

### Login
#### Upon choosing their portal the user is prompted to enter their login information. This funciton checks that the information is correct (username matches password, username exists, and that the user has logged in through the right portal). Upon validation the relevant information is added to the session variable (user_id and client_type) and the user is redirected to the homepage


### Index
#### Index is the function that displays the user's homepage. If the client is a physician it queries the database to find all patients who have thier primary physician set as the current user (the physician). This information is rendered within the HTML as a table, with the option for the physician to manage the patient. If the user is a patient, the patient_records table is queried for any records that belong to them (thier user id matches the one in the database), and presents the records. records are added by the physician, mediated by the add_record funciton (below)

### viewpatient
#### This physician facing function is used to view the details of a patient. the patient_id can either be sent as a parameter to the funciton, or sent through the front end via the press of a button (form submission, when a physician presses "mangage patient" thier patient id is sent to this function). The patient_records table is queried for information that matches the patient_id. The form automatically populates with the most recent information in the database and the physician can edit it and update it. The medication profile tool is powered by this function. The list of medications is taken from the form and the find_interaction function described above is used to search for any drug interactions. The function then renders and HTML template that contains updated information as well as any warnings returned from the find_interaction function that should be displayed

### update
#### This physician facing function is used to update patient details. It adds the updated information to the patient_records table for the patient being managed


### add_record
#### This is a physician facing funciton that is used to create records for a patient they are managing. The form details (title, descripiton, and any files they have uploaded) are inserted into the patient_records table for access by the physician later, or presentation to the patient

### view_record
#### This is a physician facing funciton that is used to allow the physician to view existing records for a patient. It queries the patient_records database for the records and serves them in an HTML template.
