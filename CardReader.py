'''
Created by Simon Possegger on 12.11.2019 as part of the Infineon Hackathon.
This Class asynchronously reads from the card reader
and provides the needed functions to interact with the Infineon Blockchain Security 2Go cards.
'''

import blocksec2go
import hashlib
import os
import json


def initReading():
    reader = get_reader()
    activate_card(reader)
    return reader


def get_reader():
    reader = None
    reader_name = 'Identiv uTrust 3700 F'
    while reader is None:
        try:
            reader = blocksec2go.find_reader(reader_name)
            print('Found reader %s' % reader_name)
        except Exception as details:
            if ('No reader found' == str(details)):
                print('No card reader found!', end='\r')
            elif ('No card on reader' == str(details)):
                print('Found reader, but no card!', end='\r')
            else:
                print('ERROR: ' + str(details))
                raise SystemExit
        return reader


def activate_card(reader):
    try:
        blocksec2go.select_app(reader)
        print('Found reader and Security 2Go card!')
    except Exception as details:
        print('ERROR: %s' % str(details))
        raise SystemExit


# Returns true if the card was initiated
def initCard(reader):
    try:
        if reader is not None:
            key_id = blocksec2go.generate_keypair(reader)
            print("Generated key on slot: %s" % str(key_id))
            return True
        else:
            return False
    except:
        return False


def read_public_key(reader, key_id):
    try:
        if blocksec2go.is_key_valid(reader, key_id):  # Check if key is valid
            global_counter, counter, key = blocksec2go.get_key_info(reader, key_id)
            return key
        else:
            return None
    except Exception as details:
        print('ERROR: ' + str(details))
        raise SystemExit


def auth(reader, pub):
    return verifyPub(reader, pub)


def generateSignature(reader, json_object=None):
    if json_object is None:
        hash = (hashlib.sha256(b'Hash' + bytearray(os.urandom(10000)))).digest()
    else:
        block_string = json.dumps(json_object, sort_keys=True)
        hash_object = hashlib.sha256(block_string.encode())
        hash = hash_object.digest()
    try:
        global_counter, counter, signature = blocksec2go.generate_signature(reader, 1, hash)
        return hash, signature
    except:
        return None, None


def verifyPub(reader, pub, hash=None, signature=None):
    # Generate random hash
    if signature is None:
        hash, signature = generateSignature(reader, hash)
    try:
        return blocksec2go.verify_signature(pub, hash, signature)
    except Exception as ex:
        print("Verification failed because of error: %s" % str(ex))
        return False


# testing:
def test():
    reader = initReading()
    print("Testing read pub:")
    pub = read_public_key(reader, 1)
    if pub is not None:
        print(pub.hex())
    else:
        print("No pub yet... creating one")
        print("Testing init card")
        print(initCard(reader))
        print("Testing read pub again:")
        pub = read_public_key(reader, 1)
        print(pub.hex())

    print("Testing auth:")
    print(auth(reader, read_public_key(reader, 1)))

    print("Testing verify pub with custom hash")
    hash = (hashlib.sha256(b'OtherHash' + bytearray(os.urandom(10000)))).digest()
    print(verifyPub(reader, read_public_key(reader, 1), hash))