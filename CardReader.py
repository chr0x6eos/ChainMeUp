'''
Created by Simon Possegger on 12.11.2019 as part of the Infineon Hackathon.
This Class asynchronously reads from the card reader
and provides the needed functions to interact with the Infineon Blockchain Security 2Go cards.
'''

import blocksec2go
import sys
import threading
import hashlib
import os
from time import sleep
from blocksec2go.comm import observer

class CardReader(object):

    cardmonitor = None
    cardobserver = None
    #last_pub = None
    current_pub = None
    reader = None

    def __init__(self, interval=0.5):
        self.interval = interval
        thread = threading.Thread(target=self.run, args=(), daemon=True)
        thread.start()

    def run(self):
        try:
            self.cardmonitor, self.cardobserver = observer.start()
            sleep(1)
            blocksec2go.add_callback(connect=self.connected, disconnect=self.disconnected)
            while True:
                sleep(self.interval)
        except:
            self.restart()

    def restart(self):
        if self.cardmonitor is not None and self.cardobserver is not None:
            observer.stop(self.cardmonitor, self.cardobserver)
        sleep(self.interval)
        self.run()

    def get_reader(self):
        reader = None
        reader_name = 'Identiv uTrust 3700 F'
        while reader is None:
            try:
                reader = blocksec2go.find_reader(reader_name)
            except:
                pass
        return reader

    def activate_card(self):
        try:
            blocksec2go.select_app(self.reader)
        except Exception as details:
            print('ERROR: %s' % str(details))
            raise SystemExit

    # TODO:handle new connection -> read card and make db query
    def connected(self):
        try:
            print("Connected\r\n")
            self.reader = self.get_reader()
            self.activate_card()
            # if self.current_pub is None and self.last_pub is None:
            #    self.last_pub = self.current_pub = self.read_public_key(1)
            #else:
            #    self.last_pub = self.current_pub # Save current pub before overwriting
            #    self.current_pub = self.read_public_key(1)

            self.current_pub = self.read_public_key(1)
            if self.current_pub is not None:
                print("Public key read: %s with a length of: %d" % (str(self.current_pub.hex()) + len(self.current_pub)))
        except RuntimeError as rex:
            print("Card is invalid!")
            sleep(1)
            self.restart()
        except:
            self.restart()

    # TODO:handle disconnect
    def disconnected(self):
        print('Disconnected\r\n')

    # Returns true if the card was initiated
    def initCard(self):
        try:
            key_id = blocksec2go.generate_keypair(self.reader)
            print("Generated key on slot: %s" % str(key_id))
            return True
        except:
            return False

    def read_public_key(self, key_id):
        try:
            if self.reader is not None:
                if blocksec2go.is_key_valid(self.reader, key_id):  # Check if key is valid
                    global_counter, counter, key = blocksec2go.get_key_info(self.reader, key_id)
                    if key is not None:
                        return key
                    else:
                        return None
                else:
                    return None
            else:
                return None
        except Exception as details:
            print('ERROR: ' + str(details))
            raise SystemExit

    # Returns last read public key
    def get_Pub_hex(self):
        return self.current_pub.hex()

    def get_Pub(self):
        return self.current_pub

    def auth(self, pub):
            return self.verifyPub(pub)

    def generateSignature(self,hash=None):
        if hash is None:
            hash = (hashlib.sha256(b'Hash' + bytearray(os.urandom(10000)))).digest()
        try:
            global_counter, counter, signature = blocksec2go.generate_signature(self.reader, 1, hash)
            return hash,signature
        except:
            return None,None

    def verifyPub(self, pub, hash=None, signature=None):
        # Generate random hash
        if signature is None:
            hash, signature = self.generateSignature(hash)
        try:
            return blocksec2go.verify_signature(pub, hash, signature)
        except Exception as ex:
            print("Verification failed because of error: %s" % str(ex))
            return False

if '__main__' == __name__:
    CardReader = CardReader()
    print("Press enter to authenticate")
    sys.stdin.read(1)
    print(CardReader.auth(CardReader.get_Pub()))