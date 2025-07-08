class dataProcess:
    
    def __init__(self, data: dict):
        self.data = data
        
    def getValue(self, key: str, default=None):
        return self.data.get(key, default)