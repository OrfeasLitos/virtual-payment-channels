'use strict'

const bcoin = require('bcoin').set('regtest')
const bcrypto = require('bcoin/node_modules/bcrypto')
const sha256 = bcrypto.SHA256
const assert = require('bcoin/node_modules/bsert')

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

const rings = Array.apply(null, Array(12))
      .map(x => KeyRing.generate())
rings.map(ring => {ring.witness = true})

const delay = 42

const fundingHash = sha256.digest(Buffer.from('funding'))

const aliceAmount = Amount.fromBTC(10).toValue()
const bobAmount = Amount.fromBTC(40).toValue()
const daveAmount = Amount.fromBTC(10).toValue()
const baseAmount = aliceAmount + bobAmount
const virt1Amount = Amount.fromBTC(15).toValue()
const virt2Amount = Amount.fromBTC(5).toValue()

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
const daveRevRing = rings[10]
const daveOwnRing = rings[11]

describe('Unit tests', () => {
  const fundingTX = Vchan.getFundingTX({
    outpoint: new Outpoint(fundingHash, 0),
    ring: aliceOrigRing,
    fundKey1: aliceFundRing1.publicKey,
    fundKey2: bobFundRing1.publicKey,
    outAmount: aliceAmount + bobAmount,
    fee: fundingFee,
  })

  describe('Funding TX', () => {
    it('should verify correctly', () => {
      assert(fundingTX.verify(),
        'Funding TX does not verify correctly')
    })

    let fundingTX2 = new MTX({version: 2})

    fundingTX2.addCoin(Coin.fromJSON({
      version: 2,
      height: -1,
      value: aliceAmount + bobAmount,
      coinbase: false,
      script: aliceOrigRing.getProgram().toRaw().toString('hex'),
      hash: fundingHash.reverse().toString('hex'),
      index: 0,
    }))

    fundingTX2 = Vchan.getFundingTX({
      fctx: fundingTX2, fundKey1: aliceFundRing1.publicKey,
      fundKey2: bobFundRing1.publicKey,
      outAmount: aliceAmount + bobAmount,
      fee: fundingFee,
    })

    fundingTX2.sign(aliceOrigRing)

    it('should be generatable both from MTX and from KeyRing', () => {
      assert(fundingTX.hash().equals(fundingTX2.hash()) &&
        fundingTX.witnessHash().equals(fundingTX2.witnessHash()),
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
    amounts: {aliceAmount, bobAmount, fee: fundingFee},
    fundingTX,
    fundingIndex: 0,
  })

  describe('Commitment TX', () => {
    it('should verify correctly', () => {
      assert(commTX.verify(),
        'Commitment TX does not verify correctly')
    })

    const fundingWitnessHash = fundingTX.outputs[0].script.code[1].data
    const commWitnessScript = commTX.inputs[0].witness.getRedeem().sha256()
    it('should spend funding TX', () => {
      assert(fundingWitnessHash.equals(commWitnessScript),
        'Funding output witness hash doesn\'t correspond to commitment input witness script')
    })
  })

  const virtualTX = Vchan.getVirtualTX({
    inRings: [aliceFundRing2, bobFundRing2],
    outRings: [
      [aliceVirtRing1, bobVirtRing],
      [aliceVirtRing2, daveVirtRing]
    ],
    amounts: [baseAmount - virt1Amount, virt1Amount],
    fee: fundingFee,
    fundingTX
  })

  describe('Virtual TX', () => {
    it('should verify correctly', () => {
      assert(virtualTX.verify(),
        'Virtual TX does not verify correctly')
    })

    const fundingWitnessHash = fundingTX.outputs[0].script.code[1].data
    const virtWitnessScript = virtualTX.inputs[0].witness.getRedeem().sha256()
    it('should spend funding TX', () => {
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
      const virtualTX2 = Vchan.getVirtualTX({
        inRings: [aliceFundRing2, bobFundRing2],
        outRings: [
          [aliceVirtRing1, bobVirtRing],
          [aliceVirtRing2, daveVirtRing],
          [aliceVirtRing3, charlieVirtRing]
        ],
        amounts: [
          baseAmount - virt1Amount - virt2Amount,
          virt2Amount, virt1Amount
        ],
        fee: fundingFee,
        fundingTX
      })

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
})

describe('On-chain tests', () => {
  let node
  const blocks = []
  let fundingTX
  let onChainFundingTX
  let firstVirtualTX
  let secondVirtualTX
  let onChainFirstVirtualTX
  let onChainSecondVirtualTX
  let aliceCommTX
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

  async function mineTX(tx) {
    await node.sendTX(tx)
    await Utils.flushEvents()
    blocks.push(await Utils.mineBlock(node))
    return blocks[blocks.length - 1].txs[1]
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

    onChainFundingTX = await mineTX(fundingTX)
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

  describe('Before new channel opening', () => {
    async function mineFirstVirtualTX() {
      firstVirtualTX = Vchan.getVirtualTX({
        inRings: [aliceFundRing1, bobFundRing1],
        outRings: [
          [aliceVirtRing1, bobVirtRing],
          [aliceVirtRing2, daveVirtRing],
        ],
        amounts: [baseAmount - virt1Amount, virt1Amount],
        fee: virtualFee,
        fundingTX
      }).toTX()

      onChainFirstVirtualTX = await mineTX(firstVirtualTX)
    }

    async function mineCommitmentTX() {
      aliceCommTX = Vchan.getCommitmentTX({
        rings: {
          aliceFundRing: aliceVirtRing2,
          bobFundRing: daveVirtRing,
          aliceRevRing,
          aliceDelRing,
          bobRevRing: daveRevRing,
          bobOwnRing: daveOwnRing,
        },
        delay,
        amounts: {
          aliceAmount: virt1Amount - daveAmount,
          bobAmount: daveAmount,
          fee: commitmentFee,
        },
        fundingTX: firstVirtualTX,
        fundingIndex: 1,
      }).toTX()

      onChainCommTX = await mineTX(aliceCommTX)
    }

    before(async () => {
      await mineFirstVirtualTX()
      await mineCommitmentTX()
    })

    it('should spend the funding TX with first virtual TX', async () => {
      assert(onChainFirstVirtualTX.hash().equals(firstVirtualTX.hash()) &&
        onChainFirstVirtualTX.witnessHash().equals(firstVirtualTX.witnessHash()),
        'The virtual TX is not accepted on-chain')
    })

    it('should spend the first virtual TX with the commitment TX', async () => {
      assert(onChainCommTX.hash().equals(aliceCommTX.hash()) &&
        onChainCommTX.witnessHash().equals(aliceCommTX.witnessHash()),
        'The virtual TX is not accepted on-chain')
    })

    async function forgetBlocks(n) {
      for (let i = 0; i < n; i++) {
        const oldTip = node.chain.tip
        await node.chain.disconnect(node.chain.tip)
        await node.chain.emitAsync('reorganize', oldTip, node.chain.tip)
      }
    }

    after(async () => {
      await forgetBlocks(2) // forget commitment TX and 1st virtual TX
    })
  })

  describe('After new channel opening', () => {
    async function mineSecondVirtualTX() {
      secondVirtualTX = Vchan.getVirtualTX({
        inRings: [aliceFundRing1, bobFundRing1],
        outRings: [
          [aliceVirtRing1, bobVirtRing],
          [aliceVirtRing2, daveVirtRing],
          [aliceVirtRing3, charlieVirtRing]
        ],
        amounts: [
          baseAmount - virt1Amount - virt2Amount,
          virt1Amount, virt2Amount
        ],
        fee: virtualFee,
        fundingTX
      }).toTX()

      onChainSecondVirtualTX = await mineTX(secondVirtualTX)
    }

    function modifyCommitmentTX() {
      aliceCommTX.inputs[0].prevout = Outpoint.fromTX(secondVirtualTX, 1)
    }

    before(async () => {
      await mineSecondVirtualTX()
      modifyCommitmentTX()
      onChainCommTX = await mineTX(aliceCommTX) // this can't work :(
    })

    it('should spend the funding TX with second virtual TX', async () => {
      assert(onChainSecondVirtualTX.hash().equals(secondVirtualTX.hash()) &&
        onChainSecondVirtualTX.witnessHash().equals(secondVirtualTX.witnessHash()),
        'The virtual TX is not accepted on-chain')
    })

    it.skip('should spend the second virtual TX with the modified commitment TX', async () => {
      assert(onChainCommTX.hash().equals(aliceCommTX.hash()) &&
        onChainCommTX.witnessHash().equals(aliceCommTX.witnessHash()),
        'The virtual TX is not accepted on-chain')
    })
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
