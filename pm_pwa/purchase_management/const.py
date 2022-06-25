from enum import Enum


# 比較対象の店舗
class CompareStore(Enum):
    RAKUTEN = "rakuten"
    OK = "ok"
    CREATE = "create"
    AMAZON = "amazon"
    FRESH = "fresh"
    YODOBASHI = "yodobashi"
    DONKI = "donki"
    LIFE = "life"
    SEIJO = "seijo"
    SUGI = "sugi"
    NISHIMATSUYA = "nishimatsuya"


# 表示名
COMPARE_DISP_NAME = {
    CompareStore.RAKUTEN: "楽天24",
    CompareStore.OK: "オーケー",
    CompareStore.CREATE: "クリエイト",
    CompareStore.AMAZON: "Amazon",
    CompareStore.FRESH: "Amazon Fresh",
    CompareStore.YODOBASHI: "ヨドバシ",
    CompareStore.DONKI: "ドン・キホーテ",
    CompareStore.LIFE: "ライフ",
    CompareStore.SEIJO: "セイジョー",
    CompareStore.SUGI: "スギ薬局",
    CompareStore.NISHIMATSUYA: "西松屋",
}

# 割引率
COMPARE_DISCOUNT_RATE = {
    CompareStore.RAKUTEN: 0.15,
}

# ポイント還元率
COMPARE_POINT_RATE = {
    CompareStore.RAKUTEN: 0.065,
    CompareStore.YODOBASHI: 0.1,
}
