from enum import Enum
from google.cloud import datastore

from pm_pwa.purchase_management.utils.database.data_class import Group, Goods

class DataTypes(Enum):
    group = "group"
    goods = "goods"

class DataStore:
    def __init__(self):
        self._client = datastore.Client()

    def add_group(self, group):
        group_name = group.name
        query = self._client.query(kind='group')
        query.add_filter('name', '=', group_name)
        query_iter = query.fetch()
        if len([entity for entity in query_iter]) == 0:
            # 未登録の場合は登録
            key = self._client.key("group")
            entity = datastore.Entity(key)
            entity.update({"name": group_name})
            self._client.put(entity)

    def get_all_group(self):
        res = []
        query = self._client.query(kind=DataTypes.group.value)
        for group in query.fetch():
            res.append(Group(group.key, **dict(group)))
        return res

    def get_group(self, name):
        query = self._client.query(kind=DataTypes.group.value)
        query.add_filter('name', '=', name)
        query_iter = query.fetch()
        groups = [entity for entity in query_iter]
        if groups:
            group = groups[0]
            return Group(group.key, **dict(group))
        return None

    def get_group_by_id(self, id_):
        key = self._client.key(DataTypes.group.value, int(id_))
        group = self._client.get(key)
        return Group(group.key, **dict(group))

    def add_goods(self, goods):
        if goods.get_id():
            key =  self._client.key(DataTypes.goods.value, goods.get_id())
        else:
            key = self._client.key("goods")
        entity = datastore.Entity(key)
        data = {"group": goods.group.key,
                "name": goods.name,
                "count": goods.count,
                "last_updated": goods.last_updated,
                }
        for key, value in goods.stores.items():
            column_key = f'value_{key}'
            data[column_key] = value

        entity.update(data)
        self._client.put(entity)

    def get_all_goods(self):
        res = []
        groups = {x.get_id(): x for x in self.get_all_group()}
        query = self._client.query(kind=DataTypes.goods.value)
        for goods in query.fetch():
            stores = {}
            for key, value in dict(goods).items():
                if key.startswith("value_"):
                    stores[key.replace("value_", "")] = value
            args = {
                "id_": goods.key.id,
                "stores": stores,
                "group": groups[goods["group"].id],
            }
            for key in ["name", "count", "last_updated"]:
                args[key] = goods.get(key)
            res.append(Goods(**args))

        return res

    def get_goods(self, id_):
        key = self._client.key(DataTypes.goods.value, int(id_))
        goods = self._client.get(key)
        stores = {}
        for key, value in dict(goods).items():
            if key.startswith("value_"):
                stores[key.replace("value_", "")] = value
        args = {
            "id_": goods.key.id,
            "stores": stores,
            "group": self.get_group_by_id(goods["group"].id),
        }
        for key in ["name", "count", "last_updated"]:
            args[key] = goods.get(key)
        return Goods(**args)

    def get_buy_goods(self):
        query = self._client.query(kind='goods')
        query.add_filter('count', '>', 0)
        res = []
        for goods in query.fetch():
            stores = {}
            for key, value in dict(goods).items():
                if key.startswith("value_"):
                    stores[key.replace("value_", "")] = value
            args = {
                "id_": goods.key.id,
                "stores": stores,
                "group": self.get_group_by_id(goods["group"].id),
            }
            for key in ["name", "count", "last_updated"]:
                args[key] = goods.get(key)
            res.append(Goods(**args))
        return res

    def update_goods_count(self, id_, count):
        key = self._client.key(DataTypes.goods.value, int(id_))
        entity = self._client.get(key)
        entity["count"] = count
        self._client.put(entity)

    def delete_goods(self, goods):
        key = self._client.key(DataTypes.goods.value, goods.get_id())
        self._client.delete(key)
