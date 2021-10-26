'use strict'

const bcoin = require('bcoin')
const assert = require('bcoin/node_modules/bsert')

const Scripts = require('./scripts')
const Utils = require('./utils')

const MTX = bcoin.MTX
const Coin = bcoin.Coin
const Script = bcoin.Script

function verifyArgs(rings, delay, amounts) {
  Object.values(rings).map(Utils.ensureWitness)
  Object.values(rings).map(ring => Utils.publicKeyVerify(ring.publicKey))
  Utils.delayVerify(delay)
  Object.values(amounts).map(Utils.amountVerify)
}

function getOutput(aliceKey, bobKey, delay, delKey, amount) {
  const [key1, key2] = Utils.sortKeys(aliceKey, bobKey)
  const redeemScript = Scripts.commitmentScript(key1, key2, delay, delKey)
  return Utils.outputScrFromRedeemScr(redeemScript)
}

function getCommitmentTX({
  rings: {
    aliceFundRing, bobFundRing, aliceRevRing,
    aliceDelRing, bobRevRing, bobOwnRing
  },
  delay,
  amounts: {aliceAmount, bobAmount, fee},
  fundingTX,
  fundingIndex,
}) {
  const arg = arguments[0]
  verifyArgs(arg.rings, arg.delay, arg.amounts)

  aliceFundRing.script = bobFundRing.script = Script.fromMultisig(2, 2, [
    aliceFundRing.publicKey, bobFundRing.publicKey
  ])
  const outputScript = Utils.outputScrFromRedeemScr(aliceFundRing.script)

  let ctx = new MTX({version: 2})

  const aliceOutput = getOutput(
    aliceRevRing.publicKey, bobRevRing.publicKey,
    delay, aliceDelRing.publicKey
  )
  ctx.addOutput(aliceOutput, aliceAmount - fee)

  const bobOutput = Utils.getP2WPKHOutput(bobOwnRing)
  ctx.addOutput(bobOutput, bobAmount)

  const coin = Utils.getCoinFromTX(outputScript.toJSON(), fundingTX, fundingIndex)
  ctx.addCoin(coin)

  ctx.sign([aliceFundRing, bobFundRing])

  return ctx
}

module.exports = getCommitmentTX
