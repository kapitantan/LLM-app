---
kindle-sync:
  bookId: '2218'
  title: ネットワークはなぜつながるのか　第２版
  author: 戸根 勤
  asin: B077XSB8BS
  lastAnnotatedDate: '2025-08-19'
  bookImageUrl: 'https://m.media-amazon.com/images/I/910zNlA35GL._SY160.jpg'
  highlightsCount: 47
---
# ネットワークはなぜつながるのか　第２版
## Metadata
* Author: [戸根 勤](https://www.amazon.comundefined)
* ASIN: B077XSB8BS
* Reference: https://www.amazon.com/dp/B077XSB8BS
* [Kindle link](kindle://book?action=open&asin=B077XSB8BS)

## Highlights
画像などを張り込む場合は、文章の中に画像ファイルを表すタグ＊22 という制御情報が埋め込まれているので、ブラウザは画面に文章を表示するときに、タグを探します。そして、画像を張り込むという意味のタグに出会ったら、そこに画像用のスペースを空けて、文章を表示します。そして、もう一度、Webサーバーにアクセスして、タグに書いてある画像ファイルをWebサーバーから読み出してそのスペースに表示します。そのときも、文章ファイルを読み出すときと同じように、URIの部分に画像ファイルの名前を書いたリクエスト・メッセージを作って送ります。 — location: [614](kindle://book?action=open&asin=B077XSB8BS&location=614) ^ref-64607

---
DNSサーバーに問い合わせるということは、DNSサーバーに問い合わせメッセージを送り、そこから送り返される応答メッセージを受け取る、ということ — location: [723](kindle://book?action=open&asin=B077XSB8BS&location=723) ^ref-12434

---
このDNSクライアントに相当するものを DNSリゾルバ、あるいは、単に リゾルバ と呼びます。 — location: [725](kindle://book?action=open&asin=B077XSB8BS&location=725) ^ref-27991

---
リゾルバの実体は Socketライブラリ に入っている部品化したプログラム — location: [728](kindle://book?action=open&asin=B077XSB8BS&location=728) ^ref-48722

---
OSに組み込まれているネットワーク機能をアプリケーションから呼び出すための部品を集めたもの — location: [736](kindle://book?action=open&asin=B077XSB8BS&location=736) ^ref-27144

---
リゾルバのプログラム名（gethostbyname）とWebサーバーの名前（www.lab.glasscom.com）を書くだけです。これでリゾルバを呼び出すことができます＊ — location: [747](kindle://book?action=open&asin=B077XSB8BS&location=747) ^ref-38022

---
ドメイン名からIPアドレスを調べるとき、ブラウザはSocketライブラリのリゾルバを利用する。 — location: [756](kindle://book?action=open&asin=B077XSB8BS&location=756) ^ref-3788

---
なお、DNSサーバーへメッセージを送信するときも、DNSサーバーのIPアドレスが必要 — location: [792](kindle://book?action=open&asin=B077XSB8BS&location=792) ^ref-5848

---
それはTCP/IP設定項目のひとつとしてコンピュータに予め設定されていますから、改めて調べる必要はありません。 — location: [793](kindle://book?action=open&asin=B077XSB8BS&location=793) ^ref-46092

---
問い合わせメッセージには下記の3つの情報 — location: [802](kindle://book?action=open&asin=B077XSB8BS&location=802) ^ref-31563

---
（a）名前 　　サーバーやメール配送先（メール・アドレスの@以後の名前）などの名前のことです。 （b）クラス 　　DNSの仕組みが考案されたときは、インターネット以外のネットワークでの利用も検討され、それを識別するためにクラスという情報が用意されています。しかし、今はインターネット以外のネットワークは消滅したので、クラスは常にインターネットを表す「IN」という値になります。 （c）タイプ 　　名前にどのようなタイプ（種類）の情報が対応づけられているのか表します。たとえば、タイプが「A」であれば、名前にIPアドレスが対応づけられていることを表し、「MX」だったら名前にメール配送先が対応づけられていることを表します。なお、このタイプによってクライアントに回答する情報の内容は異なります。 — location: [803](kindle://book?action=open&asin=B077XSB8BS&location=803) ^ref-22788

---
DNSで扱う名前は、www.lab.glasscom.comというようにドットで区切られていますが、このドットが階層の区切りを表します。 — location: [860](kindle://book?action=open&asin=B077XSB8BS&location=860) ^ref-46640

---
右に位置するものが上位の階層を表す — location: [863](kindle://book?action=open&asin=B077XSB8BS&location=863) ^ref-57477

---
1つの部署に相当するものを ドメイン と呼びます。 — location: [865](kindle://book?action=open&asin=B077XSB8BS&location=865) ^ref-47854

---
1つのドメインの情報を分割して複数の — location: [869](kindle://book?action=open&asin=B077XSB8BS&location=869) ^ref-38427

---
DNSサーバーに登録することはできない — location: [870](kindle://book?action=open&asin=B077XSB8BS&location=870) ^ref-13601

---
ただ、DNSサーバーとドメインは常に1対1ということではなく、1台のDNSサーバーに複数のドメインの情報を登録することはできます。 — location: [870](kindle://book?action=open&asin=B077XSB8BS&location=870) ^ref-60214

---
最上位のjpというドメインは日本に割り当てられたドメイン — location: [887](kindle://book?action=open&asin=B077XSB8BS&location=887) ^ref-6184

---
coというドメインは、日本国内のドメインを分類するために設けられたドメイン — location: [888](kindle://book?action=open&asin=B077XSB8BS&location=888) ^ref-26576

---
で、会社を表します。 — location: [888](kindle://book?action=open&asin=B077XSB8BS&location=888) ^ref-64941

---
wwwがサーバーの名前 — location: [889](kindle://book?action=open&asin=B077XSB8BS&location=889) ^ref-38089

---
ルート・ドメインのDNSサーバーに割り当てられたIPアドレスは全世界で13個＊47 しかありませんし、滅多に変更されませんから、それを各DNSサーバーに登録する作業はさほど難しくありません。 — location: [912](kindle://book?action=open&asin=B077XSB8BS&location=912) ^ref-18420

---
DNSサーバーはキャッシュ機能で素早く回答 — location: [942](kindle://book?action=open&asin=B077XSB8BS&location=942) ^ref-31480

---
名前が存在しないという回答が返ってきますが、それをキャッシュに保存することもあります。 — location: [953](kindle://book?action=open&asin=B077XSB8BS&location=953) ^ref-4105

---
キャッシュ中に保存した情報は正しいとは限らない、 — location: [955](kindle://book?action=open&asin=B077XSB8BS&location=955) ^ref-16741

---
そのため、DNSサーバーに登録する情報には有効期限を設定します。 — location: [956](kindle://book?action=open&asin=B077XSB8BS&location=956) ^ref-41504

---
IPアドレスの相手、ここではアクセス先のWebサーバーにメッセージを送信するようOSの内部にある プロトコル・スタック に依頼します。 — location: [963](kindle://book?action=open&asin=B077XSB8BS&location=963) ^ref-1563

---
最初はソケットを作るフェーズです。クライアント側のソケットを作るのは簡単です。Socketライブラリのsocketというプログラム部品＊53 を呼び出すだけ — location: [1024](kindle://book?action=open&asin=B077XSB8BS&location=1024) ^ref-15503

---
アプリケーションはSocketライブラリのconnectというプログラム部品を呼び出すことでこの依頼動作を実行します。 — location: [1049](kindle://book?action=open&asin=B077XSB8BS&location=1049) ^ref-32607

---
connectを呼び出すときに指定するディスクリプタ、サーバーのIPアドレス、ポート番号という3つの値 — location: [1050](kindle://book?action=open&asin=B077XSB8BS&location=1050) ^ref-12256

---
は、IPアドレスで特定できるのは、ネットワーク上のどのコンピュータなのかというところまでです。接続動作は相手側のソケットに対して行うものなので、ソケットを特定しなければいけないのですが、IPアドレスではソケットまでは特定できません。 — location: [1063](kindle://book?action=open&asin=B077XSB8BS&location=1063) ^ref-29299

---
クライアント側のソケットのポート番号は、ソケットを作るときにプロトコル・スタックが適当な値を見繕って割り当ててくれます＊61。そして、その値はプロトコル・スタックが接続動作を実行するときにサーバー側に通知されます。 — location: [1090](kindle://book?action=open&asin=B077XSB8BS&location=1090) ^ref-46578

---
アプリケーションは直接ソケットにタッチできないので、Socketライブラリを介してプロトコル・スタックにその旨依頼します。 — location: [1101](kindle://book?action=open&asin=B077XSB8BS&location=1101) ^ref-50843

---
イーサネットのヘッダー（パケットの先頭にある制御情報）のフォーマットは国際標準（IEEE802.3/802.2）ではなく、それが作られる前の古い仕様（イーサネット第2版。通称DIX仕様）に従うのが通例です。なお、国際標準（IEEE802.3/802.2）はヘッダー長が長くなり効率が低下するため普及していません。 — location: [1374](kindle://book?action=open&asin=B077XSB8BS&location=1374) ^ref-21171

---
今のTCPとIPを1つにまとめた格好になっていました。それが、後にTCPとIPの2つに分けられました。 — location: [1378](kindle://book?action=open&asin=B077XSB8BS&location=1378) ^ref-23308

---
ブラウザやメールなどの通常のアプリケーションはTCPを使ってデータを送受信し、DNSサーバーへの問い合わせなどで短い制御用のデータを送受信する場合はUDPを使う、 — location: [1441](kindle://book?action=open&asin=B077XSB8BS&location=1441) ^ref-64161

---
ICMPは、パケットを運ぶときに発生するエラーを通知したり、制御用のメッセージを通知するときに使う — location: [1451](kindle://book?action=open&asin=B077XSB8BS&location=1451) ^ref-47035

---
ARPはIPアドレスに対応するイーサネットの MACアドレス＊4 を調べるときに使います。 — location: [1452](kindle://book?action=open&asin=B077XSB8BS&location=1452) ^ref-53242

---
プロトコル・スタックは内部に制御情報を記録するメモリー領域を持ち、そこに、通信動作を制御するための制御情報を記録します。 — location: [1458](kindle://book?action=open&asin=B077XSB8BS&location=1458) ^ref-17864

---
接続するってどういうこと？ — location: [1522](kindle://book?action=open&asin=B077XSB8BS&location=1522) ^ref-27774

---
サーバーのIPアドレスやポート番号をプロトコル・スタックに知らせる動作が必要です。それが接続動作のひとつの役割です。 — location: [1535](kindle://book?action=open&asin=B077XSB8BS&location=1535) ^ref-24124

---
クライアント側からサーバー側に通信動作の開始を伝えることも接続動作の役割のひとつです。 — location: [1543](kindle://book?action=open&asin=B077XSB8BS&location=1543) ^ref-40709

---
接続動作の動きは、通信相手との間で制御情報をやり取りして、ソケットに必要な情報を記録し、データ送受信可能な状態にすること — location: [1544](kindle://book?action=open&asin=B077XSB8BS&location=1544) ^ref-12940

---
メモリー領域をバッファ・メモリーと呼び、その確保も接続動作のときに実行します。 — location: [1552](kindle://book?action=open&asin=B077XSB8BS&location=1552) ^ref-11706

---
ひとつは、クライアントとサーバーが互いに連絡を取り合うためにやり取りする制御情報です。 — location: [1557](kindle://book?action=open&asin=B077XSB8BS&location=1557) ^ref-10359

---
制御情報はもうひとつあります。それは、ソケットに記録して、プロトコル・スタックの動作をコントロールするための情報です＊ — location: [1580](kindle://book?action=open&asin=B077XSB8BS&location=1580) ^ref-40873

---
電気信号は周波数が高いほどエネルギーの落ちる率が大きい — location: [2955](kindle://book?action=open&asin=B077XSB8BS&location=2955) ^ref-32337



