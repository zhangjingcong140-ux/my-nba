class Player:
    def __init__(self,name,age,team,rating,position):
        self.name=name
        self.age=age
        self.team=team
        self.rating=rating
        self.position=position
    def display(self):
        print("player name:",self.name)
        print("player age:",self.age)
        print("player team:",self.team)
        print("player rating:",self.rating,)
        print("player position:",self.position)
        print()
    def increase_rating(self,amount):
        self.rating+=amount
        if self.rating>99 or self.rating<50:
            raise ValueError("Rating must be between 50 and 99")
    def decrease_rating(self,amount):
        self.rating-=amount
        if self.rating>99 or self.rating<50:
            raise ValueError("Rating must be between 50 and 99")