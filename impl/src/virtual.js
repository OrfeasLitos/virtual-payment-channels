'use strict'

const bcoin = require('bcoin')
const assert = require('bcoin/node_modules/bsert')

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
function getVirtualTX({inRings, outRings, amounts, fee, fundingTX}) {
  verifyArgs(inRings, outRings, amounts)

  let virtualTX = new MTX({version: 2})

  inRings[0].script = inRings[1].script = Script.fromMultisig(2, 2, [
      inRings[0].publicKey, inRings[1].publicKey
    ]
  )

  const prevoutScript = Utils.outputScrFromRedeemScr(inRings[1].script)

  const coin = Utils.getCoinFromTX(prevoutScript.toJSON(), fundingTX, 0)
  virtualTX.addCoin(coin)

  outRings.map(pair => {
    pair[0].script = pair[1].script = Script.fromMultisig(2, 2, [
        pair[0].publicKey, pair[1].publicKey
      ]
    )
  })

  const outputs = outRings.map(
    pair => Utils.outputScrFromRedeemScr(pair[1].script)
  )

  outputs.map((output, i) => virtualTX.addOutput(output, amounts[i]))
  virtualTX.outputs[0].value -= fee

  virtualTX.sign(inRings)

  return virtualTX
}

module.exports = getVirtualTX
