# Each interaction is going to be defined with three attributes (sender, recipient, and data). Might change to command but unsure
# if we will need to add anything else later.
class Interaction:
    def __init__(self, sender, recipient, data):
        self.sender = sender
        self.recipient = recipient
        self.data = data

    # To convert the inmteraction into a type that we can use for block structure.
    def to_dict(self):
        return {
        'sender': self.sender,
        'recipient': self.recipient,
        'data': self.data,
    }