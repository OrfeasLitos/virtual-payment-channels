# Attack description

## Setting

Before opening the virtual channel, A has a channel with B where the funding output has keys A_f, B_f with total value c_AB. Similarly for B and C, C and D, D and E.

A and E open a virtual channel of total value c with the help of B,C,D.

For every transaction mentioned, the party also holds all signatures from other parties that are needed to publish it.

B and D respectively hold, among other txs, tx_B and tx_D. The idea for B is that he can consume both funding outputs of his adjacent channels (AB and BC) and produce one output for the virtual channel and outputs for the adjacent channels. The same goes for D.
More specifically, tx_B:
* 2 inputs:
  * 2-of-{A_f, B_f},
  * 2-of-{B_f, C_f},
* 2 of the outputs:
  * (c, 5-of-{A,B,C,D,E} OR (2-of-{A,E} w/ timelock t)), - virtual channel
  * (c_BC-c, 4-of-{A,E,B,C} OR (2-of-{B,C} w/ timelock t)). - BC channel
(tx_B has more outputs, but we only care about these two now.)

And tx_D:
* 2 inputs:
  * 2-of-{C_f, D_f},
  * 2-of-{D_f, E_f},
* 2 of the outputs:
  * (c, 5-of-{A,B,C,D,E} OR (2-of-{A,E} w/ timelock t)), - virtual channel
  * (c_CD-c, 4-of-{A,E,C,D} OR (2-of-{C,D} w/ timelock t)). - CD channel

The virtual channel is funded by A, therefore every intermediate party should fund the virtual channel downstream and regain the same coins from upstream, in order to safeguard E from e.g. A and B that are malicious and refuse to consume their 2-of-{A_f, B_f} output. This means in particular that the “CD channel” output of tx_D, if the timelock expires, goes to a CD channel where C has c coins less than his original balance. Furthermore, the “BC channel” output does not refund C’s c coins. So, in case both tx_B and tx_D end up on-chain, C has lost c coins and there are two virtual channel outputs instead of the unique there should be. The “solution” is to give to C a tx_probl as follows:
tx_probl:
* 3 inputs:
  * 5-of-{A,B,C,D,E}, - consume one “virtual channel” output
  * 4-of-{A,E,B,C}, - “proof” that tx_B was on-chain
  * 4-of-{A,E,C,D}, - “proof” that tx_D was on-chain
* 3 outputs:
  * (c, C), - reimbursement of c for C
  * (c_BC-c, 2-of-{B,C}), - BC channel
  * (c_CD-c, 2-of-{C,D}), - CD channel (C gets c less from 3. but gets c more from 1.)
The idea is that tx_probl can only be used when both B and D have closed independently and so produced two virtual channel outputs at the expense of C, so that C can be reimbursed.

## Attack

As the name suggests, tx_probl is problematic. Indeed, if only A is honest and tries to close its channel, it will produce a single (c, 5-of-{A,B,C,D,E} OR (2-of-{A,E} w/ timelock t)) output. In this attack, the rest of the players do not consume their 2-of-{B_f, C_f}, 2-of-{C_f, D_f}, 2-of-{D_f, E_f} outputs. If the protocol was secure, the timelock should expire as this is the only “virtual channel” output on-chain. However now C, using his own independent coins, can publish a transaction with two outputs: 4-of-{A,E,B,C}, 4-of-{A,E,C,D} and then publish tx_probl which consumes A’s “virtual channel” output, effectively stealing the entire virtual channel balance.

## Lessons learned

* In my analysis, I missed the fact that the 4-of-{A,E,B,C} and 4-of-{A,E,C,D} outputs can be created by spending completely unrelated coins. Since C already has a signature for tx_prob that uses the ANYPREVOUT flag, it is impossible to ensure that these outputs come from tx_B and tx_D. However we have to use ANYPREVOUT so that the hash of the previous transaction is not signed, as tx_B and tx_D may in turn spend outputs that come from various different transactions (e.g. the previous layer might use tx_B’ or tx_probl’ to generate the 2-of-{B_b, C_b} output).
* After trying various possible fixes, it is my understanding that intermediaries cannot prove the existence of two competing “virtual channel” outputs using vanilla bitcoin script. It may be easier to only allow A and E to produce the “virtual channel” outputs and, in case both appear on-chain, allow A (using some cryptographic trick) to keep the coins of exactly one of the outputs to herself to ensure balance security. If this doesn’t work, we can look for more complicated solutions that involve the intermediaries.
