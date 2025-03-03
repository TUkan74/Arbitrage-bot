class Coin:

    """
    Represents a single cryptocurrency with its ID, name, and option to futher expand
    
    """

    def __init__(self, id,name):
        self._id = id
        self._name = name

    def get_name(self):
        return self._name
    
    def get_id(self):
        return self._id
    
    def __repr__(self):
        return f"Coin(id={self._id}, name={self._name}, symbol={self._symbol})"
    

