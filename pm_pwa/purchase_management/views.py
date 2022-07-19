import json
import os
from datetime import datetime

from django.shortcuts import redirect
from django.views.generic import TemplateView
from pprint import pprint

from pm_pwa.purchase_management.const import *
from pm_pwa.api import settings
from pm_pwa.purchase_management.utils.database.datastore import DataStore
from pm_pwa.purchase_management.utils.database.data_class import Group, Goods

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

        # タブ一覧を取得
        goods_map = {}
        datastore_ = DataStore()
        for group in [x.to_dict() for x in datastore_.get_all_group()]:
            goods_map[group["id"]] = {"name": group["name"], "goods": []}

        # 商品一覧を取得
        sum_price = {store.value: {"id": store.value,
                                   "name": COMPARE_DISP_NAME.get(store, store.value),
                                   "sum": 0} for store in CompareStore}
        for goods in [x.to_dict() for x in datastore_.get_all_goods()]:
            # 複数店舗の情報が登録されているか(比較されているか)？
            goods["compare_exist"] = True if goods["compare"] > 1 else False
            goods_map[goods["group_id"]]["goods"].append(goods)
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
        datastore_ = DataStore()
        for key, value in request.POST.items():
            print(key, value)
            # goodsの購入数の値以外は無視
            if not key.startswith("goods_count-"):
                continue
            _, _id, before = key.split("-")
            if _id == 5673742378205184:
                print(before, value)
            # 数値が変更されていない商品は無視
            if before == value:
                continue
            datastore_.update_goods_count(int(_id), int(value))

        # 最新情報取得
        response = redirect("/")
        return response


class AddView(TemplateView):
    template_name = 'home/add.html'

    def get(self, request, *args, **kwargs):
        params = params_base.copy()
        datastore_ = DataStore()

        # タブ一覧を取得
        group = [x.to_dict().get("name") for x in datastore_.get_all_group()]

        # 戻り値作成
        params["group"] = group
        params["compare_stores"] = \
            [{"name": store.value, "display": COMPARE_DISP_NAME.get(store)} for store in CompareStore]

        return self.render_to_response(params)

    def post(self, request, *args, **kwargs):
        # 値を更新
        params = {key: value for key, value in request.POST.items()}
        datastore_ = DataStore()
        if params.get("submit") == "add_group":
            # グループの登録
            group_name = params.get("group_name")
            datastore_.add_group(Group(None, group_name))
        elif params.get("submit") == "add_goods":
            # 商品の登録
            group = datastore_.get_group(params.get("group"))
            stores = {}
            for store in CompareStore:
                key = f"value_{store.value}"
                stores[store.value] = int(params.get(key, 0))
            goods = Goods(None, group, params.get("goods_name"), 0, int(datetime.now().timestamp()), stores)
            datastore_.add_goods(goods)

        # 最新情報取得
        response = redirect("/")
        return response


class EditView(TemplateView):
    template_name = 'home/edit.html'

    def get(self, request, *args, **kwargs):
        params = params_base.copy()
        datastore_ = DataStore()

        # タブ一覧を取得
        group = [x.to_dict().get("name") for x in datastore_.get_all_group()]

        # 商品情報を取得
        goods = datastore_.get_goods(int(request.path.split("/")[-1]))

        # 戻り値作成
        params["group"] = group
        params["goods"] = goods.to_dict()
        params["selected_group"] = goods.group.name
        params["compare_stores"] = []
        for store in CompareStore:
            value = goods.stores[store.value] if store.value in goods.stores else 0
            params["compare_stores"].append({"name": store.value,
                                             "display": COMPARE_DISP_NAME.get(store),
                                             "value": value})

        return self.render_to_response(params)

    def post(self, request, *args, **kwargs):
        params = {key: value for key, value in request.POST.items()}
        datastore_ = DataStore()

        # 商品情報を取得
        goods = datastore_.get_goods(int(request.path.split("/")[-1]))

        if params.get("submit") == "update_goods":
            update_exist = False
            if goods.group.name != params.get("group_name"):
                # 所属グループを更新
                goods.group = datastore_.get_group(params.get("group_name"))
                update_exist=True
            if goods.name != params.get("goods_name"):
                goods.name = params.get("goods_name")
                update_exist = True
            # 比較店舗の価格を設定
            for store in CompareStore:
                key = f"value_{store.value}"
                if store.value not in goods.stores or goods.stores[store.value] != int(params.get(key, 0)):
                    goods.stores[store.value] = int(params.get(key, 0))
                    update_exist = True

            # 登録情報更新
            if update_exist:
                goods.last_updated = int(datetime.now().timestamp())
                datastore_.add_goods(goods)
                print("update")
        elif params.get("submit") == "delete_goods":
            pprint({"operation": "delete", "target": goods.to_dict()}, width=40)
            datastore_.delete_goods(goods)

        # 最新情報取得
        response = redirect("/")
        return response


class ListView(TemplateView):
    template_name = 'home/list.html'

    def get(self, request, *args, **kwargs):
        params = params_base.copy()
        params["data"] = []
        datastore_ = DataStore()

        # 店舗ごとにマッピング
        store_map = {store.value: {"id": store.value,
                                   "name": COMPARE_DISP_NAME.get(store, store.value),
                                   "goods": []} for store in CompareStore}
        # 商品一覧を取得
        for goods in datastore_.get_buy_goods():
            goods_dict = goods.to_dict()
            store_map[goods_dict['min_store']]["goods"].append(goods_dict)

        # 戻り値作成
        params["data"] = list(store_map.values())
        params["group_ids"] = [store.value for store in CompareStore]

        return self.render_to_response(params)

    def post(self, request, *args, **kwargs):
        # 値をクリア
        params = {key: value for key, value in request.POST.items()}
        datastore_ = DataStore()

        clear_goods = []
        for key, value in params.items():
            if not key.startswith("clear_"):
                continue
            goods = datastore_.get_goods(int(value))
            clear_goods.append(goods)
        pprint({"operation": "clear", "targets": [x.to_dict() for x in clear_goods]}, width=40)
        for goods in clear_goods:
            datastore_.update_goods_count(goods.get_id(), 0)

        # 最新情報取得
        response = redirect("/")
        return response
