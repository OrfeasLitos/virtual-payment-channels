'use strict'

const bcoin = require('bcoin')
const assert = require('bsert')

const Scripts = require('./scripts')
const Utils = require('./utils')

const MTX = bcoin.MTX
const Script = bcoin.Script
const Coin = bcoin.Coin
const Stack = bcoin.Stack

function verifyArgs(rings, delay, commTX, fee) {
  Object.values(rings).map(Utils.ensureWitness)
  Object.values(rings).map(ring => Utils.publicKeyVerify(ring.publicKey))
  Utils.delayVerify(delay)
  Utils.ensureCommitmentTX(commTX)
  Utils.amountVerify(fee)
}

function getOutput(ring) {
  return Utils.getP2WPKHOutput(ring)
}

function getRevocationTX({
  rings: {
    aliceRevRing, bobRevRing,
    aliceDelRing, bobDelRing, bobOwnRing
  },
  delay, commTX, fee
}) {
  verifyArgs(arguments[0].rings, arguments[0].delay, commTX, fee)

  const [key1, key2] = Utils.sortKeys(aliceRevRing.publicKey, bobRevRing.publicKey)
  aliceRevRing.script = bobRevRing.script = Scripts.commitmentScript(
    key1, key2, delay, aliceDelRing.publicKey
  )
  const outputScript = Utils.outputScrFromRedeemScr(aliceRevRing.script)

  const rtx = new MTX({version: 2})

  const output = getOutput(bobOwnRing)
  const value = commTX.outputs[0].value + commTX.outputs[1].value - fee
  rtx.addOutput(output, value)

  const coin = Utils.getCoinFromTX(outputScript.toJSON(), commTX, 0)
  rtx.addCoin(coin)

  Utils.sign(rtx, Utils.sortRings(aliceRevRing, bobRevRing), 0, Scripts.cheatWitScr)

  return rtx
}

module.exports = getRevocationTX
