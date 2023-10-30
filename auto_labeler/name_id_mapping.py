class NameIDMapping():
    def __init__(self):
        self._id_for_name = {}
        self._name_for_id = {}

    def add(self, id, name):
        self._id_for_name[name] = id
        self._name_for_id[id] = name
    
    def id_for_name(self, name):
        return self._id_for_name[name]

    def has_name(self, name):
        return name in self._id_for_name

    def name_for_id(self, id):
        return self._name_for_id[id]
