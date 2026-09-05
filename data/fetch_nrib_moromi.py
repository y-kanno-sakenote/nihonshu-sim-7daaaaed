#!/usr/bin/env python3
"""酒類総合研究所（NRIB）清酒製造支援データベース「清酒もろみの発酵経過及び製成酒成分」から
酒類醸造講習（清酒コース）実施仕込42件を全項目で取得し、data/nrib_moromi_42_full.json に保存する。
使い方: python3 data/fetch_nrib_moromi.py   （標準ライブラリのみ。42回のPOST、0.5秒間隔）
出典: https://nribjyo.nrib.go.jp/moromi/jitumoromis （検索条件=仕込番号、順位=1..42）
"""
import urllib.request, urllib.parse, http.cookiejar, re, html, json, time, os, datetime
URL='https://nribjyo.nrib.go.jp/moromi/jitumoromis'
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'nrib_moromi_42_full.json')
cj=http.cookiejar.CookieJar(); op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
op.addheaders=[('User-Agent','Mozilla/5.0 (sakenote nihonshu-intro data fetch)'),('Accept-Language','ja')]
def clean(s): return html.unescape(re.sub('<[^>]+>','',s)).strip()
def tables(page):
    out=[]
    for t in re.findall(r'<table.*?</table>',page,flags=re.S):
        rows=[[clean(c) for c in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>',tr,flags=re.S)] for tr in re.findall(r'<tr.*?</tr>',t,flags=re.S)]
        out.append([r for r in rows if r])
    return out
def num(s):
    s=s.replace('℃','').replace('％','').replace('%','').replace('（mg／l）','').strip()
    if s=='' : return None
    try: return float(s) if '.' in s or '-' in s else int(s)
    except ValueError: return s
def parse(tb):
    g,h,a=tb[0],tb[1],tb[2]   # 概要 / 配合 / 分析値
    kv={}
    for r in g:
        for i in range(0,len(r)-1,2): kv[r[i]]=r[i+1]
    an={}
    for r in a:
        for i in range(0,len(r)-1,2): an[r[i]]=r[i+1]
    haigo={r[0]:{'総米':num(r[1]),'蒸米':num(r[2]),'麹米':num(r[3]),'汲水':num(r[4])} for r in h[1:] if len(r)==5}
    return {
      'no':int(kv['仕込番号']),'by':kv.get('仕込年度'),'yeast':kv.get('酵母種類'),'koji_type':kv.get('麹タイプ'),'note':kv.get('備考'),
      'days':num(kv.get('仕込日数','')),'maxT':num(kv.get('最高品温','')),'maxB':num(kv.get('最高ボーメ','')),'kasu_pct':num(kv.get('糟歩合','')),
      'haigo_pct':haigo,
      'alc':num(an.get('アルコール分','')),'nihon':num(an.get('日本酒度','')),'sando':num(an.get('酸度','')),'amino':num(an.get('アミノ酸度','')),
      'glucose_pct':num(an.get('グルコース','')),
      'ethyl_caproate_mgL':num(an.get('カプロン酸エチル','')),'isoamyl_acetate_mgL':num(an.get('酢酸イソアミル','')),
      'ethyl_acetate_mgL':num(an.get('酢酸エチル','')),'isoamyl_alcohol_mgL':num(an.get('イソアミルアルコール','')),
      'raw':['\n'.join('|'.join(r) for r in t) for t in tb[:3]],
    }
def main():
    page=op.open(URL,timeout=30).read().decode('utf-8','replace')
    csrf=re.search(r'name="csrf"[^>]*value="([^"]+)"',page).group(1)
    recs=[]
    for i in range(1,43):
        d=urllib.parse.urlencode({'csrf':csrf,'kensakuki':'1','shojun':str(i)}).encode()
        r=op.open(urllib.request.Request(URL,data=d),timeout=30).read().decode('utf-8','replace')
        tb=tables(r); assert len(tb)>=3, f'{i}: tables={len(tb)}'
        rec=parse(tb); assert rec['no']==i, f'順位{i}→仕込番号{rec["no"]}'
        recs.append(rec); time.sleep(0.5)
    doc={'source':{'title':'清酒もろみの発酵経過及び製成酒成分（清酒製造支援データベース）','publisher':'独立行政法人 酒類総合研究所（NRIB）','url':URL,
          'fetched':datetime.date.today().isoformat(),'method':'本スクリプトで 検索条件=仕込番号・順位=1..42 を POST し表を機械転記','common':'総米20kg・原料米60%山田錦・普通速醸酒母・純米酒（酒類醸造講習 清酒コース）'},
         'records':recs}
    json.dump(doc,open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    print(f'{len(recs)}件 → {OUT}')
if __name__=='__main__': main()
