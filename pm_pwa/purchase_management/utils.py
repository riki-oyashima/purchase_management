import math
from google.cloud import datastore

from pm_pwa.purchase_management.const import *


def update_min_store():
    """
    最安の店舗を再計算
    :return:
    """
    client = datastore.Client()
    query = client.query(kind='goods')
    query_iter = query.fetch()
    for entity in query_iter:
        min_store = None
        min_value = 0
        for store in CompareStore:
            key = f"value_{store.value}"
            if key in entity and entity[key]:
                compare_value = math.ceil(entity[key] *
                                          (1 - COMPARE_DISCOUNT_RATE.get(store, 0)) *
                                          (1 - COMPARE_POINT_RATE.get(store, 0)))
                if min_store is None or compare_value < min_value:
                    min_store = store.value
                    min_value = compare_value
        # 最安の店舗名を登録
        if "min_store" not in entity or entity["min_store"] != min_store:
            print(f"{entity['name']} update min_store {entity['min_store']} -> {min_store}")
            entity["min_store"] = min_store
            client.put(entity)
