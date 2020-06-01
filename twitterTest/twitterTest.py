#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import config
import os
import sys
import datetime as dt
import pandas as pd
from requests_oauthlib import OAuth1Session

# OAuth認証部分
CK = config.CONSUMER_KEY
CS = config.CONSUMER_SECRET
AT = config.ACCESS_TOKEN
ATS = config.ACCESS_TOKEN_SECRET
twitter = OAuth1Session(CK, CS, AT, ATS)

tz_JST = dt.timezone(dt.timedelta(hours=+9), 'JST')

# Twitter Endpoint(検索結果を取得する)
url_get = 'https://api.twitter.com/1.1/search/tweets.json'
url_post = 'https://api.twitter.com/1.1/statuses/update.json'

# アイドルプロフリスト読み込み
# 絶対パスでカレントディレクトリ移動(暫定措置)
os.chdir("C:/Users/hagirainbow/source/repos/twitterTest/twitterTest/dere_profil")
dere_profil = pd.read_csv('dere_profil.csv').fillna('')
result = pd.DataFrame(columns=['idol_name','tweets','time','tweet/hour'])

# df全件ループ(但しnanは空文字変換)
for j,profil in enumerate(dere_profil[dere_profil['CV'] == ''].iterrows()) :
# for j,profil in enumerate(dere_profil[dere_profil['CV'] != ''].iterrows()) :
#for j,profil in enumerate(dere_profil.iterrows()) :
    # Enedpointへ渡すパラメーター
    name = profil[1].l_name + profil[1].f_name
    # keyword = name + ' OR #' + name + ' -filter:retweets'
    keyword = name + 'に投票したよ #ボイスアイドルオーディション  -filter:retweets'
    # since - until 出期間指定。過去一週間のみ？
    # https://ja.stackoverflow.com/questions/33254/twitter-api%E3%81%A7%E5%8F%96%E5%BE%97%E3%81%A7%E3%81%8D%E3%82%8B%E3%83%84%E3%82%A4%E3%83%BC%E3%83%88%E3%81%AF%E4%BD%95%E6%97%A5%E5%89%8D%E3%81%BE%E3%81%A7%E3%81%A7%E3%81%99%E3%81%8B
    params = {
        'count' : 100,      # 取得するtweet数(上限100)
        'q'     : keyword  # 検索キーワード
        }

    # 検索ワードを表示
    print('単語名：' + keyword)
    # 検索実行
    req = twitter.get(url_get, params = params)

    # 検索成功か判定
    if req.status_code == 200:
        #現在時刻
        ptdatetime = dt.datetime.now(tz_JST)
        #遡り最後のツイート時刻(初期値は現在時刻)
        tdatetime = ptdatetime
        # ② 取得した検索結果ツイート件数
        num = 0
        #検索結果ツイート全件ループ
        res = json.loads(req.text)
        for i,line in enumerate(res['statuses']):
            # ツイートの時刻を取得 文字列->日付時刻変換+timezone設定
            tdatetime = dt.datetime.strptime(line['created_at'],'%a %b %d %H:%M:%S %z %Y').astimezone(tz_JST)
            # ツイート件数カウンタ++
            num = num + 1
            # print(str(i) + '件目******' + str(tdatetime))
            # print(line['text'] + '\n')
        # ① 現在時刻～一番遡ったツイートの時刻の時間差(h)
        ttime = (ptdatetime - tdatetime).total_seconds() / 3600
        print('遡り時間(h)：' + str(ttime) + '件数(件)：' + str(num))

        # 集計、DF登録(集計結果0件の場合は0除算防止のため計算しない)
        if 0 < num :
            # ツイート時速 = ② 取得ツイート数 / ① 時間差
            tweetperhour = num / ttime
            # ツイート時速を出力
            print('時速(tweet/h)：' + str(tweetperhour))
            # 取得ツイート数、時間差、ツイート時速をDF登録
            result_1 = pd.Series([name,num,ttime,tweetperhour],index = result.columns,name = j)
            result = result.append(result_1)
    else:
        print("Failed: %d" % req.status_code)
#結果を時速早い順、100件までの時間短い順にソートし表示
result = result.sort_values(['tweet/hour','time'], ascending = [False,True])
print(result)
#CSV書き出し
result.to_csv('result' + dt.datetime.now(tz_JST).strftime('%Y%m%d-%H%M%S') + '.csv', encoding='utf_8_sig')

# テスト用DF読み込み
#result = pd.read_csv('result20200321-002737.csv')

# Twitter投稿
# 日付時刻文字列化
tweetMSG = dt.datetime.now(tz_JST).strftime('%Y/%m/%d %H:%M:%S') + '現在の投票ﾂｲｰﾄ時速(T/h)\n( #ボイスアイドルオーディション )\n'
tweetLen = len(tweetMSG.encode())

for data in result.iterrows():
    addMsg = data[1]['idol_name']  + ':' + '{:.3f}'.format(data[1]['tweet/hour']) + '\n'
    if 280 < tweetLen + len(addMsg.encode()):
        break
    tweetMSG = tweetMSG + addMsg
    tweetLen = len(tweetMSG.encode())
req = twitter.post(url_post, params = {"status": tweetMSG + ''})
if req.status_code == 200:
    #正常に処理できたら
    print("Success!")
else:
    print("ERROR : %d" % req.status_code)