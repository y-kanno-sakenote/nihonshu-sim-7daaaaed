#!/usr/bin/env python3
"""記録簿（log.html）の「実測の目安」を NRIB 実もろみDB の実測値から作り、log.html に埋め込む。
使い方: python3 data/build_log_reference.py   （標準ライブラリのみ。log.html の NRIB_REF ブロックを書き換える）

出典: NRIB 実もろみDB（酒類総合研究所「清酒もろみの発酵経過及び製成酒成分」・酒類醸造講習 清酒コース
      実施仕込42件、2026-09-05取得）= data/nrib_moromi_42_full.json（台帳 dev/sake-kb/sources.csv の nrib-jitsu-moromi）

作り方（推測で値を作らない）:
- 対象: 42件から明らかな異常仕込み4件（no.5・6=最高品温24.1℃/13日、no.9=発酵停滞、no.37=低アル）を除いた38件。
  除外は MOROMI_MODEL_SPEC.md §8.10 の「正常クラスタ38仕込」と同じ。
- DBが数値で公開しているのは1仕込ごとの要約値だけ（日ごとの経過はグラフ画像のみ）。したがって日ごとの線は作らず、
  次の3つの節目を出す。節目どうしを線で結ばない（補間・外挿しない）。
    1. 最高ボーメ maxB …… 日付は非公開。赤本（清酒製造技術）p.265「留後3〜4日目の水泡時期まではボーメは高まる…
       最高のボーメ」に従い、留後3〜4日目の位置に置く。
    2. 最高品温 maxT …… 日付は非公開。赤本 p.263「醪日数の3分の1の時期で最高温度をとり、3分の2までその温度を持続」
       に従い、38件の醪日数の中央値Dの D/3〜2D/3 の位置に置く。
    3. 上槽時のボーメ …… 製成酒の日本酒度 nihon を ボーメ = −日本酒度/10 で換算（赤本 p.270「15日目の日本酒度が
       −20と−5の醪ではBMD値は30と7.5」＝日本酒度−20↔ボーメ2）。x は各仕込の醪日数 days。各仕込を点で出す。
- 代表値: 中央値。幅: 四分位（25/75%、線形補間＝numpy既定・R type7）と最小〜最大。
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'nrib_moromi_42_full.json')
LOG = os.path.join(HERE, '..', 'log.html')
EXCLUDE = [5, 6, 9, 37]


def quantile(sorted_v, p):
    """線形補間の分位点（R type7）。"""
    h = (len(sorted_v) - 1) * p
    lo = int(h)
    hi = min(lo + 1, len(sorted_v) - 1)
    return sorted_v[lo] + (h - lo) * (sorted_v[hi] - sorted_v[lo])


def summary(values):
    v = sorted(values)
    r3 = lambda x: round(x, 3) + 0.0  # +0.0 で −0.0 を 0.0 にそろえる
    return {'min': r3(v[0]), 'q1': r3(quantile(v, .25)), 'med': r3(quantile(v, .5)),
            'q3': r3(quantile(v, .75)), 'max': r3(v[-1])}


def build():
    doc = json.load(open(SRC, encoding='utf-8'))
    recs = [r for r in doc['records'] if r['no'] not in EXCLUDE]
    for r in recs:
        assert all(r[k] is not None for k in ('days', 'maxT', 'maxB', 'nihon')), r['no']
    end_b = [-r['nihon'] / 10 for r in recs]
    return {
        'source': 'NRIB 実もろみDB（酒類総合研究所 酒類醸造講習 実施仕込、2026-09-05取得）',
        'n': len(recs), 'excluded': EXCLUDE,
        'days': summary([r['days'] for r in recs]),
        'maxT': summary([r['maxT'] for r in recs]),
        'maxB': summary([r['maxB'] for r in recs]),
        'endB': summary(end_b),
        'pts': [[r['no'], r['days'], round(b, 3) + 0.0] for r, b in zip(recs, end_b)],  # [仕込番号, 醪日数, 上槽時ボーメ]
    }


def main():
    ref = build()
    block = ('// ==NRIB_REF_BEGIN== data/build_log_reference.py が生成（手で直さない）\n'
             'const NRIB_REF = ' + json.dumps(ref, ensure_ascii=False, separators=(',', ':')) + ';\n'
             '// ==NRIB_REF_END==')
    html = open(LOG, encoding='utf-8').read()
    new, k = re.subn(r'// ==NRIB_REF_BEGIN==.*?// ==NRIB_REF_END==', lambda m: block, html, flags=re.S)
    assert k == 1, 'log.html に NRIB_REF ブロックが見つからない'
    open(LOG, 'w', encoding='utf-8').write(new)
    print(f"n={ref['n']} maxB中央{ref['maxB']['med']} maxT中央{ref['maxT']['med']} 上槽ボーメ中央{ref['endB']['med']} → log.html")


if __name__ == '__main__':
    main()
