import requests
from cs50 import SQL
from bs4 import BeautifulSoup
db = SQL("sqlite:///records.db")

url = "https://www.rxlist.com/drugs/alpha_a.htm"


Rx = []

def parser(url1, Rx):
    #Fetch the page
    html = requests.get(url)
    page = BeautifulSoup(html.content, 'html.parser')

    #parse through and find the list items (Medication names)
    for element in page.find_all("div", {"class": "AZ_results"}):
        for li in element.find_all("li"):
            Rx.append(li.text)

    return Rx


#scrape the web and return a list containing every drug in a database
#the database that was used was taken from https://www.rxlist.com/
for count in range(26):
    Rx = parser(url, Rx)
    letter_index = url.find("_") + 1
    letter = chr(ord(url[letter_index]) + 1)
    url = list(url)
    url[letter_index] = letter
    url = "".join(url)

#add each drug into a database, this is way faster than scraping the web and compiling a list every time we run the app
for drug in Rx:
    db.execute("INSERT into drugs (drug) VALUES(?)", drug)


