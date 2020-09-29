import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import firestore
from os import path

opts = {
  'databaseURL': 'https://aptitude-cloud.firebaseio.com',
  'databaseAuthVariableOverride': {
    'uid': 'aptitude-box-service-worker'
  }
}
cred = credentials.Certificate(path.dirname(path.abspath(__file__)) + '/configs/aptitude-cloud-firebase-adminsdk-pv06k-64624c438a.json')
firebase_admin.initialize_app(credential=cred, options=opts)

box_ref = db.reference('boxes').child('proto-box')
if box_ref.get() == None:
  box_ref.set({
    "name": "Prototype-Box",
    "company": "PaceFactory Inc.",
    "location": "Oakville ON",
    "game-collection": {
      "face-one": "proto-box-simon-says"
    }
  })



