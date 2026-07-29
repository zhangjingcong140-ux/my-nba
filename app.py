import streamlit as st
import random
import untils
from player import Player

# 页面基础配置
st.set_page_config(page_title="NBA 球员管理系统", page_icon="🏀", layout="wide")

# 初始化数据到 Session State（确保网页刷新后数据不丢失）
if "players" not in st.session_state:
    st.session_state.players = untils.load_players()

players = st.session_state.players

st.title("🏀 NBA 球员交易与管理系统")

# 侧边栏菜单分类
menu = st.sidebar.radio(
    "功能导航",
    [
        "📋 球员列表与查询",
        "➕ 添加与删除",
        "⚙️ 修改与交易",
        "📊 数据统计与分析",
        "🔀 排序与展示",
        "🏀 5v5 斗牛对决",
        "💾 数据保存"
    ]
)

# 辅助函数：把 Player 列表转成标准字典，方便 Streamlit 美化表格
def players_to_dict_list(player_list):
    return [
        {
            "姓名": p.name,
            "年龄": p.age,
            "球队": p.team,
            "能力值": p.rating
        }
        for p in player_list
    ]

# ----------------- 1. 球员列表与查询 -----------------
if menu == "📋 球员列表与查询":
    st.header("📋 球员列表与模糊查询")
    
    col1, col2 = st.columns(2)
    with col1:
        search_part = st.text_input("🔍 搜索球员全名/部分名字（对应功能 10）：")
    with col2:
        search_team = st.text_input("🏟️ 搜索球队查看信息（对应功能 15）：")

    # 功能 10: 搜索球员
    if search_part:
        st.subheader("搜索结果")
        matched = [p for p in players if search_part.lower() in p.name.lower()]
        if matched:
            st.dataframe(players_to_dict_list(matched), use_container_width=True)
        else:
            st.warning("未匹配到相关球员。")

    # 功能 15: 查看队伍信息
    elif search_team:
        st.subheader(f"球队 '{search_team}' 信息")
        team_players = [p for p in players if search_team.lower() in p.team.lower()]
        if team_players:
            st.dataframe(players_to_dict_list(team_players), use_container_width=True)
            # 计算 >75 rating 的平均分
            high_rating_players = [p for p in team_players if p.rating > 75]
            if high_rating_players:
                avg = sum(p.rating for p in high_rating_players) / len(high_rating_players)
                st.info(f"🏀 该球队能力值 >75 的球员平均能力值为：**{avg:.2f}**")
        else:
            st.warning("未找到该球队信息。")

    # 功能 1: 查看全部球员
    else:
        st.subheader("全部球员列表")
        st.dataframe(players_to_dict_list(players), use_container_width=True)

# ----------------- 2. 添加与删除 -----------------
elif menu == "➕ 添加与删除":
    st.header("➕ 添加 / 🗑️ 删除球员")
    
    tab1, tab2 = st.tabs(["添加新球员", "删除球员"])
    
    # 功能 2: 添加球员
    with tab1:
        with st.form("add_player_form"):
            name = st.text_input("球员姓名：")
            age = st.number_input("年龄：", min_value=15, max_value=50, value=20)
            team = st.text_input("球队：")
            rating = st.number_input("能力值 (50-99)：", min_value=50, max_value=99, value=75)
            submit = st.form_submit_button("确认添加")
            
            if submit:
                if not name or not team:
                    st.error("姓名和球队不能为空！")
                else:
                    new_player = Player(name, age, team, rating)
                    players.append(new_player)
                    st.success(f"成功添加球员：{name}")

    # 功能 3: 删除球员
    with tab2:
        del_name = st.text_input("输入要删除的球员姓名：")
        if st.button("确认删除"):
            p_found = untils.find_player(players, del_name)
            if p_found:
                players.remove(p_found)
                st.success(f"已删除球员：{p_found.name}")
            else:
                st.error("未找到该球员！")

# ----------------- 3. 修改与交易 -----------------
elif menu == "⚙️ 修改与交易":
    st.header("⚙️ 修改能力值 / 🔄 球员交易")
    
    tab1, tab2 = st.tabs(["修改能力值", "球员交易"])
    
    # 功能 4: 修改能力值
    with tab1:
        mod_name = st.text_input("输入要修改能力值的球员姓名：")
        p_target = untils.find_player(players, mod_name) if mod_name else None
        
        if p_target:
            st.info(f"当前球员：{p_target.name} | 当前能力值：{p_target.rating}")
            action = st.radio("选择操作：", ["增加能力值", "减少能力值"])
            amount = st.number_input("调整数值：", min_value=1, max_value=50, value=1)
            
            if st.button("提交修改"):
                try:
                    if action == "增加能力值":
                        p_target.increase_rating(amount)
                    else:
                        p_target.decrease_rating(amount)
                    st.success(f"修改成功！{p_target.name} 当前能力值为：{p_target.rating}")
                except ValueError as e:
                    st.error(f"错误：{e}")
        elif mod_name:
            st.warning("未找到该球员。")

    # 功能 18: 球员交易
    with tab2:
        trade_player_name = st.text_input("选择要交易的球员姓名（模糊匹配）：")
        target_team_name = st.text_input("选择目标球队（模糊匹配）：")
        
        if st.button("执行交易"):
            fteam = None
            for p in players:
                if target_team_name.lower() in p.team.lower():
                    fteam = p.team
                    break
            
            if fteam is None:
                st.error("未找到目标球队！")
            else:
                player_found = False
                for p in players:
                    if trade_player_name.lower() in p.name.lower():
                        p.team = fteam
                        player_found = True
                        st.success(f"🎉 交易成功！{p.name} 已转会至 **{fteam}**")
                if not player_found:
                    st.error("未找到交易球员！")

# ----------------- 4. 数据统计与分析 -----------------
elif menu == "📊 数据统计与分析":
    st.header("📊 数据统计与极限分析")
    
    col1, col2, col3 = st.columns(3)
    
    # 功能 12: 平均能力值
    with col1:
        if players:
            avg_all = sum(p.rating for p in players) / len(players)
            st.metric("所有球员平均能力值", f"{avg_all:.2f}")
            
    # 功能 13: 能力值最高球员
    with col2:
        if players:
            best_p = max(players, key=lambda p: p.rating)
            st.metric("🏆 最高能力值球员", f"{best_p.name} ({best_p.rating})")

    # 功能 14: 年龄最小球员
    with col3:
        if players:
            youngest_p = min(players, key=lambda p: p.age)
            st.metric("👶 最年轻球员", f"{youngest_p.name} ({youngest_p.age}岁)")
            
    st.divider()
    
    # 功能 5 & 11: 查看并导出传奇球员
    st.subheader("⭐ 传奇球员 (Rating >= 95)")
    legend_players = [p for p in players if p.rating >= 95]
    if legend_players:
        st.dataframe(players_to_dict_list(legend_players), use_container_width=True)
        if st.button("📥 导出传奇球员到 LegendPlayers.txt（功能 11）"):
            with open("LegendPlayers.txt", "w") as f:
                for p in legend_players:
                    f.write(f"{p.name},{p.age},{p.team},{p.rating}\n")
            st.success("成功导出 LegendPlayers.txt！")
    else:
        st.write("暂无传奇球员。")

    st.divider()

    # 功能 17: 队伍评分对比
    st.subheader("📈 各队伍平均评分排行榜")
    team_data = {}
    for p in players:
        t_name = p.team
        if t_name not in team_data:
            team_data[t_name] = [0, 0]
        team_data[t_name][0] += 1
        team_data[t_name][1] += p.rating
    
    team_averages = {t: info[1]/info[0] for t, info in team_data.items()}
    sorted_teams = sorted(team_averages.items(), key=lambda x: x[1], reverse=True)
    
    # 用表格展示球队均分
    st.table([{"球队": t, "平均能力值": f"{avg:.2f}"} for t, avg in sorted_teams])

# ----------------- 5. 排序与展示 -----------------
elif menu == "🔀 排序与展示":
    st.header("🔀 排序与特色展示")
    
    sub_option = st.selectbox(
        "选择功能",
        [
            "能力值升序 (功能 6-1)",
            "能力值降序 (功能 6-2)",
            "按年龄升序 (功能 6-3)",
            "查看年轻球员 (Age <= 22) (功能 7)",
            "所有球员名字大写 (功能 8)",
            "🎲 随机抽取全池一位球员 (功能 9)",
            "🌟 随机抽取优质球员 (Rating >= 80)",  # 👈 新增功能
            "按队伍后缀排序 (功能 16)"
        ]
    )

    if sub_option == "能力值升序 (功能 6-1)":
        players.sort(key=lambda p: p.rating)
        st.dataframe(players_to_dict_list(players), use_container_width=True)

    elif sub_option == "能力值降序 (功能 6-2)":
        players.sort(key=lambda p: p.rating, reverse=True)
        st.dataframe(players_to_dict_list(players), use_container_width=True)

    elif sub_option == "按年龄升序 (功能 6-3)":
        players.sort(key=lambda p: p.age)
        st.dataframe(players_to_dict_list(players), use_container_width=True)

    elif sub_option == "查看年轻球员 (Age <= 22) (功能 7)":
        young_players = list(filter(lambda p: p.age <= 22, players))
        st.dataframe(players_to_dict_list(young_players), use_container_width=True)

    elif sub_option == "所有球员名字大写 (功能 8)":
        names_upper = list(map(lambda p: p.name.upper(), players))
        st.write(names_upper)

    elif sub_option == "🎲 随机抽取全池一位球员 (功能 9)":
        if st.button("开始抽卡！"):
            chosen = random.choice(players)
            st.balloons()  # 加上庆祝特效
            st.success(f"🎉 抽中的球员是：**{chosen.name}** | 球队：{chosen.team} | 能力值：{chosen.rating}")

    # 👈 新增：抽取 Rating >= 80 的球员
    elif sub_option == "🌟 随机抽取优质球员 (Rating >= 80)":
        high_rating_pool = [p for p in players if p.rating >= 80]
        st.caption(f"当前全库共有 **{len(high_rating_pool)}** 位能力值 $\ge$ 80 的优质球员。")
        
        if st.button("🌟 抽取精锐球员！"):
            if high_rating_pool:
                chosen = random.choice(high_rating_pool)
                st.balloons()
                st.success(f"🔥 欧气爆发！抽中优质球员：**{chosen.name}** | 球队：{chosen.team} | 能力值：**{chosen.rating}**")
            else:
                st.warning("⚠️ 当前没有能力值 $\ge$ 80 的球员，快去添加或修改球员能力值吧！")

    elif sub_option == "按队伍后缀排序 (功能 16)":
        players.sort(key=lambda p: p.team.split()[-1])
        st.dataframe(players_to_dict_list(players), use_container_width=True)

# ----------------- 6. 🏀 5v5 斗牛对决 -----------------
elif menu == "🏀 5v5 斗牛对决":
    st.header("🏀 5v5 阵容斗牛模拟器")
    st.caption("综合评分决定战力，同时加入随机手感波动的真实赛况模拟！")

    if len(players) < 10:
        st.error("⚠️ 球员总数不足 10 人，无法开启 5v5 斗牛，请先添加更多球员！")
    else:
        battle_mode = st.radio("选择斗牛模式：", ["🔥 盲盒抽卡 5v5", "🎯 自选阵容 5v5"], horizontal=True)
        
        player_dict = {f"{p.name} ({p.team} - {p.rating}分)": p for p in players}
        player_names = list(player_dict.keys())

        my_team = []
        opp_team = []

        if battle_mode == "🔥 盲盒抽卡 5v5":
            if st.button("🎲 一键随机抽取双方 5v5 阵容！"):
                selected_10 = random.sample(players, 10)
                st.session_state.my_team = selected_10[:5]
                st.session_state.opp_team = selected_10[5:]

            if "my_team" in st.session_state and "opp_team" in st.session_state:
                my_team = st.session_state.my_team
                opp_team = st.session_state.opp_team

        elif battle_mode == "🎯 自选阵容 5v5":
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("🔵 我方阵容（选5位）")
                my_selected_names = st.multiselect("挑选我方首发：", player_names, max_selections=5, key="my_select")
                my_team = [player_dict[name] for name in my_selected_names]

            with col_b:
                st.subheader("🔴 敌方阵容（选5位）")
                remaining_names = [n for n in player_names if n not in my_selected_names]
                opp_selected_names = st.multiselect("挑选敌方首发：", remaining_names, max_selections=5, key="opp_select")
                opp_team = [player_dict[name] for name in opp_selected_names]

        # 展示双方阵容与模拟比赛
        if len(my_team) == 5 and len(opp_team) == 5:
            st.divider()
            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("🔵 我方首发五虎")
                st.dataframe(players_to_dict_list(my_team), use_container_width=True)
                my_base_score = sum(p.rating for p in my_team)
                st.info(f"基础战力（总综评）：**{my_base_score}** | 均分：**{my_base_score/5:.1f}**")

            with c2:
                st.subheader("🔴 敌方首发五虎")
                st.dataframe(players_to_dict_list(opp_team), use_container_width=True)
                opp_base_score = sum(p.rating for p in opp_team)
                st.info(f"基础战力（总综评）：**{opp_base_score}** | 均分：**{opp_base_score/5:.1f}**")

            st.divider()
            
            if st.button("🚀 开启模拟对决！", type="primary"):
                my_luck = random.uniform(0.88, 1.12)
                opp_luck = random.uniform(0.88, 1.12)
                
                my_final_score = int(my_base_score * my_luck)
                opp_final_score = int(opp_base_score * opp_luck)

                st.subheader("📊 比赛最终比分")
                res_col1, res_col2 = st.columns(2)
                res_col1.metric("🔵 我方得分", my_final_score, delta=f"手感修正: {my_luck*100:.1f}%")
                res_col2.metric("🔴 敌方得分", opp_final_score, delta=f"手感修正: {opp_luck*100:.1f}%")

                if my_final_score > opp_final_score:
                    st.balloons()
                    st.success(f"🏆 恭喜！我方以 **{my_final_score} : {opp_final_score}** 赢得了这场 5v5 斗牛赛！")
                elif my_final_score < opp_final_score:
                    st.error(f"💔 遗憾！敌方以 **{opp_final_score} : {my_final_score}** 拿下了胜利。")
                else:
                    st.warning(f"🤝 双方手感平平，以 **{my_final_score} : {opp_final_score}** 打成平手！")
        else:
            if battle_mode == "🎯 自选阵容 5v5":
                st.warning("💡 请在左右两侧各选满 5 名球员以启动比赛模拟！")

# ----------------- 7. 数据保存 -----------------
elif menu == "💾 数据保存":
    st.header("💾 数据保存 (功能 19)")
    st.write("点击下方按钮把当前网页中的修改保存回文件中：")
    if st.button("💾 保存数据", type="primary"):
        untils.save_players(players)
        st.success("数据已成功保存到本地！")
