#!/usr/bin/env python3


"""ombibot.py: API for making API calls to sonarr/lidarr/radarr servers."""

__author__      = "Jools"
__email__       = "springjools@gmail.com"
__copyright__   = "Copyright 2019"

# Copyright 2019 Jools Holland

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.



import requests
import json
import logging
log = logging.getLogger(__name__)

httpErrors = {
    200 : 'OK',
    201 : 'Created',
    202 : 'Accepted',
    203 : 'Non-authoritative Information',
    204 : 'No Content',
    205 : 'Reset Content',
    206 : 'Partial Content',
    207 : 'Multi-Status',
    208 : 'Already Reported',
    226 : 'IM Used',
    300 : 'Multiple Choices',
    301 : 'Moved Permanently',
    302 : 'Found',
    303 : 'See Other',
    304 : 'Not Modified',
    305 : 'Use Proxy',
    307 : 'Temporary Redirect',
    308 : 'Permanent Redirect',
    400 : 'Bad Request',
    401 : 'Unauthorized',
    402 : 'Payment Required',
    403 : 'Forbidden',
    404 : 'Not Found',
    405 : 'Method Not Allowed',
    406 : 'Not Acceptable',
    407 : 'Proxy Authentication Required',
    408 : 'Request Timeout',
    409 : 'Conflict',
    410 : 'Gone',
    411 : 'Length Required',
    412 : 'Precondition Failed',
    413 : 'Payload Too Large',
    414 : 'Request-URI Too Long',
    415 : 'Unsupported Media Type',
    416 : 'Requested Range Not Satisfiable',
    417 : 'Expectation Failed',
    418 : 'I\'m a teapot',
    421 : 'Misdirected Request',
    422 : 'Unprocessable Entity',
    423 : 'Locked',
    424 : 'Failed Dependency',
    426 : 'Upgrade Required',
    428 : 'Precondition Required',
    429 : 'Too Many Requests',
    431 : 'Request Header Fields Too Large',
    444 : 'No Response (Nginx)',
    451 : 'Unavailable For Legal Reasons',
    499 : 'Client Closed Request',
    500 : 'Internal Server Error',
    501 : 'Not Implemented',
    502 : 'Bad Gateway',
    503 : 'Service Unavailable',
    504 : 'Gateway Timeout',
    505 : 'HTTP Version Not Supported',
    506 : 'Variant Also Negotiates',
    507 : 'Insufficient Storage',
    508 : 'Loop Detected',
    510 : 'Not Extended',
    511 : 'Network Authentication Required',
    522 : 'Connection timed out, server denied request for OAuth token',
    599 : 'Network Connect Timeout Error'}

class HTTP_MethodError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class OmbiServer(object):
    def __init__(self, server, apikey, port=5000, baseUrl='/ombi', userName='guest'):
        self.api_key    = apikey
        self.userName   = userName
        self.endpoint   = server + ':' + str(port) + baseUrl + '/api/v1'
         
        log.info ("Endpoint is {}".format(self.endpoint))

    def search_movies(self, title):
        """ Get queue from server
        """

        # Create and send HTTP Get to the server
        h={
            'http.useragent' : 'ombi-server',
            'ApiKey'      :     self.api_key,
            'Content-Type'   : 'application/json',
            'User-Agent'     : 'Ombi/server',
            'Accept-Encoding': 'gzip'
        }
           
        try:
            url = self.endpoint + '/Search/movie/' +str(title)
            log.debug("Sending GET request to {}".format(url))
            r = requests.get(url, headers=h,timeout=30)
        except Exception as e:
            raise HTTP_MethodError('Error Connecting to server: {}'.format(e))
        
        log.debug("HTTP {}: {}".format(r.status_code,httpErrors[r.status_code]))
        output = {}
        
        if r.status_code == 200: #200 = 'OK'
            
            parsedata = r.json()
            log.debug("type = {}, len = {}".format(type(parsedata),len(parsedata)))
            
            try:
                for data in parsedata:
                    #log.info("Parsing {} data: {}".format(self.type,data))
                    output[data.get('title')] = {'id':data.get('id'),'title':data.get('title'), 'available':data.get('available'),'requested':data.get('requested'),'releaseDate':data.get('releaseDate')}
                    
            except Exception as e:
                log.error("Invalid server type: {}, {}".format(self.type,e))
                
                
        log.info("Returning {} records".format(len(output)))
        return output
     
    def search_movies_actor(self, actor,languageCode='en'):
        """ Get queue from server
        """

        # Create and send HTTP Get to the server
        headers = {
            'http.useragent' : 'ombi-server',
            'ApiKey'      :     self.api_key,
            'Content-Type'   : 'application/json',
            'Accept-Encoding': 'gzip',
            'User-Agent'     : 'Ombi/server'
        }
        
        payload = {
            "searchTerm": actor,
            "languageCode": "en"
        }

        try:
            url = self.endpoint + '/Search/movie/actor'
            log.info("Sending POST request to {} with data = {}, {}".format(url,payload,json.dumps(payload)))
            
            r = requests.post(url = url, headers = headers, data = json.dumps(payload))
        except Exception as e:
            raise HTTP_MethodError('Error Connecting to server: {}'.format(e))
        
        log.debug("HTTP {}: {}".format(r.status_code,httpErrors[r.status_code]))
        log.debug("Response = {}".format(r.text))
        log.debug("Url = {}".format(r.url))
        
        output = {}
        if r.status_code == 200: #200 = 'OK'
            
            parsedata = r.json()
            log.debug("type = {}, len = {}".format(type(parsedata),len(parsedata)))
            
            try:
                for data in parsedata:
                    #log.info("Parsing {} data: {}".format(self.type,data))
                    output[data.get('title')] = {'id':data.get('id'),'title':data.get('title'), 'available':data.get('available'),'requested':data.get('requested'),'releaseDate':data.get('releaseDate')}
                    
            except Exception as e:
                log.error("Unable to process search: {}".format(e))
                
                
        log.info("Returning {} records".format(len(output)))
        return output
 
    def request_movie(self, movieID,user,languageCode='en'):
        """ Get queue from server
        """

        # Create and send HTTP Get to the server
        headers = {
            'http.useragent'    : 'ombi-server',
            'ApiKey'            : self.api_key,
            'UserName'          : user,
            'Content-Type'      : 'application/json',
            'Accept-Encoding'   : 'gzip',
            'User-Agent'        : 'Ombi/server'
        }
        
        payload = {
            'theMovieDbId': int(movieID),
            'languageCode': 'en'
        }

        try:
            url = self.endpoint + '/Request/movie'
            log.debug("Sending POST request to {} with headers = {}".format(url,headers))
            
            r = requests.post(url = url, headers = headers, data = json.dumps(payload))
        except Exception as e:
            raise HTTP_MethodError('Error Connecting to server: {}'.format(e))
        
        log.debug("HTTP {}: {}".format(r.status_code,httpErrors[r.status_code]))
        log.debug("Response = {}".format(r.text))
        log.debug("Url = {}".format(r.url))
        
        if r.status_code == 200: #200 = 'OK'
        
            response = r.json()
            message = response.get('message') if response.get('result') else response.get('errorMessage')
                 
            log.info("Result: {} Message: {}".format(response.get('result') if response else None,message))
            return message
        else:
            log.error("Unable to handle request: {}, {}".format(r.status_code,r.text))
            return False
    
    def find_similar(self, movieID,languageCode='en'):
        """ Get similar movies from server
        """

        # Create and send HTTP Get to the server
        headers = {
            'http.useragent' : 'ombi-server',
            'ApiKey'      :     self.api_key,
            'Content-Type'   : 'application/json',
            'Accept-Encoding': 'gzip',
            'User-Agent'     : 'Ombi/server'
        }
        
        payload = {
            'theMovieDbId': int(movieID),
            'languageCode': 'en'
        }

        try:
            url = self.endpoint + '/Search/movie/similar'
            log.debug("Sending POST request to {} with data = {}, {}".format(url,payload,json.dumps(payload)))
            
            r = requests.post(url = url, headers = headers, data = json.dumps(payload))
        except Exception as e:
            raise HTTP_MethodError('Error Connecting to server: {}'.format(e))
        
        log.debug("HTTP {}: {}".format(r.status_code,httpErrors[r.status_code]))
        log.debug("Response = {}".format(r.text))
        log.debug("Url = {}".format(r.url))

        output = {}
        
        if r.status_code == 200: #200 = 'OK'
            
            parsedata = r.json()
            log.debug("type = {}, len = {}".format(type(parsedata),len(parsedata)))
            
            try:
                for data in parsedata:
                    #log.info("Parsing {} data: {}".format(self.type,data))
                    output[data.get('title')] = {'id':data.get('id'),'title':data.get('title'), 'available':data.get('available'),'requested':data.get('requested'),'releaseDate':data.get('releaseDate')}
                    
            except Exception as e:
                log.error("Invalid server type: {}, {}".format(self.type,e))
                
                
        log.info("Returning {} records".format(len(output)))
        return output

    def get_movie_info(self, movieID,languageCode='en'):
        """ Get extra movie information from server
        """
        log.debug("Got id: {}".format(movieID))
        
        # Create and send HTTP Get to the server
        headers = {
            'http.useragent' : 'ombi-server',
            'ApiKey'      :     self.api_key,
            'Content-Type'   : 'application/json',
            'Accept-Encoding': 'gzip',
            'User-Agent'     : 'Ombi/server'
        }
        
        payload = {
            'theMovieDbId': int(movieID),
            'languageCode': 'en'
        }

        try:
            url = self.endpoint + '/Search/movie/info'
            log.debug("Sending POST request to {} with data = {}, {}".format(url,payload,json.dumps(payload)))
            
            r = requests.post(url = url, headers = headers, data = json.dumps(payload))
        except Exception as e:
            raise HTTP_MethodError('Error Connecting to server: {}'.format(e))
        
        log.debug("HTTP {}: {}".format(r.status_code,httpErrors[r.status_code]))
        log.debug("Response = {}".format(r.text))
        log.debug("Url = {}".format(r.url))

        output = {}
        
        if r.status_code == 200: #200 = 'OK'
            parsedata = r.json()
            log.debug("Text = {}".format(r.text))
            if parsedata:
                data = parsedata
                output = {'id':data.get('id'), 'overView': data.get('overview'), 'voteCount':data.get('voteCount'),'voteAverage':data.get('voteAverage'),'title':data.get('title'), 'available':data.get('available'),'requested':data.get('requested'),'releaseDate':data.get('releaseDate')}    
        
        log.info("Returning {} fields: {}".format(len(output),output))
        
        return output