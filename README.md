# blockchain-python

[ブロックチェーンを作ることで学ぶ 〜ブロックチェーンがどのように動いているのか学ぶ最速の方法は作ってみることだ〜 - Qiita](https://qiita.com/hidehiro98/items/841ece65d896aeaa8a2a#%E3%82%B9%E3%83%86%E3%83%83%E3%83%971-%E3%83%96%E3%83%AD%E3%83%83%E3%82%AF%E3%83%81%E3%82%A7%E3%83%BC%E3%83%B3%E3%82%92%E4%BD%9C%E3%82%8B) を参考にPythonでブロックチェーンを作成したもの

todo: Docker 環境で動作しないので動かせるようにしたい。ローカルのPython環境では動作確認できた。

コンテナの起動

```sh
docker-compose up -d
```

コンテナの状態を確認

```sh
docker-compose ps
```

blockchain.py を実行

```sh
docker exec -it blockchain-python python blockchain.py -p 5000
```

コンテナの終了

```sh
docker-compose down
```
