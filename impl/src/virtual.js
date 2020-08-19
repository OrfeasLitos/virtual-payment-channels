'use strict'

const bcoin = require('bcoin')
const assert = require('bsert')

const Scripts = require('./scripts')
const Utils = require('./utils')

const MTX = bcoin.MTX
const Coin = bcoin.Coin
const Script = bcoin.Script

function verifyArgs(inRings, outRings, amounts) {
  assert(inRings.length == 2)
  inRings.map(ring => {
    Utils.ensureWitness(ring)
    Utils.publicKeyVerify(ring.publicKey)
  })

  outRings.map(pair => assert(pair.length === 2))
  outRings.map(pair =>
    pair.map(ring => {
      Utils.ensureWitness(ring)
      Utils.publicKeyVerify(ring.publicKey)
    })
  )

  amounts.map(Utils.amountVerify)

  assert(outRings.length === amounts.length)
}

// A simplified version of the general virtual TX
// Only includes virtualised funding outputs
// TODO: add 0-value outputs
function getVirtualTX(inRings, outRings, amounts, ftx) {
  verifyArgs(inRings, outRings, amounts)

  let vtx = new MTX({version: 2})

  inRings[0].script = inRings[1].script = Script.fromMultisig(2, 2, [
      inRings[0].publicKey, inRings[1].publicKey
    ]
  )

  const prevoutScript = Utils.outputScrFromRedeemScr(inRings[1].script)

  const coin = Utils.getCoinFromTX(prevoutScript.toJSON(), ftx, 0)
  vtx.addCoin(coin)

  outRings.map(pair => {
    pair[0].script = pair[1].script = Script.fromMultisig(2, 2, [
        pair[0].publicKey, pair[1].publicKey
      ]
    )
  })

  const outputs = outRings.map(
    pair => Utils.outputScrFromRedeemScr(pair[1].script)
  )

  outputs.map((output, i) => vtx.addOutput(output, amounts[i]))

  vtx.sign(inRings, Script.hashType.SIGHASH_SINGLE)

  return vtx
}

module.exports = getVirtualTX
