from player import Player
import untils
players=untils.load_players()
average_ratings=[]
team_data={}
while True:
    print("1.查看全部球员")
    print("2.添加球员")
    print("3.删除球员")
    print("4.修改能力值")
    print("5.查看所有传奇球员")
    print("6.排序")
    print("7.查看年轻球员")
    print("8.所有球员名字大写输出")
    print("9.随机抽取一位球员")
    print("10.搜索球员以输出全名")
    print("11.导出传奇球员")
    print("12.所有球员平均能力值")
    print("13.能力值最高球员")
    print("14.年龄最小球员")
    print("15.查看队伍信息")
    print("16.按队伍排序")
    print("17.队伍评分对比")
    print("18.球员交易")
    print("19.保存")
    print("20.退出")
    try:
        choice=int(input("Choose an option:"))
    except Exception:
        print("Invalid input.")
        continue
    if choice==1:
        for player in players:
            player.display()
    elif choice==2:
        name=input("Enter player name:")
        age=int(input("Enter player age:"))
        team=input("Enter player team:")
        rating=int(input("Enter palyer rating:"))
        if rating<50 or rating>99:
            raise ValueError("beyond the limit")
        player=Player(name,age,team,rating)
        players.append(player)
        print("Add player successfully.")
    elif choice==3:
        name=input("Enter player name to delete:")
        player=untils.find_player(players,name)
        if player is not None:
            players.remove(player)
        else:
            print("Player not found.")
    elif choice==4:
        name=input("Enter player name to modify rating:")
        player=untils.find_player(players,name)
        if player is not None:
                while True:
                    print("1.Increase rating")
                    print("2.Decrease rating")
                    try:
                        sub_choice=int(input("Choose an option:"))
                    except Exception:
                        print("Invalid input.")
                        continue
                    if sub_choice==1:
                        amount=int(input("Enter the amount:"))
                        try:
                            player.increase_rating(amount)
                            print("Rating increased successfully.")
                        except ValueError as e:
                            print(e)
                        break
                    elif sub_choice==2:
                        amount=int(input("Enter the amount:"))
                        try:
                            player.decrease_rating(amount)
                            print("Rating decreased successfully.")
                        except ValueError as e:
                            print(e)
                            continue
                        break
                    else:
                        print("Invalid choice")
        elif player is None:
            print("Player can not found.")
            continue
    elif choice==5:
        for player in players:
            if player.rating>=95:
                player.display()
    elif choice==6:
        while True:
            print("1.Forward sorting")
            print("2.Reverse sorting")
            print("3.Sort by age")       
            try:
                achoice=int(input("Choose an option:"))
            except ValueError as e:
                print(e)
                continue
            finally:
                print("这个finally不好加入,你让我硬加那我没办法了")
            if achoice==1:
                players.sort(key=lambda p:p.rating)
                print("Sorted successfully.")
                break
            elif achoice==2:
                players.sort(key=lambda p:p.rating,reverse=True)
                print("Sorted successfully.")
                break
            elif achoice==3:
                players.sort(key=lambda p:p.age)
                print("Sorted successfully.")
                break
            else:
                print("Invalid input")
                break
    elif choice==7:
        young=list(filter(lambda p:p.age<=22,players))
        for player in young:
            player.display()
    elif choice==8:
        print(list(map(lambda p:p.name.upper(),players)))
    elif choice==9:
        import random
        player=random.choice(players)
        player.display()
    elif choice==10:
        part=input("Type a part of player's name:")
        for player in players:
            if part in player.name:
                print(player.name)
    elif choice==11:
        with open("LegendPlayers.txt","w")as f:
            for player in players:
                        if player.rating>=95:
                            info=player.name+","+str(player.age)+","+player.team+","+str(player.rating)+"\n"
                            f.write(info)
        print("Created successfully.")
    elif choice==12:
        total_rating=0
        count=len(players)
        for player in players:
            total_rating=total_rating+player.rating
        if count>0:
            average_rating=total_rating/count
            print("The average rating is:"+str(average_rating))
    elif choice==13:
        best_player=max(players,key=lambda player:player.rating)
        best_player.display()
    elif choice==14:
        youngest_player=min(players,key=lambda player:player.age)
        youngest_player.display()
    elif choice==15:
        try:
            pteam=input("Please input the team:")
            total_rating=0
            count=0
            fullteam=""
            for player in players:
                if pteam in player.team:
                    player.display()
                    if player.rating>75:
                        total_rating=total_rating+player.rating
                        count+=1
                        fullteam=player.team
            print(fullteam,total_rating/count)
            average_rating=total_rating/count  
        except Exception as e:
            print(e)
    elif choice==16:
        teams=[]
        for player in players:
            teams.append(player.team)
        okteams={x for x in teams}
        result=list(okteams)
        result.sort(key=lambda x:x.split()[-1])
        print(result)
        players.sort(key=lambda player:player.team.split()[-1])
        for player in players:
            player.display()
    elif choice==17:
        for player in players:
            team_name=player.team
            if team_name not in team_data:
                team_data[team_name]=[0,0]
            team_data[team_name][0]+=1
            team_data[team_name][1]+=player.rating
        team_averages={}
        for team_name,info in team_data.items():
            team_averages[team_name]=info[1]/info[0]
        sorted_tuples=sorted(team_averages.items(),key=lambda item:item[1],reverse=True)
        sorted_dict=dict(sorted_tuples)
        for team,avg in sorted_dict.items():
            print(team,avg)
            print()
    elif choice==18:
        part_player=input("Choose a player to trade:")
        target_team=input("Choose a new team:")
        fteam=None
        for player in players:
            if target_team.lower() in player.team.lower():
                fteam=player.team
                break
        if fteam is None:
            print("Team not found.")
        player_found=False
        for player in players:
            if part_player.lower() in player.name.lower():
                player.team=fteam
                print(f"{player.name} has been traded to {fteam}.")
                player_found=True
        if not player_found:
            print("Player not found.")
    # elif choice==19:
    #     untils.save_players(players)
    #     print("Save successfully.")
    # elif choice==20:
    #     while True:
    #         print("If you have not save, you will lose the information.")
    #         print("1.return")
    #         print("2.exit")
    #         bchoice=int(input("Choose an option:"))
    #         if bchoice==1:
    #             break
    #         elif bchoice==2:
    #             import sys
    #             sys.exit()
    else:
        print("Invalid input")
        continue
