from abc import ABC, abstractmethod


class DataClassBase(ABC):
    def __init__(self, id_):
        self._id = id_

    def get_id(self):
        return self._id

    @abstractmethod
    def to_dict(self):
        return {}


class Group(DataClassBase):
    def __init__(self, id_, name):
        super().__init__(id_)
        self.name = name

    def to_dict(self):
        res = {
            "name": self.name,
        }
        if self._id:
            res["id"] = self._id
        return res


class Goods(DataClassBase):
    def __init__(self, id_, group, name, count, last_updated, stores=(), min_store=None):
        super().__init__(id_)
        self.group = group
        self.name = name
        self._count = count
        self._last_updated = last_updated
        self._stores = stores
        self._min_store, self._min_value = self._get_min()

    def _get_min(self):
        min_store, min_value = None, None
        for store in self._stores:
            if store.get("value", 0):
                if min_value is None or store["value"] < min_value:
                    min_store, min_value = store.get("name"), store.get("value")
        return min_store, min_value

    def to_dict(self):
        res = {
            "group": self.group.name(),
            "name": self.name,
            "count": self._count,
            "last_updated": self._last_updated,
        }
        if self._id:
            res["id"] = self._id
        if self._min_store:
            res.update({
                "min_store": self._min_store,
                "min_value": self._min_value,
            })
        return res
