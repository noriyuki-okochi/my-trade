〇ファイル構成（WSL環境）
	(/mnt/d/share/Auto-trade/mytrade)
	./src/main.py
		  /myApi.py
		  /env.py
	      /coincheck/
	      /gmocoin/
	      /mysqlite3/
	./standalone-chrome/Dockerfile
	./api-key.txt
	./Auto-trade.db
	./setenv
	./auto-start.sh
	./Dockerfile
	./docker-compose.yml
	./requirements.txt
	./.env
	./readme.txt
	./Pipfile
	./Pipfile.lock

〇Dockerイメージ作成方法
	docker-compose build
    (slenium-chromeコンテナのDockerfileパス)
        ./standalone-chrome
		
	image:standalone-chrome(selenium/standalone-chrome)
	       					- VNCサーバーを含む
	      python3-mytrade(python:3.9.5)

〇起動方法
	docker-compose up -d
		プロジェクト名：mytrade
		container:selenium-chrome
	    	      mytrade

   (VNC接続）
   　　Win10 Ultra VNC-viewer　クライアントを起動
		localhost:15900
		パスワード：vncpasss
   (X11接続）
   　　Win10 VcXsrv サーバーを起動
        DISPLAY=172.24.0.1:0.0
		        Win10 WSL仮想アダプターのIPアドレス

   (現在レートのサンプリング)
	docker exec -it mytrade bash ./auto-start.sh
   (チャートの表示)
	docker exec -it mytrade bash ./chart-start.sh
   
   (過去サンプリングログの削除)
	docker exec -it -w /root/mytrade/src mytrade python main.py -d1y

〇コンテナの停止・削除、ネットワーク削除
	docker-compose down
	docker-compose down --rmi all　（上記＋イメージ削除）


