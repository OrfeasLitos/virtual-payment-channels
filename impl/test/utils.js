async function delay(milliseconds) {
  return new Promise((resolve, reject) => {
    setTimeout(resolve, milliseconds)
  })
}

module.exports = {
  mineBlock: async (node, rewardAddress) => {
    const block = await node.miner.mineBlock(node.chain.tip, rewardAddress)
    await node.chain.add(block)
    // node.chain.tip does not contain all the properties we want,
    // so we need to fetch it:
    return node.getBlock(node.chain.tip.hash)
  },

  flushEvents: async () => {
    return delay(100)
  },

  createWallet: async (walletDB, id) => {
    const options = {
      id,
      passphrase: 'secret',
      witness: true,
      type: 'pubkeyhash'
    }

    return walletDB.create(options)
  },
}
