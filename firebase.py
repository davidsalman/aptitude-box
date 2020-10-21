import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import firestore
from os import path
from time import sleep

# Constants

CRED = credentials.Certificate(path.dirname(path.abspath(__file__)) + '/configs/aptitude-cloud-firebase-adminsdk-pv06k-64624c438a.json')
OPTS = {
  'databaseURL': 'https://aptitude-cloud.firebaseio.com',
  'databaseAuthVariableOverride': {
    'uid': 'aptitude-box-service-worker'
  },
  'projectId': 'aptitude-cloud'
}

# Main
initialzed = False
while not initialzed:
  try:
    firebase_admin.initialize_app(credential=CRED, options=OPTS)
    store = firestore.client()
    initialzed = True
  except ValueError:
    print('Waiting for Firebase to initialize ...')
    sleep(1)
