import blockchain

chain = blockchain.chain()

for i in range(1, 1000):
    chain.add_block({
        "publicKeySelf", "publicKeyOther"
    })
    block = chain.blocks[i]
    print(block)

#
chain2 = chain
#chain2.add_block({
#        "publicKeySelf", "publicKeyOther"
#    })
#
#chain.update_chain(chain2)

