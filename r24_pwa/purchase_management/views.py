import json
import math
import os
from datetime import datetime

from django.shortcuts import redirect
from django.views.generic import TemplateView
from google.cloud import datastore
from pprint import pprint

from r24_pwa.purchase_management.const import *
from r24_pwa.api import settings

with open(os.environ["GOOGLE_APPLICATION_CREDENTIALS"], "r") as f:
    PROJECT_ID = json.loads(f.read()).get("project_id")
params_base = {
    "debug": settings.DEBUG,
    "project": PROJECT_ID,
}


class TopView(TemplateView):
    template_name = 'home/index.html'

    def get(self, request, *args, **kwargs):
        params = params_base.copy()
        params["data"] = []
        client = datastore.Client()

        # タブ一覧を取得
        goods_map = {}
        query = client.query(kind='group')
        for group in query.fetch():
            goods_map[group.key.id] = {"name": group["name"], "goods": []}

        # 商品一覧を取得
        sum_price = {store.value: {"id": store.value,
                                   "name": COMPARE_DISP_NAME.get(store, store.value),
                                   "sum": 0} for store in CompareStore}
        query = client.query(kind='goods')
        for goods in query.fetch():
            # 最安値を登録
            goods["min_value"] = goods[f"value_{goods['min_store']}"]
            # 複数店舗の情報が登録されているか(比較されているか)？
            compare_count = 0
            goods["compare_exist"] = False
            for store in CompareStore:
                if f"value_{store.value}" in goods:
                    if goods[f"value_{store.value}"]:
                        compare_count += 1
            if compare_count >= 2:
                goods["compare_exist"] = True
            goods_map[goods["group"].id]["goods"].append(goods)
            # 合計金額を加算
            sum_price[goods['min_store']]["sum"] += goods["min_value"] * goods["count"]

        # 戻り値作成
        if request.GET.get("target", "paid") == "all":
            params["sum_price"] = list(sum_price.values())
        else:
            params["sum_price"] = [x for x in sum_price.values() if x["sum"]]
        for key, value in goods_map.items():
            params["data"].append({"id": key, "name": value["name"],
                                   "goods": sorted(value["goods"], key=lambda x: x["name"])})

        return self.render_to_response(params)

    @staticmethod
    def post(request, *args, **kwargs):
        # 値を更新
        for key, value in request.POST.items():
            # goodsの購入数の値以外は無視
            if not key.startswith("goods_count-"):
                continue
            _, _id, before = key.split("-")
            # 数値が変更されていない商品は無視
            if before == value:
                continue
            client = datastore.Client()
            key = client.key("goods", int(_id))
            entity = client.get(key)
            entity["count"] = int(value)
            client.put(entity)

        # 最新情報取得
        response = redirect("/")
        return response


class AddView(TemplateView):
    template_name = 'home/add.html'

    def get(self, request, *args, **kwargs):
        params = params_base.copy()
        client = datastore.Client()

        # タブ一覧を取得
        query = client.query(kind='group')
        group = [x["name"] for x in query.fetch()]

        # 戻り値作成
        params["group"] = group
        params["compare_stores"] = \
            [{"name": store.value, "display": COMPARE_DISP_NAME.get(store)} for store in CompareStore]

        return self.render_to_response(params)

    def post(self, request, *args, **kwargs):
        # 値を更新
        params = {key: value for key, value in request.POST.items()}
        client = datastore.Client()
        if params.get("submit") == "add_group":
            # グループの登録
            group_name = params.get("group_name")
            # 同一名称のグループが登録済みか確認
            query = client.query(kind='group')
            query.add_filter('name', '=', group_name)
            query_iter = query.fetch()
            if len([entity for entity in query_iter]) == 0:
                # 未登録の場合は登録
                key = client.key("group")
                entity = datastore.Entity(key)
                entity.update({"name": group_name})
                client.put(entity)
        elif params.get("submit") == "add_goods":
            # 商品の登録
            query = client.query(kind='group')
            query.add_filter('name', '=', params.get("group"))
            query_iter = query.fetch()
            group = [entity for entity in query_iter][0]
            key = client.key("goods")
            entity = datastore.Entity(key)
            data = {"group": group.key,
                    "name": params.get("goods_name"),
                    "count": 0,
                    "last_updated": int(datetime.now().timestamp()),
                    }

            # 最安の店舗を算出
            min_store = None
            min_value = 0
            for store in CompareStore:
                key = f"value_{store.value}"
                # 比較店舗の価格を登録
                data[key] = int(params.get(key, 0))
                if data[key]:
                    compare_value = math.ceil(data[key] *
                                              (1 - COMPARE_DISCOUNT_RATE.get(store, 0)) *
                                              (1 - COMPARE_POINT_RATE.get(store, 0)))
                    if min_store is None or compare_value < min_value:
                        min_store = store.value
                        min_value = compare_value
            # 価格未設定の場合はデフォルト値を設定
            if not min_store:
                min_store = CompareStore.RAKUTEN
            # 最安の店舗名を登録
            data["min_store"] = min_store

            entity.update(data)
            client.put(entity)

        # 最新情報取得
        response = redirect("/")
        return response


class EditView(TemplateView):
    template_name = 'home/edit.html'

    def get(self, request, *args, **kwargs):
        params = params_base.copy()
        client = datastore.Client()

        # タブ一覧を取得
        query = client.query(kind='group')
        group = [x["name"] for x in query.fetch()]

        # 商品情報を取得
        key = client.key("goods", int(request.path.split("/")[-1]))
        entity = client.get(key)

        # 所属グループを取得
        selected_key = entity["group"]
        group_entity = client.get(selected_key)

        # 戻り値作成
        params["group"] = group
        params["goods"] = entity
        params["selected_group"] = group_entity["name"]
        params["compare_stores"] = []
        for store in CompareStore:
            key = f"value_{store.value}"
            value = entity[key] if key in entity else 0
            params["compare_stores"].append({"name": store.value,
                                             "display": COMPARE_DISP_NAME.get(store),
                                             "value": value})

        return self.render_to_response(params)

    def post(self, request, *args, **kwargs):
        params = {key: value for key, value in request.POST.items()}
        client = datastore.Client()

        # 商品情報を取得
        key = client.key("goods", int(request.path.split("/")[-1]))
        entity = client.get(key)

        if params.get("submit") == "update_goods":
            # 所属グループを取得
            selected_key = entity["group"]
            group_entity = client.get(selected_key)

            update_exist = False
            if group_entity["name"] != params.get("group_name"):
                # 変更後の所属グループを取得
                query = client.query(kind='group')
                query.add_filter('name', '=', params.get("group_name"))
                query_iter = query.fetch()
                group = [entity for entity in query_iter][0]
                entity["group"] = group.key
                update_exist=True
            if entity["name"] != params.get("goods_name"):
                entity["name"] = params.get("goods_name")
                update_exist = True
            # 比較店舗の価格を設定
            for store in CompareStore:
                key = f"value_{store.value}"
                if key not in entity or entity[key] != int(params.get(key, 0)):
                    entity[key] = int(params.get(key, 0))
                    update_exist = True
            # 最安の店舗を算出
            min_store = None
            min_value = 0
            for store in CompareStore:
                key = f"value_{store.value}"
                if entity[key]:
                    compare_value = math.ceil(entity[key] *
                                              (1 - COMPARE_DISCOUNT_RATE.get(store, 0)) *
                                              (1 - COMPARE_POINT_RATE.get(store, 0)))
                    if min_store is None or compare_value < min_value:
                        min_store = store.value
                        min_value = compare_value
            # 価格未設定の場合はデフォルト値を設定
            if not min_store:
                min_store = CompareStore.RAKUTEN
            # 最安の店舗名を登録
            if "min_store" not in entity or entity["min_store"] != min_store:
                entity["min_store"] = min_store
                update_exist = True

            # 登録情報更新
            if update_exist:
                entity["last_updated"] = int(datetime.now().timestamp())
                client.put(entity)
                print("update")
        elif params.get("submit") == "delete_goods":
            pprint({"operation": "delete", "target": entity}, width=40)
            client.delete(key)

        # 最新情報取得
        response = redirect("/")
        return response


class ListView(TemplateView):
    template_name = 'home/list.html'

    def get(self, request, *args, **kwargs):
        params = params_base.copy()
        params["data"] = []
        client = datastore.Client()

        # 店舗ごとにマッピング
        store_map = {store.value: {"id": store.value,
                                   "name": COMPARE_DISP_NAME.get(store, store.value),
                                   "goods": []} for store in CompareStore}
        # 商品一覧を取得
        query = client.query(kind='goods')
        query.add_filter('count', '>', 0)
        for goods in query.fetch():
            goods["min_value"] = goods[f"value_{goods['min_store']}"]
            store_map[goods['min_store']]["goods"].append(goods)

        # 戻り値作成
        params["data"] = list(store_map.values())
        params["group_ids"] = [store.value for store in CompareStore]

        return self.render_to_response(params)

    def post(self, request, *args, **kwargs):
        # 値をクリア
        params = {key: value for key, value in request.POST.items()}
        client = datastore.Client()
        entities = []
        for key, value in params.items():
            if not key.startswith("clear_"):
                continue
            ds_key = client.key("goods", int(value))
            entity = client.get(ds_key)
            entities.append(entity)
        pprint({"operation": "clear", "targets": entities}, width=40)
        for entity in entities:
            entity["count"] = 0
            client.put(entity)

        # 最新情報取得
        response = redirect("/")
        return response
