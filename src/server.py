import os
import sys
import argparse
import pyrebase
import requests
import webbrowser
from urllib.parse import quote
import pycurl
import json
from flask import Flask, url_for, jsonify, request
python3 = False
try:
    from StringIO import StringIO
except ImportError:
    python3 = True
    import io as bytesIOModule
from bs4 import BeautifulSoup
if python3:
    import certifi

config={
    "apiKey": "AIzaSyCQZXsJoPay0R5Uoe_g3TlHUBvb6fmxnWw",
    "authDomain": "trial-6d399.firebaseapp.com",
    "databaseURL": "https://trial-6d399.firebaseio.com",
    "projectId": "trial-6d399",
    "storageBucket": "trial-6d399.appspot.com",
    "messagingSenderId": "26993915592"
}

#SEARCH_URL = 'https://www.google.com/searchbyimage?image_url='
SEARCH_LABEL = 'https://www.google.com/search?q='
app = Flask(__name__)

@app.route('/labelsearch', methods = ['POST'])
def label_search():
    if request.headers['Content-Type'] != 'application/json':
        return "Request must be JSON format"
    client_json = json.dumps(request.json)
    client_data = json.loads(client_json)

    code = doImageSearch(SEARCH_LABEL + quote(client_data['q']))
    
    return parseLabelResults(code)

@app.route('/search', methods = ['POST'])
def search():
    if request.headers['Content-Type'] != 'application/json':
        return "Requests must be in JSON format. Please make sure the header is 'application/json' and the JSON is valid."
    client_json = json.dumps(request.json)
    client_data = json.loads(client_json)

    
    app = pyrebase.initialize_app(config)
    storage = app.storage()
    storage.child(client_data['image_path']).download("example.jpg")
    dirname= os.path.dirname(os.path.abspath(__file__))
    filename= os.path.join(dirname,'example.jpg')
    searchUrl='https://www.google.hr/searchbyimage/upload'
    multipart={'encoded_image':(filename, open(filename,'rb')),'image_content':''}
    response=requests.post(searchUrl, files=multipart, allow_redirects=False)
    fetchUrl=response.headers['Location']
    code = doImageSearch(fetchUrl)
    return parseResults(code)


def doImageSearch(full_url):
    # Directly passing full_url
    """Return the HTML page response."""

    if python3:
        returned_code = bytesIOModule.BytesIO()
    else:
        returned_code = StringIO()
    # full_url = SEARCH_URL + image_url

    if app.debug:
        print('POST: ' + full_url)

    conn = pycurl.Curl()
    if python3:
        conn.setopt(conn.CAINFO, certifi.where())
    conn.setopt(conn.URL, str(full_url))
    conn.setopt(conn.FOLLOWLOCATION, 1)
    conn.setopt(conn.USERAGENT, 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:61.0) Gecko/20100101 Firefox/61.0')
    conn.setopt(conn.WRITEFUNCTION, returned_code.write)
    conn.perform()
    conn.close()
    if python3:
        return returned_code.getvalue().decode('UTF-8')
    else:
        return returned_code.getvalue()

def parseLabelResults(code):
    soup = BeautifulSoup(code, 'html.parser')
    label_results = {
        'links': [],
        'titles': [],
        'maps': '',
        'images': [],
        'buy_link':[]
    }

    for div in soup.findAll('div', attrs={'class':'rc'}):
        sLink = div.find('a')
        label_results['links'].append(sLink['href'])

    for buy in soup.findAll('div', attrs={'class':'mnr-c pla-unit'}):
        if type(buy)!='NoneType':
            blink=buy.find('a').find_next_sibling('a')
            if type(blink)!='NoneType':
                label_results['buy_link'].append(blink['href'])

    for title in soup.findAll('div', attrs={'class':'rc'}):
        title_name=title.find('h3')
        label_results['titles'].append(title_name.get_text())

    for map_link in soup.findAll('div', attrs={'class':'xERobd'}):
        if type(map_link)!='NoneType':
            mlink=map_link.find('a')
            if type(mlink)!='NoneType':
                label_results['maps']='https://www.google.com' + mlink['href']

    for image in soup.findAll('div', attrs={'id':'imagebox_bigimages'}):
        if type(image)!='NoneType':
            image_link=image.find('a')
            if type(image_link)!='NoneType':
                label_results['images'].append('https://www.google.com'+image_link['href'])

    for image in soup.findAll('div', attrs={'class':'PFaeqe'}):
        if type(image)!='NoneType':
            image_link=image.find('a')
            if type(image_link)!='NoneType':
                label_results['images'].append('https://www.google.com'+image_link['href'])

    
    print("Successful search")

    return json.dumps(label_results)

def parseResults(code):
    """Parse/Scrape the HTML code for the info we want."""

    soup = BeautifulSoup(code, 'html.parser')

    results = {
        'links': [],
        'descriptions': [],
        'titles': [],
        'similar_images': [],
        'best_guess': ''
    }

    for div in soup.findAll('div', attrs={'class':'rc'}):
        sLink = div.find('a')
        results['links'].append(sLink['href'])

    for desc in soup.findAll('span', attrs={'class':'st'}):
        results['descriptions'].append(desc.get_text())

    for title in soup.findAll('div', attrs={'class':'rc'}):
        title_name=title.find('h3')
        results['titles'].append(title_name.get_text())

    for similar_image in soup.findAll('div', attrs={'rg_meta'}):
        tmp = json.loads(similar_image.get_text())
        img_url = tmp['ou']
        results['similar_images'].append(img_url)

    for best_guess in soup.findAll('a', attrs={'class':'fKDtNb'}):
      results['best_guess'] = best_guess.get_text()

    for image in soup.findAll('div', attrs={'id':'imagebox_bigimages'}):
        image_link=image.find('a')
        results['similar_images'].append('https://www.google.com'+image_link['href'])


    print("Successful search")

    return json.dumps(results)



def main():
    parser = argparse.ArgumentParser(description='Meta Reverse Image Search API')
    parser.add_argument('-p', '--port', type=int, default=5000, help='port number')
    #parser.add_argument('-d','--debug', action='store_true', help='enable debug mode')
    #parser.add_argument('-c','--cors', action='store_true', default=False, help="enable cross-origin requests")
    args = parser.parse_args()

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()
