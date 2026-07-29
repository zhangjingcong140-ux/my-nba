import streamlit as st
import random
import untils
from player import Player

# 页面基础配置
st.set_page_config(page_title="NBA 球员管理系统", page_icon="🏀", layout="wide")

# 初始化数据到 Session State
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

# 辅助函数：转换为字典列表（使用 getattr 做了兼容防护）
def players_to_dict_list(player_list):
    return [
        {
            "姓名": p.name,
            "年龄": p.age,
            "球队": p.team,
            "能力值": p.rating,
            "位置": getattr(p, "position", "未知")
        }
        for p in player_list
    ]

# ----------------- 1. 球员列表与查询 -----------------
if menu == "📋 球员列表与查询":
    st.header("📋 球员列表与模糊查询")
    
    col1, col2 = st.columns(2)
    with col1:
        search_part = st.text_input("🔍 搜索球员全名/部分名字：")
    with col2:
        search_team = st.text_input("🏟️ 搜索球队查看信息：")

    if search_part:
        st.subheader("搜索结果")
        matched = [p for p in players if search_part.lower() in p.name.lower()]
        if matched:
            st.dataframe(players_to_dict_list(matched), use_container_width=True)
        else:
            st.warning("未匹配到相关球员。")

    elif search_team:
        st.subheader(f"球队 '{search_team}' 信息")
        team_players = [p for p in players if search_team.lower() in p.team.lower()]
        if team_players:
            st.dataframe(players_to_dict_list(team_players), use_container_width=True)
            high_rating_players = [p for p in team_players if p.rating > 75]
            if high_rating_players:
                avg = sum(p.rating for p in high_rating_players) / len(high_rating_players)
                st.info(f"🏀 该球队能力值 >75 的球员平均能力值为：**{avg:.2f}**")
        else:
            st.warning("未找到该球队信息。")

    else:
        st.subheader("全部球员列表")
        st.dataframe(players_to_dict_list(players), use_container_width=True)

# ----------------- 2. 添加与删除 -----------------
elif menu == "➕ 添加与删除":
    st.header("➕ 添加 / 🗑️ 删除球员")
    
    tab1, tab2 = st.tabs(["添加新球员", "删除球员"])
    
    with tab1:
        with st.form("add_player_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                name = st.text_input("球员姓名：")
                age = st.number_input("年龄：", min_value=15, max_value=50, value=20)
            with col_b:
                team = st.text_input("球队：")
                rating = st.number_input("能力值 (50-99)：", min_value=50, max_value=99, value=75)
            
            # 👇 已改回中文位置选项
            position = st.selectbox("球员位置：", ["控卫", "分卫", "小前", "大前", "中锋"])
            
            submit = st.form_submit_button("确认添加")
            
            if submit:
                if not name or not team:
                    st.error("姓名和球队不能为空！")
                else:
                    new_player = Player(name, age, team, rating, position)
                    players.append(new_player)
                    st.success(f"成功添加球员：{name} [{position}]")

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
    st.header("⚙️ 修改能力值/位置 / 🔄 球员交易")
    
    tab1, tab2 = st.tabs(["修改能力值/位置", "球员交易"])
    
    with tab1:
        mod_name = st.text_input("输入要修改的球员姓名：")
        p_target = untils.find_player(players, mod_name) if mod_name else None
        
        if p_target:
            curr_pos = getattr(p_target, "position", "未知")
            st.info(f"当前球员：**{p_target.name}** | 位置：**{curr_pos}** | 当前能力值：**{p_target.rating}**")
            
            col_mod1, col_mod2 = st.columns(2)
            with col_mod1:
                action = st.radio("修改能力值：", ["增加能力值", "减少能力值"])
                amount = st.number_input("调整数值：", min_value=1, max_value=50, value=1)
            with col_mod2:
                # 👇 已改回中文位置选项
                pos_options = ["控卫", "分卫", "小前", "大前", "中锋"]
                default_idx = pos_options.index(curr_pos) if curr_pos in pos_options else 0
                new_pos = st.selectbox("更新位置（可选）：", pos_options, index=default_idx)

            if st.button("提交修改"):
                try:
                    if action == "增加能力值":
                        p_target.increase_rating(amount)
                    else:
                        p_target.decrease_rating(amount)
                    p_target.position = new_pos
                    st.success(f"修改成功！{p_target.name} 位置：{p_target.position} | 当前能力值：{p_target.rating}")
                except ValueError as e:
                    st.error(f"错误：{e}")
        elif mod_name:
            st.warning("未找到该球员。")

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
    
    with col1:
        if players:
            avg_all = sum(p.rating for p in players) / len(players)
            st.metric("所有球员平均能力值", f"{avg_all:.2f}")
            
    with col2:
        if players:
            best_p = max(players, key=lambda p: p.rating)
            st.metric("🏆 最高能力值球员", f"{best_p.name} ({best_p.rating})")

    with col3:
        if players:
            youngest_p = min(players, key=lambda p: p.age)
            st.metric("👶 最年轻球员", f"{youngest_p.name} ({youngest_p.age}岁)")
            
    st.divider()
    
    st.subheader("⭐ 传奇球员 (Rating >= 95)")
    legend_players = [p for p in players if p.rating >= 95]
    if legend_players:
        st.dataframe(players_to_dict_list(legend_players), use_container_width=True)
        if st.button("📥 导出传奇球员到 LegendPlayers.txt"):
            with open("LegendPlayers.txt", "w", encoding="utf-8") as f:
                for p in legend_players:
                    f.write(f"{p.name},{p.age},{p.team},{p.rating},{getattr(p, 'position', '未知')}\n")
            st.success("成功导出 LegendPlayers.txt！")
    else:
        st.write("暂无传奇球员。")

    st.divider()

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
    st.table([{"球队": t, "平均能力值": f"{avg:.2f}"} for t, avg in sorted_teams])

# ----------------- 5. 排序与展示 -----------------
elif menu == "🔀 排序与展示":
    st.header("🔀 排序与特色展示")
    
    sub_option = st.selectbox(
        "选择功能",
        [
            "能力值升序",
            "能力值降序",
            "按年龄升序",
            "查看年轻球员 (Age <= 22)",
            "所有球员名字大写",
            "🎲 随机抽取全池一位球员",
            "🌟 随机抽取优质球员 (Rating >= 80)",
            "按队伍后缀排序"
        ]
    )

    if sub_option == "能力值升序":
        players.sort(key=lambda p: p.rating)
        st.dataframe(players_to_dict_list(players), use_container_width=True)

    elif sub_option == "能力值降序":
        players.sort(key=lambda p: p.rating, reverse=True)
        st.dataframe(players_to_dict_list(players), use_container_width=True)

    elif sub_option == "按年龄升序":
        players.sort(key=lambda p: p.age)
        st.dataframe(players_to_dict_list(players), use_container_width=True)

    elif sub_option == "查看年轻球员 (Age <= 22)":
        young_players = list(filter(lambda p: p.age <= 22, players))
        st.dataframe(players_to_dict_list(young_players), use_container_width=True)

    elif sub_option == "所有球员名字大写":
        names_upper = list(map(lambda p: p.name.upper(), players))
        st.write(names_upper)

    elif sub_option == "🎲 随机抽取全池一位球员":
        if st.button("开始抽卡！"):
            chosen = random.choice(players)
            pos = getattr(chosen, "position", "未知")
            st.balloons()
            st.success(f"🎉 抽中的球员是：**{chosen.name}** | 位置：[{pos}] | 球队：{chosen.team} | 能力值：{chosen.rating}")

    elif sub_option == "🌟 随机抽取优质球员 (Rating >= 80)":
        high_rating_pool = [p for p in players if p.rating >= 80]
        st.caption(f"当前全库共有 **{len(high_rating_pool)}** 位能力值 $\ge$ 80 的优质球员。")
        
        if st.button("🌟 抽取精锐球员！"):
            if high_rating_pool:
                chosen = random.choice(high_rating_pool)
                pos = getattr(chosen, "position", "未知")
                st.balloons()
                st.success(f"🔥 欧气爆发！抽中优质球员：**{chosen.name}** | 位置：[{pos}] | 球队：{chosen.team} | 能力值：**{chosen.rating}**")
            else:
                st.warning("⚠️ 当前没有能力值 $\ge$ 80 的球员！")

    elif sub_option == "按队伍后缀排序":
        players.sort(key=lambda p: p.team.split()[-1])
        st.dataframe(players_to_dict_list(players), use_container_width=True)

# ----------------- 6. 🏀 5v5 斗牛对决 -----------------
elif menu == "🏀 5v5 斗牛对决":
    st.header("🏀 5v5 阵容斗牛模拟器")
    st.caption("支持盲盒、自选及【💰 80+ 球员资金竞拍】模式！")

    if len(players) < 10:
        st.error("⚠️ 球员总数不足 10 人，无法开启 5v5 斗牛，请先添加更多球员！")
    else:
        battle_mode = st.radio("选择斗牛模式：", ["🔥 盲盒抽卡 5v5", "🎯 自选阵容 5v5", "💰 资金竞拍 5v5"], horizontal=True)
        
        player_dict = {f"{p.name} [{getattr(p, 'position', '未知')}] ({p.team} - {p.rating}分)": p for p in players}
        player_names = list(player_dict.keys())

        blue_team = []
        red_team = []

        def reset_match_state():
            st.session_state.pop("blue_item", None)
            st.session_state.pop("red_item", None)
            st.session_state.blue_drawn = False
            st.session_state.red_drawn = False

        if battle_mode == "🔥 盲盒抽卡 5v5":
            if st.button("🎲 一键随机抽取双方 5v5 阵容！"):
                selected_10 = random.sample(players, 10)
                st.session_state.blue_team = selected_10[:5]
                st.session_state.red_team = selected_10[5:]
                reset_match_state()

            if "blue_team" in st.session_state and "red_team" in st.session_state:
                blue_team = st.session_state.blue_team
                red_team = st.session_state.red_team

        elif battle_mode == "🎯 自选阵容 5v5":
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("🔵 蓝方阵容（选5位）")
                blue_selected_names = st.multiselect("挑选蓝方首发：", player_names, max_selections=5, key="blue_select")
                blue_team = [player_dict[name] for name in blue_selected_names]

            with col_b:
                st.subheader("🔴 红方阵容（选5位）")
                remaining_names = [n for n in player_names if n not in blue_selected_names]
                red_selected_names = st.multiselect("挑选红方首发：", remaining_names, max_selections=5, key="red_select")
                red_team = [player_dict[name] for name in red_selected_names]

            if len(blue_team) != 5 or len(red_team) != 5:
                reset_match_state()

        elif battle_mode == "💰 资金竞拍 5v5":
            st.subheader("💰 赛前球员竞拍大厅")
            st.caption("双方初始资金 $20。系统随机抽出 80+ 球员供竞拍，资金耗尽将按顺序免费分派随机球员！")

            if "auction_inited" not in st.session_state or not st.session_state.auction_inited:
                st.session_state.blue_money = 20
                st.session_state.red_money = 20
                st.session_state.auction_blue_team = []
                st.session_state.auction_red_team = []
                st.session_state.current_target_player = None
                st.session_state.auction_logs = []
                st.session_state.auction_inited = True

            if st.button("🔄 重置/重新开始竞拍"):
                st.session_state.auction_inited = False
                reset_match_state()
                st.rerun()

            col_m1, col_m2 = st.columns(2)
            col_m1.metric("🔵 蓝方剩余资金", f"${st.session_state.blue_money}", delta=f"已选 {len(st.session_state.auction_blue_team)}/5 人")
            col_m2.metric("🔴 红方剩余资金", f"${st.session_state.red_money}", delta=f"已选 {len(st.session_state.auction_red_team)}/5 人")

            auc_blue = st.session_state.auction_blue_team
            auc_red = st.session_state.auction_red_team

            if len(auc_blue) < 5 or len(auc_red) < 5:
                used_players = set(auc_blue + auc_red)
                available_pool = [p for p in players if p not in used_players]
                high_rating_pool = [p for p in available_pool if p.rating >= 80]

                both_money_empty = (st.session_state.blue_money <= 0 and st.session_state.red_money <= 0)
                
                if both_money_empty or not high_rating_pool:
                    st.warning("⚠️ 资金已耗尽或无剩余 80+ 球员！系统将自动按顺序免费为双方补充剩余阵容。")
                    if st.button("⚡ 自动按顺序补满双方阵容"):
                        random.shuffle(available_pool)
                        while len(st.session_state.auction_blue_team) < 5 and available_pool:
                            st.session_state.auction_blue_team.append(available_pool.pop(0))
                        while len(st.session_state.auction_red_team) < 5 and available_pool:
                            st.session_state.auction_red_team.append(available_pool.pop(0))
                        reset_match_state()
                        st.rerun()
                else:
                    st.divider()
                    if st.button("🎲 抽取下一位 80+ 竞拍球员"):
                        st.session_state.current_target_player = random.choice(high_rating_pool)
                        st.rerun()

                    target = st.session_state.current_target_player
                    if target:
                        pos = getattr(target, "position", "未知")
                        st.info(f"🌟 **当前竞拍球员：** **{target.name}** （位置：[{pos}] | 球队：{target.team} | 能力值：**{target.rating}**）")

                        with st.form("auction_form"):
                            st.write("请双方选择出价（不可超过自身剩余资金，选择 $0 代表弃权）：")
                            col_b_bid, col_r_bid = st.columns(2)
                            
                            with col_b_bid:
                                max_b = max(0, st.session_state.blue_money)
                                blue_bid = st.number_input("🔵 蓝方出价 ($)", min_value=0, max_value=max_b, value=0, step=1)

                            with col_r_bid:
                                max_r = max(0, st.session_state.red_money)
                                red_bid = st.number_input("🔴 红方出价 ($)", min_value=0, max_value=max_r, value=0, step=1)

                            submit_bid = st.form_submit_button("🔨 确认出价/结算本轮竞拍")

                            if submit_bid:
                                blue_full = len(auc_blue) >= 5
                                red_full = len(auc_red) >= 5

                                if blue_full:
                                    blue_bid = -1
                                if red_full:
                                    red_bid = -1

                                if blue_bid == 0 and red_bid == 0:
                                    st.warning("双方均弃权，该球员流拍！点击重新抽取。")
                                    st.session_state.current_target_player = None
                                elif blue_bid > red_bid:
                                    st.session_state.blue_money -= blue_bid
                                    st.session_state.auction_blue_team.append(target)
                                    st.session_state.auction_logs.append(f"🔵 蓝方以 **${blue_bid}** 竞拍成功获得 **{target.name}** [{getattr(target, 'position', '未知')}] ({target.rating}分)")
                                    st.session_state.current_target_player = None
                                    reset_match_state()
                                    st.rerun()
                                elif red_bid > blue_bid:
                                    st.session_state.red_money -= red_bid
                                    st.session_state.auction_red_team.append(target)
                                    st.session_state.auction_logs.append(f"🔴 红方以 **${red_bid}** 竞拍成功获得 **{target.name}** [{getattr(target, 'position', '未知')}] ({target.rating}分)")
                                    st.session_state.current_target_player = None
                                    reset_match_state()
                                    st.rerun()
                                else:
                                    winner = random.choice(["blue", "red"])
                                    if winner == "blue" and not blue_full:
                                        st.session_state.blue_money -= blue_bid
                                        st.session_state.auction_blue_team.append(target)
                                        st.session_state.auction_logs.append(f"🎲 双方出价相同，系统抽签：🔵 蓝方获得 **{target.name}** [{getattr(target, 'position', '未知')}]")
                                    else:
                                        st.session_state.red_money -= red_bid
                                        st.session_state.auction_red_team.append(target)
                                        st.session_state.auction_logs.append(f"🎲 双方出价相同，系统抽签：🔴 红方获得 **{target.name}** [{getattr(target, 'position', '未知')}]")
                                    st.session_state.current_target_player = None
                                    reset_match_state()
                                    st.rerun()

            if st.session_state.auction_logs:
                with st.expander("📜 查看本局竞拍日志记录"):
                    for log in st.session_state.auction_logs:
                        st.write(log)

            blue_team = st.session_state.auction_blue_team
            red_team = st.session_state.auction_red_team

        # ----------------- 比赛流程展示 -----------------
        if len(blue_team) == 5 and len(red_team) == 5:
            st.divider()

            calc_blue_team = [Player(p.name, p.age, p.team, p.rating, getattr(p, "position", "未知")) for p in blue_team]
            calc_red_team = [Player(p.name, p.age, p.team, p.rating, getattr(p, "position", "未知")) for p in red_team]

            # 1. 展示双方阵容
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("🔵 蓝方首发五虎")
                st.dataframe(players_to_dict_list(calc_blue_team), use_container_width=True)
                blue_base_score = sum(p.rating for p in calc_blue_team)
                st.info(f"基础战力（总综评）：**{blue_base_score}** | 均分：**{blue_base_score/5:.1f}**")

            with c2:
                st.subheader("🔴 红方首发五虎")
                st.dataframe(players_to_dict_list(calc_red_team), use_container_width=True)
                red_base_score = sum(p.rating for p in calc_red_team)
                st.info(f"基础战力（总综评）：**{red_base_score}** | 均分：**{red_base_score/5:.1f}**")

            st.divider()

            # 2. 道具抽卡
            if "blue_drawn" not in st.session_state:
                st.session_state.blue_drawn = False
            if "red_drawn" not in st.session_state:
                st.session_state.red_drawn = False

            items_pool = [
                {"name": "🧪 佳得乐", "desc": "佳得乐补充体力", "effect_detail": "⚡ 效果：最终得分 +10", "effect": "self_add_10"},
                {"name": "🎮 游戏机", "desc": "昨晚打游戏", "effect_detail": "💤 效果：最终得分 -10", "effect": "self_sub_10"},
                {"name": "👁️ 红色的眼睛", "desc": "全员觉醒", "effect_detail": "🔥 效果：最终得分 +20", "effect": "self_add_20"},
                {"name": "🍾 酒瓶", "desc": "昨晚夜店喝酒", "effect_detail": "😵 效果：最终得分 -20", "effect": "self_sub_20"},
                {"name": "👄 嘴", "desc": "喷垃圾话", "effect_detail": "💢 效果：对方最终得分 -20", "effect": "opp_sub_20"},
                {"name": "🦶 脚", "desc": "垫脚", "effect_detail": "🚑 效果：对方评分最高的球员能力值变为 80", "effect": "ankle_breaker"}
            ]

            st.subheader("🎁 赛前随机抽取道具事件（每局限抽一次）")
            col_item1, col_item2 = st.columns(2)

            with col_item1:
                btn_blue = st.button("🎲 蓝方抽取赛前道具", disabled=st.session_state.blue_drawn, key="btn_blue_draw")
                if btn_blue:
                    st.session_state.blue_item = random.choice(items_pool)
                    st.session_state.blue_drawn = True
                    st.rerun()

                if "blue_item" in st.session_state and st.session_state.blue_drawn:
                    item = st.session_state.blue_item
                    st.info(f"🔵 **蓝方抽到：[{item.get('name', '道具')}]**（{item.get('desc', '')}）")
                    st.caption(f"{item.get('effect_detail', '⚡ 效果已生效')}")

            with col_item2:
                btn_red = st.button("🎲 红方抽取赛前道具", disabled=st.session_state.red_drawn, key="btn_red_draw")
                if btn_red:
                    st.session_state.red_item = random.choice(items_pool)
                    st.session_state.red_drawn = True
                    st.rerun()

                if "red_item" in st.session_state and st.session_state.red_drawn:
                    item = st.session_state.red_item
                    st.error(f"🔴 **红方抽到：[{item.get('name', '道具')}]**（{item.get('desc', '')}）")
                    st.caption(f"{item.get('effect_detail', '⚡ 效果已生效')}")

            st.divider()

            # 3. 结算与模拟
            blue_score_bonus = 0
            red_score_bonus = 0
            logs = []

            if "blue_item" in st.session_state and st.session_state.blue_drawn:
                eff = st.session_state.blue_item.get("effect", "")
                if eff == "self_add_10":
                    blue_score_bonus += 10
                elif eff == "self_sub_10":
                    blue_score_bonus -= 10
                elif eff == "self_add_20":
                    blue_score_bonus += 20
                elif eff == "self_sub_20":
                    blue_score_bonus -= 20
                elif eff == "opp_sub_20":
                    red_score_bonus -= 20
                    logs.append("🗣️ 蓝方使用了 [嘴 - 喷垃圾话]，红方最终得分 -20！")
                elif eff == "ankle_breaker":
                    top_red = max(calc_red_team, key=lambda p: p.rating)
                    old_r = top_red.rating
                    top_red.rating = 80
                    logs.append(f"🦶 蓝方使用了 [脚 - 垫脚]！红方最高能力值球员 **{top_red.name}** 能力值从 {old_r} 降至 **80**！")

            if "red_item" in st.session_state and st.session_state.red_drawn:
                eff = st.session_state.red_item.get("effect", "")
                if eff == "self_add_10":
                    red_score_bonus += 10
                elif eff == "self_sub_10":
                    red_score_bonus -= 10
                elif eff == "self_add_20":
                    red_score_bonus += 20
                elif eff == "self_sub_20":
                    red_score_bonus -= 20
                elif eff == "opp_sub_20":
                    blue_score_bonus -= 20
                    logs.append("🗣️ 红方使用了 [嘴 - 喷垃圾话]，蓝方最终得分 -20！")
                elif eff == "ankle_breaker":
                    top_blue = max(calc_blue_team, key=lambda p: p.rating)
                    old_r = top_blue.rating
                    top_blue.rating = 80
                    logs.append(f"🦶 红方使用了 [脚 - 垫脚]！蓝方最高能力值球员 **{top_blue.name}** 能力值从 {old_r} 降至 **80**！")

            if logs:
                st.warning("⚠️ **赛前特殊事件生效：**\n\n" + "\n\n".join(logs))

            blue_base_score = sum(p.rating for p in calc_blue_team)
            red_base_score = sum(p.rating for p in calc_red_team)

            if st.button("🚀 开启模拟对决！", type="primary"):
                blue_luck = random.uniform(0.88, 1.12)
                red_luck = random.uniform(0.88, 1.12)
                
                blue_final_score = int(blue_base_score * blue_luck) + blue_score_bonus
                red_final_score = int(red_base_score * red_luck) + red_score_bonus

                st.subheader("📊 比赛最终比分")
                res_col1, res_col2 = st.columns(2)
                res_col1.metric("🔵 蓝方得分", blue_final_score, delta=f"手感修正: {blue_luck*100:.1f}% | 道具修正: {blue_score_bonus:+d}")
                res_col2.metric("🔴 红方得分", red_final_score, delta=f"手感修正: {red_luck*100:.1f}% | 道具修正: {red_score_bonus:+d}")

                if blue_final_score > red_final_score:
                    st.balloons()
                    st.success(f"🏆 恭喜！🔵 蓝方以 **{blue_final_score} : {red_final_score}** 赢得了这场 5v5 斗牛赛！")
                elif blue_final_score < red_final_score:
                    st.balloons()
                    st.error(f"🏆 恭喜！🔴 红方以 **{red_final_score} : {blue_final_score}** 赢得了这场 5v5 斗牛赛！")
                else:
                    st.warning(f"🤝 双方手感平平，以 **{blue_final_score} : {red_final_score}** 打成平手！")
        else:
            if battle_mode == "🎯 自选阵容 5v5":
                st.warning("💡 请在左右两侧各选满 5 名球员以启动比赛模拟！")
            elif battle_mode == "💰 资金竞拍 5v5":
                st.info("💡 竞拍还在进行中，当双方都组满 5 名球员后将自动开启比赛对决！")

# ----------------- 7. 数据保存 -----------------
elif menu == "💾 数据保存":
    st.header("💾 数据保存")
    st.write("点击下方按钮把当前网页中的修改保存回文件中：")
    if st.button("💾 保存数据", type="primary"):
        untils.save_players(players)
        st.success("数据已成功保存到本地 players.txt！")
