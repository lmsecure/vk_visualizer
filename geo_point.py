
class GeoPoint:
    def __init__(self, lat: float, long: float, source: str, profile_link: str, description: str, created: str):
        self.lat = lat
        self.long = long
        self.source = source
        self.profile_link = profile_link
        self.description = description
        self.created = created

    def equals(self, other, threshold=0.001):
        from math import fabs
        return fabs(self.lat - other.lat) < threshold and fabs(self.long - other.long) < threshold

    def to_dict(self):
        result = {}
        for i in list(self.__dict__.keys()):
            try:
                result.update({i: self.__getattribute__(i)})
            except:
                continue
        return result

    def __str__(self):
        return f'lat: {self.lat}, long: {self.long}'
