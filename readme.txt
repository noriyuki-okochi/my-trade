〇ファイル構成

	./src/main.py
		  /myApi.py
		  /env.py
	      /coincheck/
	      /gmocoin/
	      /mysqlite3/
	./api-key.txt
	./Auto-trade.db
	./setenv
	./auto-start.sh
	./Dockerfile
	./docker-compose.yml
	./requirements.txt
	./.env
	./readme.txt

〇Dockerイメージ作成方法
	docker-compose build

〇起動方法
	docker-compose up -data
   
   (現在レートのサンプリング)
	docker exec -it mytrade bash ./auto-start.sh
   
   (過去サンプリングログの削除)
	docker exec -it -w /root/mytrade/src mytrade python main.py -d1y

〇コンテナの停止・削除、ネットワーク削除
	docker-compose down
	docker-compose down --rmi all　（上記＋イメージ削除）


