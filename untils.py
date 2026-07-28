from player import Player
def load_players():
    players=[]
    try:
        with open("players.txt","r")as f:
            for line in f:
                name,age,team,rating=line.strip().split(",")
                player=Player(name,int(age),team,int(rating))
                players.append(player)
    except FileNotFoundError:
        print("File not found.")
    return players

def save_players(players):
    with open("players.txt","w")as f:
        for player in players:
            f.write(f"{player.name},{player.age},{player.team},{player.rating}\n")
def find_player(players,name):
    for player in players:
        if player.name==name:
            return player
    return None
