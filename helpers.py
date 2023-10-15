from flask import redirect, render_template, session
from functools import wraps
import requests
import json


def login_required(func):

    #updates the wrapper to have the same information as the function that was passed in
    @wraps(func)
    def wrapper(*args, **kwargs):

        #if there is no session recorded that means the user hasnt logged in, redirect them to the login
        if session.get("user_id") is None:
            print("you need to be logged in")
            return redirect("/clientselect")

        #otherwise execute whatever function was called with whatever arguments/keywords it takes
        return func(*args, **kwargs)
    return wrapper


def error(text, code):

    #replaces any special characters with escape characters theat work so the link doesnt break
    for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"), ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
        text = text.replace(old,new)

    return render_template("error.html", text = text, code = code), code



def find_Rxcui(medications):
    """Uses the RxNorm API to search for a medication and return its unique identificaiton number from the RXlist database"""
    cuis = []
    for drug in medications:
        string = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={drug}&search=2"
        cui = requests.get(string).content
        cui = json.loads(cui)

        if not cui["idGroup"]:
            cuis.append(None)

        else:
            cui = cui["idGroup"] ["rxnormId"]
            cuis.append(cui[0])

    return (cuis)



def find_interaction(medications):
    """Returns a list of known interactions given a list of medications"""
    interactionlist = []

    #converts the medications from a comma delimited string to a list
    medications = medications.split(",")

    #creates a string of drug cuids to feed into the API
    cuis = find_Rxcui(medications)
    drugstring = ""
    for drug in cuis:
        if drug != None:
            drugstring += " " + drug

    #sends a get request to the API and returns a json
    string = f" https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis={drugstring}"
    interactions = requests.get(string).content
    interactions = json.loads(interactions)

    # pareses the json and returns description of the interaction
    if interactions.get("fullInteractionTypeGroup"):
        for interaction in interactions["fullInteractionTypeGroup"]:
            for concept in interaction["fullInteractionType"]:
                for ddi in concept["interactionPair"]:
                    if ddi["description"] not in interactionlist:
                        interactionlist.append(ddi["description"])

    return interactionlist





