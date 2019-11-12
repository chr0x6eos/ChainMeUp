'''
Created by Simon Possegger on 12.11.2019 as part of the Infineon Hackathon.
'''

import blocksec2go
import sys
import threading
from time import sleep
from blocksec2go.comm import observer


class CardReader(object):

    cardmonitor = None
    cardobserver = None

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

    def activate_card(self, reader):
        try:
            blocksec2go.select_app(reader)
        except Exception as details:
            print('ERROR: ' + str(details))
            raise SystemExit

    # TODO:handle new connection -> read card and make db query
    def connected(self):
        try:
            print("Connected\r\n")
            reader = self.get_reader()
            self.activate_card(reader)
            pub_key = self.get_public_key(reader, 1)
            print(str(pub_key))
            # Make db query with public key
        except RuntimeError as rex:
            print("Card is invalid!")
            sleep(1)
            self.restart()
        except:
            self.restart()

    # TODO:handle disconnect
    def disconnected(self):
        print('Disconnected\r\n')

    def initCard(self, reader):
        key_id = blocksec2go.generate_keypair(reader)
        print("Generated key on slot: " + str(key_id))

    def get_public_key(self, reader, key_id):
        try:
            if reader is not None:
                if blocksec2go.is_key_valid(reader, key_id):  # Check if key is valid
                    global_counter, counter, key = blocksec2go.get_key_info(reader, key_id)
                    return str(key)
            else:
                raise RuntimeError('Key_id is invalid!')
        except Exception as details:
            print('ERROR: ' + str(details))
            raise SystemExit


if '__main__' == __name__:
    CardReader = CardReader()
    print("Press enter to stop")
    sys.stdin.read(1)
