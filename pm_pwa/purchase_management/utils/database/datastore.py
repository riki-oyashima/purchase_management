from google.cloud import datastore

from pm_pwa.purchase_management.utils.database.data_class import Group, Goods


class DataStore:
    def __init__(self):
        self._client = datastore.Client()

    def get_all_group(self):
        res = []
        query = self._client.query(kind='group')
        for group in query.fetch():
            res.append(Group(group.key.id, **dict(group)))
        return res

    def get_all_goods(self):
        res = []
        groups = {x.get_id(): x for x in self.get_all_group()}
        query = self._client.query(kind='goods')
        for goods in query.fetch():
            values = []
            for key, value in dict(goods).items():
                if key.startswith("value_"):
                    values.append({
                        "name": key.replace("value_"),
                        "value": value,
                    })
            args = {
                "id_": goods.key.id,
                "values": values,
                "group": groups[goods["group"].id],
            }
            for key in ["name", "count", "last_updated", "min_store"]:
                args[key] = goods.get(key)
            res.append(Goods(**args))

        return res
