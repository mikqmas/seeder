import webapp2
import os
import logging
import json
import pdb
import urlparse
import random
from faker import Faker

# Webpay
from Crypto.PublicKey import RSA
from base64 import b64encode

# GAE
from google.appengine.api import urlfetch
from google.appengine.ext.webapp import template

faker = Faker()

auth_token = None
merchant_id = None
client_id = None
CLIENT_SECRET = "19c36b3e-d632-5a1d-4e23-f5ee3ef5bdb6" # Change to your app

def getAuthToken(self, code):
    global client_id
    global merchant_id
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


class MainPage(webapp2.RequestHandler):
    def get(self):
        code = self.request.get('code')
        names = []
        if code:
            global auth_token
            auth_token = getAuthToken(self, code)

        for _ in range(20):
            names.append(faker.name())

        data = {'names': names}

        # print data
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, data))


class CreateCustomer(webapp2.RequestHandler):
    def post(self):
        global auth_token
        global merchant_id
        global client_id
        if auth_token:
            form_data = urlparse.parse_qs(self.request.body)

            url = 'https://sandbox.dev.clover.com/v3/merchants/{}/customers'.format( merchant_id )
            headers = {"Authorization": "Bearer " + auth_token, 'Content-Type': 'application/json'}

            results = []

            for _ in range(int(form_data['customer'][0])):
                post_data = json.dumps({
                    "firstName": faker.first_name(),
                    "lastName": faker.last_name()
                    # "emailAddresses": [faker.email()]
                })

                result = urlfetch.fetch(
                    url = url,
                    method = 'POST',
                    headers = headers,
                    payload = post_data
                )

                results.append(json.loads(result.content))

            path = os.path.join(os.path.dirname(__file__), 'created_customers.html')
            self.response.out.write(template.render(path, {'results': results}))


        else:
            self.redirect("https://sandbox.dev.clover.com/oauth/merchants/{}?client_id={}".format(merchant_id, client_id))


class CreateInventory(webapp2.RequestHandler):
    def post(self):
        global auth_token
        global merchant_id
        global client_id
        if auth_token:
            form_data = urlparse.parse_qs(self.request.body)

            url = 'https://sandbox.dev.clover.com/v3/merchants/{}/items'.format( merchant_id )
            headers = {"Authorization": "Bearer " + auth_token, 'Content-Type': 'application/json'}

            names = ["shirt", "pants", "ball", "dress", "stick", "rock", "drink", "burger", "fries", "flower", "shoes", "glasses",
             "spoon","bottle cap","nail clippers","candle","ice cube","slipper","thread","glow stick","needle","stop sign","blouse",
             "hanger","rubber duck","shovel","bookmark","model car","tampon","rubber band","tire swing","sharpie","picture frame",
             "photo album","nail filer","tooth paste","bath fizzers","tissue box","deodorant","cookie jar","rusty nail","drill press",
             "chalk","word search","thermometer","face wash","paint brush","candy wrapper","shoe lace","leg warmers","wireless control",
             "boom box","quilt","stockings","card","tooth pick","shawl","speakers","key chain","cork","helmet","mouse pad","zipper",
             "lamp shade","sketch pad","gage","plastic fork","flag","clay pot","check book","CD","#2 pencil","fake flowers","sticky note",
             "hair tie","credit card","sun glasses","seat belt","buckel","button","canvas","vase","lip gloss","rug","gel","twezzers","toe ring",
             "scotch tape","bow","white out","grid paper","earser","puddle","cement stone","sponge","lace","outlet","frizz control","sailboat",
             "screw","sand paper","eye liner","pool stick","pop can","balloon","spring","ipod charger","twister"]

            results = []

            for _ in range(int(form_data['inventory'][0])):
                post_data = json.dumps({
                    "name": random.choice(names),
                    "price": int(random.random()*(random.random()*10000))
                })

                result = urlfetch.fetch(
                    url = url,
                    method = 'POST',
                    headers = headers,
                    payload = post_data
                )

                results.append(json.loads(result.content))

            path = os.path.join(os.path.dirname(__file__), 'created_inventories.html')
            self.response.out.write(template.render(path, {'results': results}))


        else:
            self.redirect("https://sandbox.dev.clover.com/oauth/merchants/{}?client_id={}".format(merchant_id, client_id))

class CreateOrder(webapp2.RequestHandler):
    def post(self):
        global auth_token
        global merchant_id
        global client_id

        if auth_token:
            form_data = urlparse.parse_qs(self.request.body)

            url = 'https://sandbox.dev.clover.com/v3/merchants/{}/orders'.format( merchant_id )
            headers = {"Authorization": "Bearer " + auth_token, 'Content-Type': 'application/json'}

            results = []

            # Create form_data number of orders
            for _ in range(int(form_data['order'][0])):
                post_data = json.dumps({
                    "state": "open"
                })

                result = urlfetch.fetch(
                    url = url,
                    method = 'POST',
                    headers = headers,
                    payload = post_data
                )

                orderId = json.loads(result.content)['id']

                # Get all items in inventory (limit = 100)
                items = urlfetch.fetch(
                    url = 'https://sandbox.dev.clover.com/v3/merchants/{}/items?expand=taxRates'.format( merchant_id ),
                    method = 'GET',
                    headers = headers
                )

                items = json.loads(items.content)['elements']

                #Variable to hold total of all lineitems. Order total needs to be calc manually.
                ordertotal = 0

                #Seed random number of lineitems
                for _ in range(int(random.random()*5) + 1):
                    thisitem = random.choice(items)

                    #If there's tax, add to ordertotal
                    if thisitem['taxRates']['elements'] != []:
                        tax = thisitem['price'] * (thisitem['taxRates']['elements'][0]['rate']/10000000.0)
                    else:
                        tax = 0
                    ordertotal += (thisitem['price'] + tax)
                    post_data = json.dumps({
                        "item": {
                            "id": thisitem['id']
                          }
                    })

                    result = urlfetch.fetch(
                        url = 'https://sandbox.dev.clover.com/v3/merchants/{}/orders/{}/line_items'.format( merchant_id, orderId ),
                        method = 'POST',
                        headers = headers,
                        payload = post_data
                    )

                    results.append(json.loads(result.content))

                post_data = json.dumps({
                    "total": ordertotal
                })

                result = urlfetch.fetch(
                    url = 'https://sandbox.dev.clover.com/v3/merchants/{}/orders/{}'.format( merchant_id, orderId ),
                    method = 'POST',
                    headers = headers,
                    payload = post_data
                )

            path = os.path.join(os.path.dirname(__file__), 'created_orders.html')
            self.response.out.write(template.render(path, {'results': results}))


        else:
            self.redirect("https://sandbox.dev.clover.com/oauth/merchants/{}?client_id={}".format(merchant_id, client_id))


#Does not work right now because issues with GAE libraries
class CreatePayment(webapp2.RequestHandler):
    def post(self):
        global auth_token
        global merchant_id
        global client_id

        # CC info
        cardNumber = '4761739001010010'
        expMonth = 12
        expYear = 2018
        CVV = '201'

        if auth_token:
            # Getting secrets to encrypt cc info
            url = 'https://apisandbox.dev.clover.com/v2/merchant/{}/pay/key'.format( merchant_id )
            headers = {"Authorization": "Bearer " + auth_token}
            response = eval(urlfetch.fetch(url = url, headers = headers).content)

            modulus = long(response['modulus'])
            exponent = long(response['exponent'])
            prefix = long(response['prefix'])

            RSAkey = RSA.construct((modulus, exponent))



            publickey = RSAkey.publickey()
            encrypted = publickey.encrypt(cardNumber, prefix)
            cardEncrypted = b64encode(encrypted[0])

            url = 'https://apisandbox.dev.clover.com/v3/merchants/{}/orders?filter=state=open'.format( merchant_id )

            fetched = urlfetch.fetch(
                url = url,
                headers = headers
            )
            openOrders = json.loads(fetched.content)

            order = random.choice(openOrders['elements'])

            orderId = order['id']
            orderTotal = order['total']

            post_data = {
                "orderId": orderId,
                "currency": "usd",
                "amount": orderTotal,
                "expMonth": expMonth,
                "cvv": CVV,
                "expYear": expYear,
                "cardEncrypted": cardEncrypted,
                "last4": cardNumber[-4:],
                "first6": cardNumber[0:6]
            }

            posturl = 'https://apisandbox.dev.clover.com/v2/merchant/{}/pay'.format(merchant_id)
            postresponse = urlfetch.fetch(
                url = posturl,
                headers = headers,
                method='POST',
                payload = post_data
            )

            print postresponse.content

            # payment_id = eval(postresponse.content)['paymentId']

            # form_data = urlparse.parse_qs(self.request.body)
            #
            # url = 'https://sandbox.dev.clover.com/v3/merchants/{}/payments/{}'.format( merchant_id, payment_id )
            # headers = {"Authorization": "Bearer " + auth_token, 'Content-Type': 'application/json'}
            #
            # results = []
            #
            # result = urlfetch.fetch(
            #     url = url,
            #     method = 'POST',
            #     headers = headers,
            #     payload = post_data
            # )
            #
            # results.append(json.loads(result.content))

            # path = os.path.join(os.path.dirname(__file__), 'created_customers.html')
            # self.response.out.write(template.render(path, {'results': results}))


        else:
            self.redirect("https://sandbox.dev.clover.com/oauth/merchants/{}?client_id={}".format(merchant_id, client_id))

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/customer/create', CreateCustomer),
    ('/inventory/create', CreateInventory),
    ('/order/create', CreateOrder),
    ('/payment/create', CreatePayment)
], debug=True)
