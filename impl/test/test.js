'use strict'

const bcoin = require('bcoin').set('regtest')
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
const Utils = require('./utils')

const rings = Array.apply(null, Array(10))
      .map(x => KeyRing.generate())
rings.map(ring => {ring.witness = true})

const delay = 42

const fundingHash = sha256.digest(Buffer.from('funding'))

const aliceAmount = Amount.fromBTC(10).toValue()
const bobAmount = Amount.fromBTC(40).toValue()
const fundingFee = 2330
const commitmentFee = 14900
const revocationFee = 8520
const virtualFee = 8520 // attention: chosen somewhat arbitrarily

const aliceOrigRing = rings[0]
const aliceFundRing1 = rings[1]
const aliceFundRingPrivateKey = aliceFundRing1.getPrivateKey()
const aliceFundRing2 = KeyRing.fromPrivate(aliceFundRingPrivateKey)
aliceFundRing2.witness = true
const aliceVirtRing1 = KeyRing.fromPrivate(aliceFundRingPrivateKey)
aliceVirtRing1.witness = true
const aliceVirtRing2 = KeyRing.fromPrivate(aliceFundRingPrivateKey)
aliceVirtRing2.witness = true
const aliceVirtRing3 = KeyRing.fromPrivate(aliceFundRingPrivateKey)
aliceVirtRing3.witness = true
const bobFundRing1 = rings[2]
const bobFundRingPrivateKey = bobFundRing1.getPrivateKey()
const bobFundRing2 = KeyRing.fromPrivate(bobFundRingPrivateKey)
bobFundRing2.witness = true
const bobVirtRing = KeyRing.fromPrivate(bobFundRingPrivateKey)
bobVirtRing.witness = true
const aliceRevRing = rings[3]
const bobRevRing = rings[4]
const aliceDelRing = rings[5]
const bobDelRing = rings[6]
const bobOwnRing = rings[7]
const charlieFundRing = rings[8]
const charlieVirtRing = KeyRing.fromPrivate(charlieFundRing.getPrivateKey())
charlieVirtRing.witness = true
const daveVirtRing = rings[9]

describe('End-to-end test', () => {
  const ftx = Vchan.getFundingTX({
    outpoint: new Outpoint(fundingHash, 0),
    ring: aliceOrigRing,
    fundKey1: aliceFundRing1.publicKey,
    fundKey2: bobFundRing1.publicKey,
    outAmount: aliceAmount + bobAmount,
    fee: fundingFee,
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
      hash: fundingHash.reverse().toString('hex'),
      index: 0,
    }))

    ftx2 = Vchan.getFundingTX({
      fctx: ftx2, fundKey1: aliceFundRing1.publicKey,
      fundKey2: bobFundRing1.publicKey,
      outAmount: aliceAmount + bobAmount,
      fee: fundingFee,
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
      aliceFundRing: aliceFundRing1,
      bobFundRing: bobFundRing1,
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

  const baseAmount = Amount.fromBTC(30).toValue()
  const virt1Amount = Amount.fromBTC(15).toValue()
  const virt2Amount = Amount.fromBTC(5).toValue()

  const virtualTX = Vchan.getVirtualTX(
    [aliceFundRing2, bobFundRing2],
    [
      [aliceVirtRing1, bobVirtRing],
      [aliceVirtRing2, daveVirtRing]
    ],
    [baseAmount - virt1Amount, virt1Amount],
    ftx
  )

  describe('Virtual TX', () => {
    it('should verify correctly', () => {
      assert(virtualTX.verify(),
        'Virtual TX does not verify correctly')
    })

    const fundingWitnessHash = ftx.outputs[0].script.code[1].data
    const virtWitnessScript = virtualTX.inputs[0].witness.getRedeem().sha256()
    it('should spend Funding TX', () => {
      assert(fundingWitnessHash.equals(virtWitnessScript),
        'Funding output witness hash doesn\'t correspond to virtual input witness script')
    })

    describe('Virtualized output', () => {
      const virtualWitnessHash = virtualTX.outputs[0].script.code[1].data
      const commWitnessScript = commTX.inputs[0].witness.getRedeem().sha256()
      it('should be spendable by commitment TX', () => {
        assert(virtualWitnessHash.equals(commWitnessScript),
          '1st virtual output witness hash doesn\'t correspond to commitment input witness script')
      })
    })

    describe('Updated Virtual TX', () => {
      const virtualTX2 = Vchan.getVirtualTX(
        [aliceFundRing2, bobFundRing2],
        [
          [aliceVirtRing1, bobVirtRing],
          [aliceVirtRing2, daveVirtRing],
          [aliceVirtRing3, charlieVirtRing]
        ],
        [baseAmount - virt1Amount - virt2Amount, virt2Amount, virt1Amount],
        ftx
      )

      const virtualWitnessHash = virtualTX2.outputs[0].script.code[1].data
      const commWitnessScript = commTX.inputs[0].witness.getRedeem().sha256()
      describe('Virtualized output', () => {
        it('should still be spendable by commitment TX', () => {
          assert(virtualWitnessHash.equals(commWitnessScript),
            '1st virtual output witness hash doesn\'t correspond to commitment input witness script')
        })
      })
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

  describe('On-chain tests', () => {
    let node
    const blocks = []
    let fundingTX
    let onChainFundingTX
    const virtualTXs = []
    const onChainVirtualTXs = []
    let commTX
    let onChainCommTX

    async function setupNode() {
      node = new bcoin.FullNode({
        network: bcoin.Network.get().toString(),
        passphrase: 'secret',
        coinbaseAddress: [aliceOrigRing.getAddress()],
        //logConsole: true,
        //logLevel: 'spam',
      })
      await node.open()
      await node.connect()
      node.startSync()
    }

    async function mineCoins() {
      blocks.push(await Utils.mineBlock(node))
      await Utils.flushEvents()
      bcoin.protocol.consensus.COINBASE_MATURITY = 0
    }

    async function mineFundingTX() {
      fundingTX = Vchan.getFundingTX({
        outpoint: Outpoint.fromTX(blocks[0].txs[0], 0),
        ring: aliceOrigRing,
        fundKey1: aliceFundRing1.publicKey,
        fundKey2: bobFundRing1.publicKey,
        outAmount: aliceAmount + bobAmount,
        fee: fundingFee,
      }).toTX()

      await node.sendTX(fundingTX)
      await Utils.flushEvents()
      blocks.push(await Utils.mineBlock(node))
      onChainFundingTX = blocks[1].txs[1]
    }

    before(async () => {
      await setupNode()
      await mineCoins()
      await mineFundingTX()
    })

    it('should create a valid on-chain funding TX', async () => {
      assert(onChainFundingTX.hash().equals(fundingTX.hash()) &&
        onChainFundingTX.witnessHash().equals(fundingTX.witnessHash()),
        'The funding TX is not accepted on-chain')
    })

    async function closeNode() {
      node.stopSync()
      await node.disconnect()
      await node.close()
    }

    after(async () => {
      await closeNode()
    })
  })
})
