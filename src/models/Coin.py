class Coin:

    """
    Represents a single cryptocurrency with its ID, name, and option to futher expand
    
    """

    def __init__(self, _id,_name):
        self.id = _id
        self.name = _name

    def get_name(self) -> str:
        return self.name
    
    def get_id(self) -> str:
        return self.id
    
    def __repr__(self):
        return f"Coin(id={self.id}, name={self.name})"
    

