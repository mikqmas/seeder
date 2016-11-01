import webapp2
import os
import logging
import json
import pdb
import urlparse
import random

# # Webpay
# from Crypto.PublicKey import RSA
# from base64 import b64encode

from google.appengine.api import urlfetch
from client_secret import *

from google.appengine.ext.webapp import template
from faker import Faker
faker = Faker()

auth_token = None
merchant_id = None
client_id = None

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

        print data
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, data))

        # self.response.headers['Content-Type'] = 'text/html';
        # self.response.write("<script src='./frontend/bundle.js'></script><div id='root' />");


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

            names = ["shirt", "pants", "ball", "dress", "stick"]

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

                items = urlfetch.fetch(
                    url = 'https://sandbox.dev.clover.com/v3/merchants/{}/items'.format( merchant_id ),
                    method = 'GET',
                    headers = headers
                )


                items = json.loads(items.content)['elements']


                for _ in range(int(random.random()*5) + 1):
                    post_data = json.dumps({
                        "item": {
                            "id": random.choice(items)['id']
                          }
                    })

                    result = urlfetch.fetch(
                        url = 'https://sandbox.dev.clover.com/v3/merchants/{}/orders/{}/line_items'.format( merchant_id, orderId ),
                        method = 'POST',
                        headers = headers,
                        payload = post_data
                    )

                    results.append(json.loads(result.content))

            path = os.path.join(os.path.dirname(__file__), 'created_orders.html')
            self.response.out.write(template.render(path, {'results': results}))


        else:
            self.redirect("https://sandbox.dev.clover.com/oauth/merchants/{}?client_id={}".format(merchant_id, client_id))


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

            openOrders = eval(urlfetch.fetch(
                url = url,
                headers = headers
            ).content)

            order = random.choice(openOrders['elements'])

            orderId = order['id']
            orderTotal = order['total']

            post_data = {
                "orderId": orderId,
                "amount": orderTotal,
                "expMonth": expMonth,
                "cvv": CVV,
                "expYear": expYear,
                "cardEncrypted": cardEncrypted,
                "last4": cardNumber[-4:],
                "first6": cardNumber[0:6]
            }

            posturl = 'https://apisandbox.dev.clover.com/v2/merchant/EJE2ZH35JJAG2/pay'
            postresponse = urlfetch.fetch(
                url = posturl,
                headers = headers,
                method='POST',
                data = post_data
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
