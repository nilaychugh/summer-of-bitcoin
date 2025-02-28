const bitcoin = require("bitcoinjs-lib");
const tinysecp = require("tiny-secp256k1");
const ECPairFactory = require("ecpair").ECPairFactory;
const fs = require("fs");

bitcoin.initEccLib(tinysecp);
const ECPair = ECPairFactory(tinysecp);

// Set Bitcoin Mainnet Network
const NETWORK = bitcoin.networks.bitcoin;

// Constants
const PRIVATE_KEY_1 = "39dc0a9f0b185a2ee56349691f34716e6e0cda06a7f9707742ac113c4e2317bf";
const PRIVATE_KEY_2 = "5077ccd9c558b7d04a81920d38aa11b4a9f9de3b23fab45c3ef28039920fdd6d";
const REDEEM_SCRIPT_HEX = "5221032ff8c5df0bc00fe1ac2319c3b8070d6d1e04cfbf4fedda499ae7b775185ad53b21039bbc8d24f89e5bc44c5b0d1980d6658316a6b2440023117c3c03a4975b04dd5652ae";
const TARGET_ADDRESS = "325UUecEQuyrTd28Xs2hvAxdAjHM7XzqVF";
const SATOSHIS = 100000;

// Step 1: Create Key Pairs
const keyPair1 = ECPair.fromPrivateKey(Buffer.from(PRIVATE_KEY_1, "hex"));
const keyPair2 = ECPair.fromPrivateKey(Buffer.from(PRIVATE_KEY_2, "hex"));

// Step 2: Parse Redeem Script
const redeemScript = Buffer.from(REDEEM_SCRIPT_HEX, "hex");

// Step 3: Create P2WSH Payment
const p2wsh = bitcoin.payments.p2wsh({
    redeem: {
        output: redeemScript,
        network: NETWORK
    },
    network: NETWORK
});

// Step 4: Create P2SH-P2WSH Payment
const p2sh = bitcoin.payments.p2sh({
    redeem: p2wsh,
    network: NETWORK
});

// Verify address matches
console.log(`Expected P2SH Address: ${TARGET_ADDRESS}`);
console.log(`Calculated P2SH Address: ${p2sh.address}`);

if (p2sh.address !== TARGET_ADDRESS) {
    throw new Error("Address mismatch! Cannot create valid transaction.");
}

// Create transaction
const tx = new bitcoin.Transaction();

// Add input
tx.addInput(Buffer.alloc(32, 0), 0, 0xffffffff);

// Add output
tx.addOutput(
    bitcoin.address.toOutputScript(TARGET_ADDRESS, NETWORK),
    SATOSHIS
);

// Calculate sighash for both signatures
const sighash = tx.hashForWitnessV0(
    0, // input index
    redeemScript, // prevOutScript
    SATOSHIS, // value
    bitcoin.Transaction.SIGHASH_ALL // sighash type
);

// Sign with both keys and create DER encoded signatures with sighash
const sig1 = bitcoin.script.signature.encode(
    Buffer.from(keyPair1.sign(sighash)), // Convert Uint8Array to Buffer
    bitcoin.Transaction.SIGHASH_ALL
);

const sig2 = bitcoin.script.signature.encode(
    Buffer.from(keyPair2.sign(sighash)), // Convert Uint8Array to Buffer
    bitcoin.Transaction.SIGHASH_ALL
);

// Build the witness stack - note the order and structure
tx.setWitness(0, [
    Buffer.alloc(0), // OP_0 for CHECKMULTISIG bug
    sig2,  // DER encoded signature 1 with sighash
    sig1,  // DER encoded signature 2 with sighash
    redeemScript
]);

// Set P2SH-P2WSH scriptSig
tx.ins[0].script = bitcoin.script.compile([p2wsh.output]);

// Write to file
fs.writeFileSync("out.txt", tx.toHex());
console.log("Transaction hex written to out.txt");
