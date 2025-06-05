from models import RegularBike, ElectricBike


class BikeBuilder:
    def __init__(self):
        self.bike = None

    def set_bike_type(self, bike_type):
        if self.bike:
            self.bike.bike_type = bike_type
        return self

    def set_color(self, color):
        if self.bike:
            self.bike.color = color
        return self

    def set_electric(self, is_electric):
        self.bike = ElectricBike() if is_electric else RegularBike()
        return self

    def build(self):
        if not self.bike or not self.bike.bike_type or not self.bike.color:
            raise ValueError("Не вказано обов'язкові поля велосипеда")
        return self.bike
