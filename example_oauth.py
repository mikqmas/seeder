def getAuthToken(self, code):

    global client_id
    global merchant_id
    global code

    code = self.request.get('code')
    client_id = self.request.get('client_id')
    merchant_id = self.request.get('merchant_id')

    url = "https://sandbox.dev.clover.com/oauth/token?client_id=" + client_id + "&client_secret=" + CLIENT_SECRET + "&code=" + code

    try:
        result = urlfetch.fetch(url)
        if result.status_code == 200:
            return str(json.loads(result.content)['access_token'])
        else:
            self.response.status_code = result.status_code
    except:
        logging.exception('Caught exception')
