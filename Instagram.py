"""
A sample application that uses the Instagram and Google Maps API's

knotthere@gmail.com
20140217
"""

import cherrypy
import os
import sys
import json
import urllib
import urllib2


gMsg = True
def showMsg(msg):
    if gMsg:
        sys.stdout.write('LTK: {0}\n'.format(msg))

class Instagram:

    client_id = "XXX"
    bing_map_key = "YYY"

    def __init__(self):
        access_log = os.path.join(os.path.dirname(__file__), 'logs/access_log')
        error_log = os.path.join(os.path.dirname(__file__), 'logs/error_log')
        cherrypy.config.update({'log.screen': False # On by default, but we can quiet it here
            # ,   'log.access_file': access_log
            # ,   'log.error_file': error_log
            })

        # Init my variables..
        self._mylist = []

        # Read Instagram Client_Id and bing_map_key from disk
        keyfile = open('Private_Ids_and_Keys.json', 'r')
        keys = json.loads(keyfile.read())
        self.client_id = keys['Instagram Client Id']
        self.bing_map_key = keys['Bing Map Key']
        showMsg('Initializing!')
        showMsg('Instagram: ' + self.client_id)
        showMsg('Bing: ' + self.bing_map_key)


    def index(self):
        # Ask for the user's name.
        f = open('Instagram.html', 'r')
        return f.read()

    index.exposed = True

    ''' Called by the timer on the Web Page '''
    def fetchone(self):
        if len(self._mylist) > 0:
            returnme = self._mylist.pop(0)
            showMsg('Serving: {0} - {1}'.format(returnme[0], returnme[3]))
            ''' Turns this array into a JSON String '''       
            return (json.dumps(returnme))
        else:
            return None
    fetchone.exposed = True


    ''' Keep a finite number of entries '''
    def add_item(self, addme):
        # Avoid duplicates
        for item in self._mylist:
            if item[2] == addme[2]:
                showMsg('Skipping Duplicate: {0} - {1}'.format(addme[0], addme[3]))
                return;
        showMsg('Adding [{2}]: {0} - {1}'.format(addme[0], addme[3], len(self._mylist)))
        self._mylist.append(addme)
   
    ''' Passed the location, call Bing and get the address for a tooltip '''
    def call_bing(self, location):
        baseUrl = 'http://dev.virtualearth.net/REST/v1/Locations/{0},{1}?key={2}'.format(
                str(location['latitude']),
                str(location['longitude']),
                self.bing_map_key)
        req = urllib2.Request(baseUrl)
        response = urllib2.urlopen(req)
        result = response.read()
        resultJson = json.loads(result)
        # Verify our call succeeded...
        if resultJson['statusCode'] == 200:
            # May not have an entry...
            resSets = resultJson['resourceSets']
            if (len(resSets) > 0):
                # Grab the first one
                res = resSets[0]['resources']
                if (len(res) > 0):
                    short_address = res[0]['name']
                else:
                    short_address = "(Bing returned no resources!)"
            else:
                short_address = "(Bing returned no resourceSets!)"
        else: 
            short_address = "(Bing error resultCode: " + str(resultJson['statusCode'])
        showMsg('Bing found: ' + short_address)
        return short_address

    ''' This is the callback method I registered with Instagram '''
    def instagram_cb(self, **kwargs):   #hub.verify_token = None, hub.challenge = None, hub.mode = None):
        """ Return hub.challenge  """
        method = cherrypy.request.method
        if 'GET' == method:
            ''' we are being authenticated '''
            showMsg("Instagram Challenge Received.")
            if kwargs and  'hub.challenge' in kwargs:
                ''' return what they want '''
                return kwargs['hub.challenge']
            showMsg("Expected, but did not get the Instagram Challenge!")

        elif 'POST' == method:
            ''' There are no arguments in this case, we are supposed to call back to the instagram API 
                to get the changed items.
                The body will have the subscription id and my client id, that's all.  '''
            showMsg('Instagram Change Notification Received.')

            # Bail if we are full...
            if len(self._mylist) > 50:
                showMsg('Our queue is full [{0!s}]'.format(len(self._mylist)))
                return

            bodyStr = str(cherrypy.request.body.read())
            bodyArgs = json.loads(bodyStr) # dumps() goes the other way
            ''' TODO: There could be multiple, both geoId's and Results!  
                I believe the number of items is how many we should retreive below.
                '''
            nUpdates = len(bodyArgs)
            if (nUpdates > 1):
                showMsg('Received {0!s} Updates !!!'.format(nUpdates))

            geoId = bodyArgs[0]['object_id']

            ''' Try to call Instagram API '''
            url = 'https://api.instagram.com/v1/geographies/' + str(geoId) + '/media/recent'
            # HTTPError: HTTP Error 405: METHOD NOT ALLOWED
            #values = { 'client_id': self.client_id, 'count': str(nUpdates) }
            url += "?client_id=" + self.client_id + "&count=" + str(nUpdates)
            data = None # urllib.urlencode(values)
            showMsg('Calling Instagram to get the Changed Items')
            req = urllib2.Request(url, data)
            response = urllib2.urlopen(req)
            result = response.read()
            resultJson = json.loads(result)

            ''' Find 'data', then spit out (array dictionaries) '''
            if 'data' in resultJson:
                data = resultJson['data']
                for item in data:

                    # Get location data from bing
                    short_address = self.call_bing(item['location'])

                    entry = [   item['user']['username']
                            ,   item['link']
                            ,   item['images']['low_resolution']['url']
                            ,   short_address
                            ,   item['location']
                            ]

                    self.add_item(entry)
            else:
                showMsg('No [data] in response! ')

    instagram_cb.exposed = True
    

''' Run us on load... '''

configfile = os.path.join(os.path.dirname(__file__), 'Instagram.conf')

if __name__ == '__main__':
    # CherryPy always starts with app.root when trying to map request URIs
    # to objects, so we need to mount a request handler root. A request
    # to '/' will be mapped to HelloWorld().index().
    cherrypy.quickstart(Instagram(), config=configfile)
else:
    # This branch is for the test suite; you can ignore it.
    cherrypy.tree.mount(Instagram(), config=configfile)
