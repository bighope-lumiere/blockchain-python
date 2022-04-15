# coding: UTF-8

import hashlib
import json
from time import time
from urllib.parse import urlparse
from uuid import uuid4

import requests
from flask import Flask, jsonify, request


class Blockchain(object):
    def __init__(self) -> None:
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        # ジェネシスブロックの作成
        self.new_block(proof=100, previous_hash=1)

    def new_block(self, proof: int, previous_hash=None) -> dict:
        """ブロックチェーンに新しいブロックを作る

        Args:
            proof (int): プルーフ・オブ・ワークアルゴリズムから得られるプルーフ
            previous_hash (str, optional): 前のブロックのハッシュ

        Returns:
            dict: 新しいブロック
        """

        block = {
            "index": len(self.chain) + 1,
            "timestamp": time(),
            "transactions": self.current_transactions,
            "proof": proof,
            "previous_hash": previous_hash or self.hash(self.chain[-1]),
        }

        # 現在のトランザクションリストをリセット
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender: str, recipient: str, amount: int) -> int:
        """次に採掘されるブロックに加える新しいトランザクションを作る

        Args:
            sender (str): 送信者のアドレス
            recipient (str): 受信者のアドレス
            amount (int): 量

        Returns:
            int: このトランザクションを含むブロックのアドレス
        """

        self.current_transactions.append(
            {
                "sender": sender,
                "recipient": recipient,
                "amount": amount,
            }
        )

        return self.last_block["index"] + 1

    @property
    def last_block(self):
        """チェーンの最後のブロックをリターンする"""
        return self.chain[-1]

    @staticmethod
    def hash(block: dict) -> str:
        """ブロックのSHA-256ハッシュを作る

        Args:
            block (dict): ブロック

        Returns:
            str
        """

        # 一意性のあるハッシュにするためにソートする
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_proof: int) -> int:
        """シンプルなプルーフ・オブ・ワークのアルゴリズム
        - hash(pp')の最初の4つが0となるようなp'を探す
        - pは1つ前のブロックのプルーフ、p'は新しいブロックのプルーフ

        Args:
            last_proof (int): 1つ前のブロックのプルーフ

        Returns:
            int
        """

        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof: int, proof: int) -> bool:
        """プルーフが正しいか（hash(last_proof, proof)の最初の4つが0となっているか）を確認

        Args:
            last_proof (int): 前のプルーフ
            proof (int): 現在のプルーフ

        Returns:
            bool: 正しいか
        """

        guess = f"{last_proof}{proof}".encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        return guess_hash[:4] == "0000"

    def register_node(self, address: str) -> None:
        """ノードリストに新しいノードを加える

        Args:
            address (str): ノードのアドレス ex: "http://192.168.0.5:5000"

        Returns:
            None
        """

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain: list) -> bool:
        """ブロックチェーンが正しいかを確認する

        Args:
            chain (list): ブロックチェーン

        Returns:
            bool: 正しいか
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f"{last_block}")
            print(f"{block}")
            print("\n--------------\n")

            # ブロックからのハッシュが正しいかを確認
            if block["previous_hash"] != self.hash(last_block):
                return False

            # プルーフ・オブ・ワークが正しいかを確認
            if not self.valid_proof(last_block["proof"], block["proof"]):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self) -> bool:
        """コンセンサスアルゴリズム。ネットワーク上の最も長いチェーンで自らのチェーンを置換することでコンフリクトを解消する。

        Returns:
            bool: 自らのチェーンが置換されるとTrue
        """

        neighbours = self.nodes
        new_chain = None

        # 自らのチェーンより長いチェーンを探す
        max_length = len(self.chain)

        # 他のすべてのノードのチェーンを確認
        for node in neighbours:
            response = requests.get(f"http://{node}/chain")

            if response.status_code == 200:
                length = response.json()["length"]
                chain = response.json()["chain"]

                # ぞのチェーンより長いか、かつ有効かを確認
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # もし自らのチェーンより長く、かつ有効なチェーンを見つけた場合それで置換
        if new_chain:
            self.chain = new_chain
            return True

        return False


# ノードを作る
app = Flask(__name__)

# ノードのグローバルにユニークなアドレスを作る
node_identifier = str(uuid4()).replace("-", "")


blockchain = Blockchain()


@app.route("/")
def index():
    return "Hello World"


@app.route("/transactions/new", methods=["POST"])
def new_transaction():
    values = request.get_json()

    required = ["sender", "recipient", "amount"]
    if not all(k in values for k in required):
        return "Missing values", 400

    index = blockchain.new_transaction(values["sender"], values["recipient"], values["amount"])

    response = {"message": f"トランザクションはブロック {index} に追加されました"}
    return jsonify(response), 201


@app.route("/mine", methods=["GET"])
def mine():
    # 次のプルーフを見つけるためプルーフ・オブ・ワークアルゴリズムを使用する
    last_block = blockchain.last_block
    last_proof = last_block["proof"]
    proof = blockchain.proof_of_work(last_proof)

    # プルーフを見つけたことに対する報酬を得る
    # 送信者は、採掘者が新しいコインを採掘したことを表すために"0"とする
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # チェーンに新しいブロックを加えることで、新しいブロックを採掘する
    block = blockchain.new_block(proof)

    response = {
        "message": "新しいブロックを追加しました",
        "index": block["index"],
        "transactions": block["transactions"],
        "proof": block["proof"],
        "previous_hash": block["previous_hash"],
    }
    return jsonify(response), 200


@app.route("/chain", methods=["GET"])
def full_chain():
    response = {
        "chain": blockchain.chain,
        "length": len(blockchain.chain),
    }
    return jsonify(response), 200


@app.route("/nodes/register", methods=["POST"])
def register_node():
    values = request.get_json()

    nodes = values.get("nodes")
    if nodes is None:
        return "Error: 有効ではないノードのリストです", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        "message": "新しいノードが追加されました",
        "total_nodes": list(blockchain.nodes),
    }
    return jsonify(response), 201


@app.route("/nodes/resolve", methods=["GET"])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            "message": "チェーンが置き換えられました",
            "new_chain": blockchain.chain,
        }
    else:
        response = {
            "message": "チェーンが確認されました",
            "new_chain": blockchain.chain,
        }
    return jsonify(response), 200


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("-p", "--port", default=5000, type=int, help="port to listen on")
    args = parser.parse_args()
    port = args.port

    app.run(debug=True, host="0.0.0.0", port=port)
