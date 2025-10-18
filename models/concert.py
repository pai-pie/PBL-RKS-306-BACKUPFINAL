class Concert:
    def __init__(self, concert_data=None):
        if concert_data is None:
            concert_data = {}
        self.id = concert_data.get('id')
        self.name = concert_data.get('name')
        self.artist = concert_data.get('artist')
        self.date = concert_data.get('date')
        self.venue = concert_data.get('venue')
        self.price = concert_data.get('price')
        self.available_tickets = concert_data.get('available_tickets')