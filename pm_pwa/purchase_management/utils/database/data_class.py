import math
from abc import ABC, abstractmethod
from pm_pwa.purchase_management.const import *


class DataClassBase(ABC):
    def __init__(self, id_):
        self._id = id_

    def get_id(self):
        return self._id

    @abstractmethod
    def to_dict(self):
        return {}


class Group(DataClassBase):
    def __init__(self, key, name):
        super().__init__(key.id)
        self.key = key
        self.name = name

    def to_dict(self):
        res = {
            "name": self.name,
        }
        if self._id:
            res["id"] = self._id
        return res


class Goods(DataClassBase):
    def __init__(self, id_, group, name, count, last_updated, stores=()):
        super().__init__(id_)
        self.group = group
        self.name = name
        self.count = count
        self.last_updated = last_updated
        self.stores = stores
        self._min_store, self._min_value, self._compare = self._get_stores_info()

    def _get_stores_info(self):
        min_store, min_value, compare = None, None, 0
        discount_value = None
        for key, value in self.stores.items():
            if value:
                compare += 1
                store_value = math.ceil(value * (1 - COMPARE_DISCOUNT_RATE.get(key, 0)) *
                                                (1 - COMPARE_POINT_RATE.get(key, 0)))
                if min_value is None or store_value < discount_value:
                    min_store, min_value = key, value
                    discount_value = store_value
        return min_store, min_value, compare

    def to_dict(self):
        res = {
            "group_name": self.group.name,
            "group_id": self.group.get_id(),
            "name": self.name,
            "count": self.count,
            "compare": self._compare,
            "last_updated": self.last_updated,
        }
        if self._id:
            res["id"] = self._id
        if self._min_store:
            res.update({
                "min_store": self._min_store,
                "min_value": self._min_value,
            })
        return res
