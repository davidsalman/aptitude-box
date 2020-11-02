from firebase import db

# Constants

BOX_DB = 'boxes'
BOX_ID = 'proto-box'
BOX_NAME = 'Prototype-Box'

# Main

box_ref = db.reference(BOX_DB).child(BOX_ID)
if box_ref.get() == None:
  box_ref.set({
    'name': BOX_NAME,
    'company': 'PaceFactory Inc.',
    'location': 'Oakville ON',
    'game-collection': {
      'face-one': BOX_ID + '-simon-says',
      'face-two': BOX_ID + '-follow-the-leader',
      'face-three': BOX_ID + '-push-pull',
      'face-four': BOX_ID + '-under-pressure',
      'face-five': BOX_ID + '-dial-it-in'
    }
  })