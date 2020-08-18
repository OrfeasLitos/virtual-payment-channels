'use strict'


const bcoin = require('bcoin')
const sha256 = require('bcrypto/lib/sha256')
const assert = require('bsert')

const KeyRing = bcoin.KeyRing
const Amount = bcoin.Amount
const Script = bcoin.Script
const Outpoint = bcoin.Outpoint
const MTX = bcoin.MTX
const Input = bcoin.Input
const Witness = bcoin.Witness
const Coin = bcoin.Coin

const Vchan = require('../src/vchan')

const rings = Array.apply(null, Array(8))
      .map(x => KeyRing.generate())
rings.map(ring => {ring.witness = true})

const delay = 42

const fundingHash = sha256.digest(Buffer.from('funding'))

const aliceAmount = Amount.fromBTC(10).toValue()
const bobAmount = Amount.fromBTC(20).toValue()
const fundingFee = 2330
const commitmentFee = 14900
const revocationFee = 8520

const aliceOrigRing = rings[0]
const aliceFundRing = rings[1]
const bobFundRing = rings[2]
const aliceRevRing = rings[3]
const bobRevRing = rings[4]
const aliceDelRing = rings[5]
const bobDelRing = rings[6]
const bobOwnRing = rings[7]

describe('End-to-end test', () => {
  const ftx = Vchan.getFundingTX({
    outpoint: new Outpoint(fundingHash, 0),
    ring: aliceOrigRing,
    fundKey1: aliceFundRing.publicKey,
    fundKey2: bobFundRing.publicKey,
    outAmount: aliceAmount + bobAmount
  })

  describe('Funding TX', () => {
    it('should verify correctly', () => {
      assert(ftx.verify(),
        'Funding TX does not verify correctly')
    })

    let ftx2 = new MTX({version: 2})

    ftx2.addCoin(Coin.fromJSON({
      version: 2,
      height: -1,
      value: aliceAmount + bobAmount,
      coinbase: false,
      script: aliceOrigRing.getProgram().toRaw().toString('hex'),
      hash: fundingHash.toString('hex'),
      index: 0
    }))

    ftx2 = Vchan.getFundingTX({
      fctx: ftx2, fundKey1: aliceFundRing.publicKey,
      fundKey2: bobFundRing.publicKey, outAmount: aliceAmount + bobAmount
    })

    ftx2.sign(aliceOrigRing)

    it('should be generatable both from MTX and from KeyRing', () => {
      assert(ftx.hash().equals(ftx2.hash()) &&
        ftx.witnessHash().equals(ftx2.witnessHash()),
        'The two funding TX generation methods do not produce same results')
    })
  })

  const commTX = Vchan.getCommitmentTX({
    rings: {
      aliceFundRing, bobFundRing,
      aliceRevRing, aliceDelRing,
      bobRevRing, bobOwnRing
    },
    delay,
    amount: {aliceAmount, bobAmount, fee: fundingFee},
    ftx
  })

  describe('Commitment TX', () => {
    it('should verify correctly', () => {
      assert(commTX.verify(),
        'Commitment TX does not verify correctly')
    })

    const fundingWitnessHash = ftx.outputs[0].script.code[1].data
    const commWitnessScript = commTX.inputs[0].witness.getRedeem().sha256()
    it('should spend Funding TX', () => {
      assert(fundingWitnessHash.equals(commWitnessScript),
        'Funding output witness hash doesn\'t correspond to commitment input witness script')
    })
  })

  const rtx = Vchan.getRevocationTX({
    rings: {
      aliceRevRing, bobRevRing,
      aliceDelRing, bobDelRing, bobOwnRing
    },
    delay, commTX,
    fee: revocationFee
  })

  describe('Revocation TX', () => {
    it('should verify correctly', () => {
      assert(rtx.verify(),
        'Revocation TX does not verify correctly')
    })

    const aliceWitnessHash = commTX.outputs[0].script.code[1].data
    const aliceWitnessScript = rtx.inputs[0].witness.getRedeem().sha256()
    it('should spend Commitment TX output 0', () => {
      assert(aliceWitnessHash.equals(aliceWitnessScript),
        'Alice output witness hash doesn\'t correspond to revocation input witness script')
    })
  })
})
