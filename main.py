import blockchain
import time
import json
chain = blockchain.bc.Blockchain()

required_fields = ["publicKeyMe", "publicKeyYou"]
def new_transactions():
    for i in range(1,10):
        tx_data = {}
        tx_data['publicKeyMe'] = "key1"
        tx_data['publicKeyYou'] = "key2"

        for field in required_fields:
            if not tx_data.get(field):
                print( "Invlaid transaction data", 404)
            else:
                print("success")

            tx_data["timestamp"] = time.time()
        chain.add_new_transaction(tx_data)
        print(i)


def get_chain():
    chain_data = []
    for block in chain.chain:
        chain_data.append(block.__dict__)
    return json.dumps({"length": len(chain_data),
                       "chain": chain_data})

def mine_unconfirmed_transactions():
    result = chain.mine()
    print("result", result)
    if not result:
        return "No transactions to mine"
    return "Block #{} is mined.".format(result)

def get_pending_tx():
    return json.dumps(chain.unconfirmed_transactions)

new_transactions()
mine_unconfirmed_transactions()
print(get_chain())