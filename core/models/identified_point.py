class IdentifiedPoint(object):
    """Identified point"""

    def __init__(self, identifier: int):
        """
        Identified point constructor

        :param identifier: Identifier of point
        """
        self.identifier = identifier

    def __str__(self):
        return "{identifier: %d}" % self.identifier

    def __hash__(self):
        return self.identifier
