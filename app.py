import streamlit as st
import random
import utils
from player import Player

# 页面基础配置
st.set_page_config(page_title="NBA 球员管理系统", page_icon="🏀", layout="wide")

# ----------------- 模式切换与数据初始化 -----------------
# 初始化模式状态，默认“现役”
if "player_mode" not in st.session_state:
    st.session_state.player_mode = "现役"

# 侧边栏添加切换按钮
st.sidebar.markdown("### 🔄 球员库模式")
col_m1, col_m2 = st.sidebar.columns(2)

with col_m1:
    if st.button("🏀 现役球员", type="primary" if st.session_state.player_mode == "现役" else "secondary", use_container_width=True):
        if st.session_state.player_mode != "现役":
            st.session_state.player_mode = "现役"
            utils.FILENAME = "players.txt" if hasattr(utils, "FILENAME") else "players.txt"
            st.session_state.players = utils.load_players()
            st.session_state.pop("auction_inited", None)
            st.session_state.pop("blue_blind", None)
            st.session_state.pop("red_blind", None)
            st.rerun()

with col_m2:
    if st.button("🌟 Alltime球员", type="primary" if st.session_state.player_mode == "Alltime" else "secondary", use_container_width=True):
        if st.session_state.player_mode != "Alltime":
            st.session_state.player_mode = "Alltime"
            try:
                players_list = []
                with open("alltimeplayers.txt", "r", encoding="utf-8") as f:
                    for line in f:
                        name, age, team, rating, position = line.strip().split(",")
                        player = Player(name, int(age), team, int(rating), position)
                        players_list.append(player)
                st.session_state.players = players_list
            except Exception as e:
                st.error(f"加载 alltimeplayers.txt 失败: {e}")
            
            st.session_state.pop("auction_inited", None)
            st.session_state.pop("blue_blind", None)
            st.session_state.pop("red_blind", None)
            st.rerun()

# 初始化数据到 Session State
if "players" not in st.session_state:
    if st.session_state.player_mode == "Alltime":
        if hasattr(utils, "FILENAME"):
            utils.FILENAME = "alltimeplayers.txt"
        st.session_state.players = utils.load_players()
    else:
        st.session_state.players = utils.load_players()

players = st.session_state.players

# 标题显示当前模式
st.title(f"🏀 NBA 球员交易与管理系统 ({'🌟 Alltime传奇库' if st.session_state.player_mode == 'Alltime' else '⚡ 现役库'})")

# 位置定义与偏离惩罚计算辅助函数
POSITIONS = ["控卫", "分卫", "小前", "大前", "中锋"]

def calculate_position_penalty(player, slot_pos):
    """计算球员放入特定槽位时的惩罚得分"""
    player_pos = getattr(player, "position", "未知")
    if player_pos not in POSITIONS:
        return 0, "位置未知，无惩罚"
    
    player_idx = POSITIONS.index(player_pos)
    slot_idx = POSITIONS.index(slot_pos)
    diff = abs(player_idx - slot_idx)
    
    penalty = diff * 2
    if diff == 0:
        note = "✅ 契合原位置"
    else:
        note = f"⚠️ 不在原位置 (原: {player_pos})，偏离 {diff} 个位置，扣 {penalty} 分"
    
    return penalty, note

# 辅助函数：转换为字典列表
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
        "👑 最强球队",
        "🏆 黄金季后赛",
        "💰 资本家之战",
        "💾 数据保存"
    ]
)

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
            
            position = st.selectbox("球员位置：", POSITIONS)
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
            p_found = utils.find_player(players, del_name)
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
        p_target = utils.find_player(players, mod_name) if mod_name else None
        
        if p_target:
            curr_pos = getattr(p_target, "position", "未知")
            st.info(f"当前球员：**{p_target.name}** | 位置：**{curr_pos}** | 当前能力值：**{p_target.rating}**")
            
            col_mod1, col_mod2 = st.columns(2)
            with col_mod1:
                action = st.radio("修改能力值：", ["增加能力值", "减少能力值"])
                amount = st.number_input("调整数值：", min_value=1, max_value=50, value=1)
            with col_mod2:
                default_idx = POSITIONS.index(curr_pos) if curr_pos in POSITIONS else 0
                new_pos = st.selectbox("更新位置（可选）：", POSITIONS, index=default_idx)

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
        if st.button("开始抽取"):
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
                st.success(f"🔥 抽中优质球员：**{chosen.name}** | 位置：[{pos}] | 球队：{chosen.team} | 能力值：**{chosen.rating}**")
            else:
                st.warning("⚠️ 当前没有能力值 $\ge$ 80 的球员！")
    elif sub_option == "按队伍后缀排序":
        players.sort(key=lambda p: p.team.split()[-1])
        st.dataframe(players_to_dict_list(players), use_container_width=True)

# ----------------- 6. 🏀 5v5 斗牛对决 -----------------
elif menu == "🏀 5v5 斗牛对决":
    st.header("🏀 5v5 阵容斗牛模拟器")
    st.caption("按位置框架组建阵容（控卫 -> 分卫 -> 小前 -> 大前 -> 中锋），偏离原位置每级扣 2 分")

    if len(players) < 10:
        st.error("⚠️ 球员总数不足 10 人，无法开启 5v5 斗牛，请先添加更多球员！")
    else:
        battle_mode = st.radio("选择斗牛模式：", ["🔥 盲盒抽卡 5v5", "🎯 自选阵容 5v5", "💰 资金竞拍 5v5"], horizontal=True)
        player_dict = {f"{p.name} [{getattr(p, 'position', '未知')}] ({p.team} - {p.rating}分)": p for p in players}

        def reset_match_state():
            st.session_state.pop("blue_item", None)
            st.session_state.pop("red_item", None)
            st.session_state.blue_drawn = False
            st.session_state.red_drawn = False

        calc_blue_team = []
        calc_red_team = []

        # ================= 模式 1：🔥 盲盒抽卡 5v5 =================
        if battle_mode == "🔥 盲盒抽卡 5v5":
            st.subheader("🎲 严格位置盲盒抽卡")
            st.caption("系统将从球员库中，分别针对【控卫、分卫、小前、大前、中锋】按顺序随机抽取球员")
            
            if st.button("🎲 一键随机抽取双方 5v5 阵容"):
                blue_blind = []
                red_blind = []
                for pos in POSITIONS:
                    pos_pool = [p for p in players if getattr(p, "position", "") == pos]
                    if len(pos_pool) < 2:
                        pos_pool = players
                    sampled = random.sample(pos_pool, min(2, len(pos_pool)))
                    if len(sampled) == 2:
                        blue_blind.append(sampled[0])
                        red_blind.append(sampled[1])
                    else:
                        blue_blind.append(sampled[0])
                        red_blind.append(random.choice(players))
                st.session_state.blue_blind = blue_blind
                st.session_state.red_blind = red_blind
                reset_match_state()

            if "blue_blind" in st.session_state and "red_blind" in st.session_state:
                b_list = st.session_state.blue_blind
                r_list = st.session_state.red_blind
                for i, pos in enumerate(POSITIONS):
                    bp = b_list[i]
                    pen_b, _ = calculate_position_penalty(bp, pos)
                    calc_blue_team.append(Player(bp.name, bp.age, bp.team, max(0, bp.rating - pen_b), getattr(bp, 'position', '未知')))

                    rp = r_list[i]
                    pen_r, _ = calculate_position_penalty(rp, pos)
                    calc_red_team.append(Player(rp.name, rp.age, rp.team, max(0, rp.rating - pen_r), getattr(rp, 'position', '未知')))

        # ================= 模式 2：🎯 自选阵容 5v5 =================
        elif battle_mode == "🎯 自选阵容 5v5":
            st.subheader("📋 自选球员（按位置顺序自上而下配置，球员不可重复选择）")
            col_a, col_b = st.columns(2)
            blue_selection = []
            red_selection = []

            with col_a:
                st.markdown("### 🔵 蓝方阵容配置")
                selected_blue_names = []
                for pos in POSITIONS:
                    avail_options = ["-- 请选择球员 --"] + [k for k in player_dict.keys() if k not in selected_blue_names or k == st.session_state.get(f"blue_select_{pos}")]
                    choice = st.selectbox(f"位置 [{pos}] 选择球员：", avail_options, key=f"blue_select_{pos}")
                    if choice != "-- 请选择球员 --":
                        selected_blue_names.append(choice)
                        p_obj = player_dict[choice]
                        pen, note = calculate_position_penalty(p_obj, pos)
                        st.caption(f"↳ {note}")
                        blue_selection.append((p_obj, pos, pen))

            with col_b:
                st.markdown("### 🔴 红方阵容配置")
                selected_red_names = []
                for pos in POSITIONS:
                    avail_options = ["-- 请选择球员 --"] + [k for k in player_dict.keys() if k not in selected_red_names or k == st.session_state.get(f"red_select_{pos}")]
                    choice = st.selectbox(f"位置 [{pos}] 选择球员：", avail_options, key=f"red_select_{pos}")
                    if choice != "-- 请选择球员 --":
                        selected_red_names.append(choice)
                        p_obj = player_dict[choice]
                        pen, note = calculate_position_penalty(p_obj, pos)
                        st.caption(f"↳ {note}")
                        red_selection.append((p_obj, pos, pen))

            if len(blue_selection) == 5 and len(red_selection) == 5:
                for p_obj, pos, pen in blue_selection:
                    calc_blue_team.append(Player(p_obj.name, p_obj.age, p_obj.team, max(0, p_obj.rating - pen), getattr(p_obj, 'position', '未知')))
                for p_obj, pos, pen in red_selection:
                    calc_red_team.append(Player(p_obj.name, p_obj.age, p_obj.team, max(0, p_obj.rating - pen), getattr(p_obj, 'position', '未知')))
            else:
                reset_match_state()

        # ================= 模式 3：💰 资金竞拍 5v5 =================
        elif battle_mode == "💰 资金竞拍 5v5":
            st.subheader("🔨 回合制拍卖大厅")
            st.caption("规则：手牌达到 5 张即定格！若资金为 $0 或对方手牌已满，可免费 $0 抽牌补齐手牌。")

            if "auction_inited" not in st.session_state or not st.session_state.auction_inited:
                st.session_state.blue_money = 20
                st.session_state.red_money = 20
                st.session_state.auction_blue_pool = []
                st.session_state.auction_red_pool = []
                st.session_state.current_target_player = None
                st.session_state.auction_logs = []
                st.session_state.current_bid = 0
                st.session_state.highest_bidder = None
                st.session_state.drawer = "blue"
                st.session_state.turn = "blue"
                st.session_state.auction_inited = True

            if st.button("🔄 重置/重新开始拍卖"):
                st.session_state.auction_inited = False
                reset_match_state()
                st.rerun()

            auc_blue_pool = st.session_state.auction_blue_pool
            auc_red_pool = st.session_state.auction_red_pool

            col_m1, col_m2 = st.columns(2)
            blue_full = len(auc_blue_pool) >= 5
            red_full = len(auc_red_pool) >= 5
            
            col_m1.metric("🔵 蓝方资金", f"${st.session_state.blue_money}", delta=f"手牌: {len(auc_blue_pool)}/5 {'(已满)' if blue_full else ''}")
            col_m2.metric("🔴 红方资金", f"${st.session_state.red_money}", delta=f"手牌: {len(auc_red_pool)}/5 {'(已满)' if red_full else ''}")

            st.markdown("#### 📋 双方手牌清单")
            list_col1, list_col2 = st.columns(2)
            with list_col1:
                if auc_blue_pool:
                    blue_list_str = "\n".join([f"* **{p.name}** [{getattr(p, 'position', '未知')}] (能力值: {p.rating})" for p in auc_blue_pool])
                    st.markdown(f"**🔵 蓝方手牌 ({len(auc_blue_pool)}/5):**\n" + blue_list_str)
                else:
                    st.caption("🔵 蓝方暂无拍得球员")

            with list_col2:
                if auc_red_pool:
                    red_list_str = "\n".join([f"* **{p.name}** [{getattr(p, 'position', '未知')}] (能力值: {p.rating})" for p in auc_red_pool])
                    st.markdown(f"**🔴 红方手牌 ({len(auc_red_pool)}/5):**\n" + red_list_str)
                else:
                    st.caption("🔴 红方暂无拍得球员")
            st.divider()

            if not (blue_full and red_full):
                used_players = set(auc_blue_pool + auc_red_pool)
                available_pool = [p for p in players if p not in used_players]
                high_rating_pool = [p for p in available_pool if p.rating >= 80]
                if not high_rating_pool:
                    high_rating_pool = available_pool

                current_drawer = st.session_state.drawer
                if current_drawer == "blue" and blue_full:
                    current_drawer = "red"
                elif current_drawer == "red" and red_full:
                    current_drawer = "blue"

                st.session_state.drawer = current_drawer
                drawer_text = "🔵 蓝方" if current_drawer == "blue" else "🔴 红方"
                other_side = "red" if current_drawer == "blue" else "blue"
                other_full = red_full if current_drawer == "blue" else blue_full
                drawer_money = st.session_state.blue_money if current_drawer == "blue" else st.session_state.red_money

                if not st.session_state.current_target_player:
                    is_free_draw = (drawer_money <= 0) or other_full
                    if is_free_draw:
                        reason = "(资金为 $0)" if drawer_money <= 0 else "(对方已满 5 张)"
                        btn_label = f"🎲 {drawer_text} $0 免费抽取球员 {reason}"
                        st.markdown(f"### 🎲 轮到 **{drawer_text}** 抽牌 {reason}：")
                    else:
                        btn_label = f"🎲 {drawer_text} 抽取并支付 $1 起拍"
                        st.markdown(f"### 🎲 轮到 **{drawer_text}** 抽牌：")
                    
                    if st.button(btn_label):
                        target = random.choice(high_rating_pool)
                        if is_free_draw:
                            if current_drawer == "blue":
                                st.session_state.auction_blue_pool.append(target)
                            else:
                                st.session_state.auction_red_pool.append(target)
                            st.session_state.auction_logs.append(f"{drawer_text} {reason} 以 **$0** 获得 **{target.name}**")
                            st.session_state.current_target_player = None
                            st.session_state.drawer = other_side
                        else:
                            st.session_state.current_target_player = target
                            st.session_state.current_bid = 1
                            st.session_state.highest_bidder = current_drawer
                            st.session_state.turn = other_side
                        st.rerun()

                target = st.session_state.current_target_player
                if target:
                    pos = getattr(target, "position", "未知")
                    high_bidder_text = "🔵 蓝方" if st.session_state.highest_bidder == "blue" else "🔴 红方"
                    st.info(f"🌟 **当前竞拍球员：** **{target.name}** （原位置：[{pos}] | 能力值：**{target.rating}**）")
                    st.write(f"当前最高出价：**${st.session_state.current_bid}**（保持者：**{high_bidder_text}**）")

                    turn = st.session_state.turn
                    turn_text = "🔵 蓝方" if turn == "blue" else "🔴 红方"
                    st.markdown(f"### 📢 轮到 **{turn_text}** 应价：")

                    curr_money = st.session_state.blue_money if turn == "blue" else st.session_state.red_money
                    min_bid = st.session_state.current_bid + 1

                    c_act1, c_act2 = st.columns(2)
                    with c_act1:
                        can_bid = (curr_money >= min_bid)
                        bid_val = st.number_input(
                            f"{turn_text} 提高应价 ($)",
                            min_value=min_bid,
                            max_value=max(min_bid, curr_money),
                            value=min_bid,
                            step=1,
                            key="turn_bid_input",
                            disabled=not can_bid
                        )
                        if st.button(f"🔨 {turn_text} 确认加价应价 (${bid_val})", disabled=not can_bid):
                            st.session_state.current_bid = bid_val
                            st.session_state.highest_bidder = turn
                            other = "red" if turn == "blue" else "blue"
                            other_team_len = len(st.session_state.auction_red_pool) if other == "red" else len(st.session_state.auction_blue_pool)
                            if other_team_len < 5:
                                st.session_state.turn = other
                            else:
                                winner = turn
                                cost = bid_val
                                if winner == "blue":
                                    st.session_state.blue_money = max(0, st.session_state.blue_money - cost)
                                    st.session_state.auction_blue_pool.append(target)
                                else:
                                    st.session_state.red_money = max(0, st.session_state.red_money - cost)
                                    st.session_state.auction_red_pool.append(target)
                                w_text = "🔵 蓝方" if winner == "blue" else "🔴 红方"
                                st.session_state.auction_logs.append(f"{w_text} 以 **${cost}** 拍得 **{target.name}** [{pos}] ({target.rating}分)")
                                st.session_state.drawer = "red" if st.session_state.drawer == "blue" else "blue"
                                st.session_state.current_target_player = None
                            st.rerun()

                    with c_act2:
                        if st.button(f"🏳️ {turn_text} 放弃应价 (Pass)"):
                            winner = st.session_state.highest_bidder
                            cost = st.session_state.current_bid
                            if winner == "blue":
                                st.session_state.blue_money = max(0, st.session_state.blue_money - cost)
                                st.session_state.auction_blue_pool.append(target)
                            else:
                                st.session_state.red_money = max(0, st.session_state.red_money - cost)
                                st.session_state.auction_red_pool.append(target)
                            w_text = "🔵 蓝方" if winner == "blue" else "🔴 红方"
                            st.session_state.auction_logs.append(f"{w_text} 以 **${cost}** 拍得 **{target.name}** [{pos}] ({target.rating}分)")
                            st.session_state.drawer = "red" if st.session_state.drawer == "blue" else "blue"
                            st.session_state.current_target_player = None
                            reset_match_state()
                            st.rerun()

            if len(auc_blue_pool) >= 5 and len(auc_red_pool) >= 5:
                st.divider()
                st.subheader("🧩 拍卖结束：请将已拍得球员放入阵容位置框架中")
                col_slot1, col_slot2 = st.columns(2)
                b_assigned = []
                r_assigned = []

                with col_slot1:
                    st.markdown("### 🔵 蓝方阵容指派")
                    b_dict = {f"{p.name} [{getattr(p, 'position', '未知')}] ({p.rating}分)": p for p in auc_blue_pool}
                    selected_b_auc_names = []
                    for pos in POSITIONS:
                        avail_b = ["-- 请选择 --"] + [k for k in b_dict.keys() if k not in selected_b_auc_names or k == st.session_state.get(f"auc_b_slot_{pos}")]
                        c_sel = st.selectbox(f"蓝方 [{pos}] 选派：", avail_b, key=f"auc_b_slot_{pos}")
                        if c_sel != "-- 请选择 --":
                            selected_b_auc_names.append(c_sel)
                            p_obj = b_dict[c_sel]
                            pen, note = calculate_position_penalty(p_obj, pos)
                            st.caption(f"↳ {note}")
                            b_assigned.append((p_obj, pos, pen))

                with col_slot2:
                    st.markdown("### 🔴 红方阵容指派")
                    r_dict = {f"{p.name} [{getattr(p, 'position', '未知')}] ({p.rating}分)": p for p in auc_red_pool}
                    selected_r_auc_names = []
                    for pos in POSITIONS:
                        avail_r = ["-- 请选择 --"] + [k for k in r_dict.keys() if k not in selected_r_auc_names or k == st.session_state.get(f"auc_r_slot_{pos}")]
                        c_sel = st.selectbox(f"红方 [{pos}] 选派：", avail_r, key=f"auc_r_slot_{pos}")
                        if c_sel != "-- 请选择 --":
                            selected_r_auc_names.append(c_sel)
                            p_obj = r_dict[c_sel]
                            pen, note = calculate_position_penalty(p_obj, pos)
                            st.caption(f"↳ {note}")
                            r_assigned.append((p_obj, pos, pen))

                if len(b_assigned) == 5 and len(r_assigned) == 5:
                    for p_obj, pos, pen in b_assigned:
                        calc_blue_team.append(Player(p_obj.name, p_obj.age, p_obj.team, max(0, p_obj.rating - pen), getattr(p_obj, 'position', '未知')))
                    for p_obj, pos, pen in r_assigned:
                        calc_red_team.append(Player(p_obj.name, p_obj.age, p_obj.team, max(0, p_obj.rating - pen), getattr(p_obj, 'position', '未知')))

        # ----------------- 比赛流程与道具结算 -----------------
        if len(calc_blue_team) == 5 and len(calc_red_team) == 5:
            st.divider()

            if "blue_drawn" not in st.session_state:
                st.session_state.blue_drawn = False
            if "red_drawn" not in st.session_state:
                st.session_state.red_drawn = False

            items_pool = [
                {"name": "🧪 佳得乐", "desc": "佳得乐补充体力", "effect_detail": "⚡ 效果：队伍总战力 +10", "effect": "self_add_10"},
                {"name": "🎮 游戏机", "desc": "昨晚打游戏", "effect_detail": "💤 效果：队伍总战力 -10", "effect": "self_sub_10"},
                {"name": "👁️ 红色的眼睛", "desc": "全员觉醒", "effect_detail": "🔥 效果：队伍总战力 +20", "effect": "self_add_20"},
                {"name": "🍾 酒瓶", "desc": "昨晚夜店喝酒", "effect_detail": "😵 效果：队伍总战力 -20", "effect": "self_sub_20"},
                {"name": "👄 嘴", "desc": "喷垃圾话", "effect_detail": "💢 效果：对方队伍总战力 -20", "effect": "opp_sub_20"},
                {"name": "🦶 脚", "desc": "垫脚", "effect_detail": "🚑 效果：对方评分最高的球员能力值降为 80", "effect": "ankle_breaker"},
                {"name": "🚽 教练上厕所", "desc": "教练不在场", "effect_detail": "🔀 效果：己方随机两位球员的位置互换，并重新扣除偏离分数", "effect": "swap_positions"}
            ]

            st.subheader("🎁 赛前随机抽取道具事件（每局限抽一次）")
            col_item1, col_item2 = st.columns(2)

            with col_item1:
                btn_blue = st.button("🎲 蓝方抽取赛前道具", disabled=st.session_state.blue_drawn, key="btn_blue_draw")
                if btn_blue:
                    avail_blue_pool = items_pool
                    if "red_item" in st.session_state and st.session_state.red_item:
                        avail_blue_pool = [item for item in items_pool if item["name"] != st.session_state.red_item["name"]]
                    st.session_state.blue_item = random.choice(avail_blue_pool)
                    st.session_state.blue_drawn = True
                    st.rerun()

                if "blue_item" in st.session_state and st.session_state.blue_drawn:
                    item = st.session_state.blue_item
                    st.info(f"🔵 **蓝方抽到：[{item.get('name', '道具')}]**（{item.get('desc', '')}）")
                    st.caption(f"{item.get('effect_detail', '⚡ 效果已生效')}")

            with col_item2:
                btn_red = st.button("🎲 红方抽取赛前道具", disabled=st.session_state.red_drawn, key="btn_red_draw")
                if btn_red:
                    avail_red_pool = items_pool
                    if "blue_item" in st.session_state and st.session_state.blue_item:
                        avail_red_pool = [item for item in items_pool if item["name"] != st.session_state.blue_item["name"]]
                    st.session_state.red_item = random.choice(avail_red_pool)
                    st.session_state.red_drawn = True
                    st.rerun()

                if "red_item" in st.session_state and st.session_state.red_drawn:
                    item = st.session_state.red_item
                    st.error(f"🔴 **红方抽到：[{item.get('name', '道具')}]**（{item.get('desc', '')}）")
                    st.caption(f"{item.get('effect_detail', '⚡ 效果已生效')}")

            st.divider()

            blue_power_bonus = 0
            red_power_bonus = 0
            logs = []

            if "blue_item" in st.session_state and st.session_state.blue_drawn:
                eff = st.session_state.blue_item.get("effect", "")
                if eff == "self_add_10":
                    blue_power_bonus += 10
                elif eff == "self_sub_10":
                    blue_power_bonus -= 10
                elif eff == "self_add_20":
                    blue_power_bonus += 20
                elif eff == "self_sub_20":
                    blue_power_bonus -= 20
                elif eff == "opp_sub_20":
                    red_power_bonus -= 20
                    logs.append("🗣️ 蓝方使用了 [嘴 - 喷垃圾话]，红方队伍总战力 -20")
                elif eff == "ankle_breaker":
                    top_red = max(calc_red_team, key=lambda p: p.rating)
                    if top_red.rating > 80:
                        old_r = top_red.rating
                        top_red.rating = 80
                        logs.append(f"🦶 蓝方使用了 [脚 - 垫脚]，红方评分最高的球员 **{top_red.name}** 能力值从 {old_r} 降至 **80**")
                elif eff == "swap_positions":
                    idx1, idx2 = random.sample(range(5), 2)
                    pos1, pos2 = POSITIONS[idx1], POSITIONS[idx2]
                    p1_old = calc_blue_team[idx1]
                    p2_old = calc_blue_team[idx2]
                    calc_blue_team[idx1], calc_blue_team[idx2] = p2_old, p1_old
                    pen1, _ = calculate_position_penalty(calc_blue_team[idx1], pos1)
                    pen2, _ = calculate_position_penalty(calc_blue_team[idx2], pos2)
                    orig_r1 = getattr(calc_blue_team[idx1], "raw_rating", calc_blue_team[idx1].rating)
                    orig_r2 = getattr(calc_blue_team[idx2], "raw_rating", calc_blue_team[idx2].rating)
                    calc_blue_team[idx1].rating = max(0, orig_r1 - pen1)
                    calc_blue_team[idx2].rating = max(0, orig_r2 - pen2)
                    logs.append(f"🚽 蓝方触发了 [教练上厕所]！阵型混乱，【{pos1} - {calc_blue_team[idx1].name}】与【{pos2} - {calc_blue_team[idx2].name}】互换了位置，并重新计算了位置扣分！")

            if "red_item" in st.session_state and st.session_state.red_drawn:
                eff = st.session_state.red_item.get("effect", "")
                if eff == "self_add_10":
                    red_power_bonus += 10
                elif eff == "self_sub_10":
                    red_power_bonus -= 10
                elif eff == "self_add_20":
                    red_power_bonus += 20
                elif eff == "self_sub_20":
                    red_power_bonus -= 20
                elif eff == "opp_sub_20":
                    blue_power_bonus -= 20
                    logs.append("🗣️ 红方使用了 [嘴 - 喷垃圾话]，蓝方队伍总战力 -20")
                elif eff == "ankle_breaker":
                    top_blue = max(calc_blue_team, key=lambda p: p.rating)
                    if top_blue.rating > 80:
                        old_r = top_blue.rating
                        top_blue.rating = 80
                        logs.append(f"🦶 红方使用了 [脚 - 垫脚]，蓝方评分最高的球员 **{top_blue.name}** 能力值从 {old_r} 降至 **80**")
                elif eff == "swap_positions":
                    idx1, idx2 = random.sample(range(5), 2)
                    pos1, pos2 = POSITIONS[idx1], POSITIONS[idx2]
                    p1_old = calc_red_team[idx1]
                    p2_old = calc_red_team[idx2]
                    calc_red_team[idx1], calc_red_team[idx2] = p2_old, p1_old
                    pen1, _ = calculate_position_penalty(calc_red_team[idx1], pos1)
                    pen2, _ = calculate_position_penalty(calc_red_team[idx2], pos2)
                    orig_r1 = getattr(calc_red_team[idx1], "raw_rating", calc_red_team[idx1].rating)
                    orig_r2 = getattr(calc_red_team[idx2], "raw_rating", calc_red_team[idx2].rating)
                    calc_red_team[idx1].rating = max(0, orig_r1 - pen1)
                    calc_red_team[idx2].rating = max(0, orig_r2 - pen2)
                    logs.append(f"🚽 红方触发了 [教练上厕所]！阵型混乱，【{pos1} - {calc_red_team[idx1].name}】与【{pos2} - {calc_red_team[idx2].name}】互换了位置，并重新计算了位置扣分！")

            if logs:
                st.warning("⚠️ **赛前特殊事件生效：**\n\n" + "\n\n".join(logs))

            c1, c2 = st.columns(2)
            with c1:
                st.subheader("🔵 蓝方首发五虎（包含位置折损与道具影响）")
                st.dataframe(players_to_dict_list(calc_blue_team), use_container_width=True)
                blue_base_score = max(10, sum(p.rating for p in calc_blue_team) + blue_power_bonus)
                if blue_power_bonus != 0:
                    st.caption(f"🎁 道具战力修正：{'+' if blue_power_bonus > 0 else ''}{blue_power_bonus}")
                st.info(f"修正后总战力：**{blue_base_score}** | 场上均分：**{blue_base_score/5:.1f}**")

            with c2:
                st.subheader("🔴 红方首发五虎（包含位置折损与道具影响）")
                st.dataframe(players_to_dict_list(calc_red_team), use_container_width=True)
                red_base_score = max(10, sum(p.rating for p in calc_red_team) + red_power_bonus)
                if red_power_bonus != 0:
                    st.caption(f"🎁 道具战力修正：{'+' if red_power_bonus > 0 else ''}{red_power_bonus}")
                st.info(f"修正后总战力：**{red_base_score}** | 场上均分：**{red_base_score/5:.1f}**")

            st.divider()

            if st.button("🚀 开启模拟对决！", type="primary"):
                blue_luck = random.uniform(0.88, 1.12)
                red_luck = random.uniform(0.88, 1.12)
                
                raw_blue_score = int(blue_base_score * blue_luck)
                raw_red_score = int(red_base_score * red_luck)

                raw_blue_score = max(10, raw_blue_score)
                raw_red_score = max(10, raw_red_score)

                game_base_total = random.randint(195, 225)
                real_blue_score = round(game_base_total * (raw_blue_score / (raw_blue_score + raw_red_score)))
                real_red_score = game_base_total - real_blue_score

                if real_blue_score == real_red_score:
                    if raw_blue_score > raw_red_score:
                        real_blue_score += random.choice([2, 3])
                    elif raw_red_score > raw_blue_score:
                        real_red_score += random.choice([2, 3])
                    else:
                        real_blue_score += random.choice([1, 2])

                st.subheader("📊 比赛最终比分")
                res_col1, res_col2 = st.columns(2)
                res_col1.metric("🔵 蓝方赛场最终得分", f"{real_blue_score} 分", delta=f"手感: {blue_luck:.0%} | 战力折算: {raw_blue_score}")
                res_col2.metric("🔴 红方赛场最终得分", f"{real_red_score} 分", delta=f"手感: {red_luck:.0%} | 战力折算: {raw_red_score}")

                st.caption(f"💡 赛场真实比分由双方包含道具战力修正与手感波动的总战力（蓝 {raw_blue_score} vs 红 {raw_red_score}）等比例映射缩放得出。")

                winner_team_name = ""
                winning_players_list = []
                
                if real_blue_score > real_red_score:
                    winner_team_name = "🔵 蓝方"
                    winning_players_list = calc_blue_team
                    st.balloons()
                    st.success(f"🏆 恭喜！🔵 蓝方以 **{real_blue_score} : {real_red_score}** 赢得了这场 5v5 斗牛赛！")
                elif real_blue_score < real_red_score:
                    winner_team_name = "🔴 红方"
                    winning_players_list = calc_red_team
                    st.balloons()
                    st.error(f"🏆 恭喜！🔴 红方以 **{real_red_score} : {real_blue_score}** 赢得了这场 5v5 斗牛赛！")
                else:
                    winner_team_name = "双方"
                    winning_players_list = calc_blue_team + calc_red_team
                    st.info(f"🤝 双方战平！")

                # ================= 🏆 评选本场 MVP =================
                if winning_players_list:
                    st.divider()
                    st.subheader("🌟 本场比赛 MVP 评选")
                    mvp_weights = [max(1, p.rating - 60) for p in winning_players_list]
                    mvp_player = random.choices(winning_players_list, weights=mvp_weights, k=1)[0]
                    mvp_pos = getattr(mvp_player, "position", "未知")
                    
                    st.markdown(
                        f"""
                        <div style="padding: 15px; border-radius: 10px; background-color: #f0f2f6; border-left: 5px solid #ff4b4b;">
                            <h4>🔥 <b>{winner_team_name}</b> 斩获本场 MVP 的球员是：</h4>
                            <p style="font-size: 1.2em; margin: 5px 0;"><b>{mvp_player.name}</b> [{mvp_pos}] | 球队：{mvp_player.team}</p>
                            <p style="color: #555; margin: 0;">场上有效评分：<b>{mvp_player.rating}</b> 分（MVP 评选加权评分）</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.info("💡 请将 5 个位置槽位全部选满，自动汇总计算位置折损并生成对战")

# ----------------- 7. 👑 终极王朝车轮战 -----------------
elif menu == "👑 最强球队":
    col_t_dyn, col_btn_dyn = st.columns([4, 1])
    with col_t_dyn:
        st.header("👑 终极王朝车轮战 (3败即止)")
    with col_btn_dyn:
        st.write("")
        if st.button("🔄 重新开始", key="restart_dynasty"):
            st.session_state.dynasty_active = False
            st.session_state.dynasty_match_finished = False
            st.session_state.dynasty_last_result = None
            st.session_state.dynasty_venue = None
            st.session_state.popovich_summoned = False
            st.session_state.popovich_attempted = False
            for key in list(st.session_state.keys()):
                if key.startswith("dynasty_") or key.startswith("popo_") or key.startswith("current_enemy_team"):
                    del st.session_state[key]
            st.rerun()
    st.markdown("组建规则：**2位 95-99分球员**、**1位 90-94分球员**、**2位 85-89分球员**。每场比赛随机决定主客场（**主场战力 +5%**）。通过战术反应挑战召唤**波波维奇（全队战力 +10%）**！")
    if "dynasty_active" not in st.session_state:
        st.session_state.dynasty_active = False
    if "dynasty_wins" not in st.session_state:
        st.session_state.dynasty_wins = 0
    if "dynasty_losses" not in st.session_state:
        st.session_state.dynasty_losses = 0
    if "dynasty_my_team" not in st.session_state:
        st.session_state.dynasty_my_team = []
    if "dynasty_history" not in st.session_state:
        st.session_state.dynasty_history = []
    if "dynasty_item_drawn" not in st.session_state:
        st.session_state.dynasty_item_drawn = False
    if "dynasty_my_item" not in st.session_state:
        st.session_state.dynasty_my_item = None
    if "dynasty_enemy_item" not in st.session_state:
        st.session_state.dynasty_enemy_item = None
    if "dynasty_match_finished" not in st.session_state:
        st.session_state.dynasty_match_finished = False
    if "dynasty_last_result" not in st.session_state:
        st.session_state.dynasty_last_result = None
    if "dynasty_venue" not in st.session_state:
        st.session_state.dynasty_venue = None
    if "popovich_summoned" not in st.session_state:
        st.session_state.popovich_summoned = False
    if "popovich_attempted" not in st.session_state:
        st.session_state.popovich_attempted = False

    # 1. 配置阵容阶段
    if not st.session_state.dynasty_active:
        st.subheader("🛠️ 第一步：按分段要求挑选 5 位王朝球员")

        pool_95_99 = {f"{p.name} [{getattr(p, 'position', '未知')}] ({p.team} - {p.rating}分)": p for p in players if 95 <= p.rating <= 99}
        pool_90_94 = {f"{p.name} [{getattr(p, 'position', '未知')}] ({p.team} - {p.rating}分)": p for p in players if 90 <= p.rating <= 94}
        pool_85_89 = {f"{p.name} [{getattr(p, 'position', '未知')}] ({p.team} - {p.rating}分)": p for p in players if 85 <= p.rating <= 89}

        col_tier1, col_tier2, col_tier3 = st.columns(3)

        with col_tier1:
            st.markdown("### 🌟 95-99分 (需选 2 位)")
            sel_t1_keys = st.multiselect("选择 95-99 巨星", options=list(pool_95_99.keys()), max_selections=2, key="dynasty_t1")

        with col_tier2:
            st.markdown("### 🔥 90-94分 (需选 1 位)")
            sel_t2_keys = st.multiselect("选择 90-94 全明星", options=list(pool_90_94.keys()), max_selections=1, key="dynasty_t2")

        with col_tier3:
            st.markdown("### ⚡ 85-89分 (需选 2 位)")
            sel_t3_keys = st.multiselect("选择 85-89 悍将", options=list(pool_85_89.keys()), max_selections=2, key="dynasty_t3")

        selected_raw_players = [pool_95_99[k] for k in sel_t1_keys] + \
                               [pool_90_94[k] for k in sel_t2_keys] + \
                               [pool_85_89[k] for k in sel_t3_keys]

        st.divider()
        st.subheader("🛠️ 第二步：将已选的 5 位球员指派到位置框架中（计算位置偏离）")
        st.caption("💡 防重复指派机制：每个位置必须指派不同的已选球员，且 5 个位置必须全部分配完毕。")

        dynasty_selection = []
        if len(selected_raw_players) == 5:
            chosen_dict = {f"{p.name} [{getattr(p, 'position', '未知')}] ({p.rating}分)": p for p in selected_raw_players}
            
            currently_assigned = []
            for pos in POSITIONS:
                val = st.session_state.get(f"dynasty_pos_{pos}", "-- 请选择 --")
                if val != "-- 请选择 --":
                    currently_assigned.append(val)

            col_d1, col_d2 = st.columns(2)
            for idx, pos in enumerate(POSITIONS):
                with (col_d1 if idx % 2 == 0 else col_d2):
                    current_val = st.session_state.get(f"dynasty_pos_{pos}", "-- 请选择 --")
                    avail_options = ["-- 请选择 --"] + [k for k in chosen_dict.keys() if k not in currently_assigned or k == current_val]
                    
                    if current_val not in avail_options:
                        current_val = "-- 请选择 --"
                        st.session_state[f"dynasty_pos_{pos}"] = "-- 请选择 --"

                    choice = st.selectbox(f"位置 [{pos}] 指派：", avail_options, index=avail_options.index(current_val), key=f"dynasty_pos_{pos}")
                    
                    if choice != "-- 请选择 --":
                        p_obj = chosen_dict[choice]
                        pen, note = calculate_position_penalty(p_obj, pos)
                        st.caption(f"↳ {note}")
                        dynasty_selection.append((p_obj, pos, pen))
        else:
            st.info(f"💡 请先在上方挑选齐 5 名球员（当前已选：{len(selected_raw_players)} / 5）：\n- 95-99分：{len(sel_t1_keys)}/2\n- 90-94分：{len(sel_t2_keys)}/1\n- 85-89分：{len(sel_t3_keys)}/2")

        st.divider()
        if st.button("🚀 开启终极王朝征程", type="primary"):
            final_chosen_names = [st.session_state.get(f"dynasty_pos_{pos}") for pos in POSITIONS]
            
            if len(sel_t1_keys) != 2 or len(sel_t2_keys) != 1 or len(sel_t3_keys) != 2:
                st.error("⚠️ 选人未达标！必须严格满足：2位(95-99分)、1位(90-94分)、2位(85-89分)！")
            elif any(name == "-- 请选择 --" for name in final_chosen_names):
                st.error("⚠️ 请将 5 个位置槽位全部指派完毕，不能有未分配的空位！")
            elif len(set(final_chosen_names)) < 5:
                st.error("⚠️ 不能重复使用同一名球员！每个位置必须指派不同的已选球员！")
            else:
                final_dynasty_team = []
                chosen_dict = {f"{p.name} [{getattr(p, 'position', '未知')}] ({p.rating}分)": p for p in selected_raw_players}
                for pos in POSITIONS:
                    choice_name = st.session_state.get(f"dynasty_pos_{pos}")
                    p_obj = chosen_dict[choice_name]
                    pen, _ = calculate_position_penalty(p_obj, pos)
                    final_dynasty_team.append(Player(p_obj.name, p_obj.age, p_obj.team, max(0, p_obj.rating - pen), pos))
                
                st.session_state.dynasty_my_team = final_dynasty_team
                st.session_state.dynasty_wins = 0
                st.session_state.dynasty_losses = 0
                st.session_state.dynasty_history = []
                st.session_state.dynasty_active = True
                st.session_state.dynasty_item_drawn = False
                st.session_state.dynasty_my_item = None
                st.session_state.dynasty_enemy_item = None
                st.session_state.dynasty_match_finished = False
                st.session_state.dynasty_last_result = None
                st.session_state.dynasty_venue = None
                st.session_state.popovich_summoned = False
                st.session_state.popovich_attempted = False
                st.rerun()
    
    # 2. 挑战进行中阶段
    else:
        col_w, col_l, col_r = st.columns(3)
        col_w.metric("🔥 当前连胜场次", f"{st.session_state.dynasty_wins} 连胜")
        col_l.metric("❌ 已失利场次", f"{st.session_state.dynasty_losses} / 3 场")
        
        current_match_num = st.session_state.dynasty_wins + st.session_state.dynasty_losses + 1

        if st.session_state.dynasty_venue is None or st.session_state.get("last_venue_match_num") != current_match_num:
            st.session_state.dynasty_venue = random.choice(["主场", "客场"])
            st.session_state.last_venue_match_num = current_match_num
            st.session_state.popovich_summoned = False
            st.session_state.popovich_attempted = False

        current_venue = st.session_state.dynasty_venue

        if st.session_state.dynasty_match_finished and st.session_state.dynasty_last_result:
            res = st.session_state.dynasty_last_result
            
            st.markdown("---")
            st.markdown(f"### 📊 【本场对决最终结算战报 ({res['venue']})】")
            
            st.markdown("#### 📐 双方球队战力与加成拆解：")
            breakdown_cols = st.columns(2)
            with breakdown_cols[0]:
                st.info(
                    f"**🔵 你的王朝球队数据**\n\n"
                    f"- 基础总战力：`{res['my_base_power']}`\n"
                    f"- 🏟️ 主客场修正：`{res['my_venue_str']}`\n"
                    f"- 👨‍🦳 波波维奇加成：`{res['my_popo_str']}`\n"
                    f"- 🎁 赛前手感道具：`{res['my_item_str']}`\n"
                    f"- **最终计算战力**：`{res['my_final_power']}`"
                )
            with breakdown_cols[1]:
                st.error(
                    f"**🔴 对手挑战者数据**\n\n"
                    f"- 基础总战力：`{res['enemy_base_power']}`\n"
                    f"- 🏟️ 主客场修正：`{res['enemy_venue_str']}`\n"
                    f"- 🎁 赛前道具影响：`{res['enemy_item_str']}`\n"
                    f"- **最终计算战力**：`{res['enemy_final_power']}`"
                )

            st.markdown("---")
            res_col1, res_col2 = st.columns(2)
            res_col1.metric("🔵 你的王朝队伍得分", f"{res['my_score']} 分")
            res_col2.metric("🔴 对手挑战者队伍得分", f"{res['enemy_score']} 分")

            if res["status"] == "胜利":
                st.success("🎉 本场比赛获胜！连胜延续下去！")
                st.balloons()
            else:
                st.error("💀 本场比赛遗憾失利！")

            st.info(f"🌟 **本场比赛 MVP 球员**：**{res['mvp'].name}** [位置: {getattr(res['mvp'], 'position', '未知')}]（有效战力评分: {res['mvp'].rating}）")
            st.markdown("---")

            if st.session_state.dynasty_losses >= 3:
                st.warning(f"⚠️ 挑战结束！你的终极王朝总共取得了 **{st.session_state.dynasty_wins} 场胜利**。")
                if st.button("🔄 重新开始新王朝", type="primary", key="dynasty_restart_btn"):
                    st.session_state.dynasty_active = False
                    st.session_state.dynasty_match_finished = False
                    st.session_state.dynasty_last_result = None
                    st.session_state.dynasty_venue = None
                    st.session_state.popovich_summoned = False
                    st.session_state.popovich_attempted = False
                    st.session_state.pop("current_enemy_team", None)
                    st.rerun()
            else:
                if st.button("👉 点击进入下一场比赛", type="primary", key="dynasty_next_btn"):
                    st.session_state.dynasty_item_drawn = False
                    st.session_state.dynasty_my_item = None
                    st.session_state.dynasty_enemy_item = None
                    st.session_state.dynasty_match_finished = False
                    st.session_state.dynasty_last_result = None
                    st.session_state.dynasty_venue = None
                    st.session_state.popovich_summoned = False
                    st.session_state.popovich_attempted = False
                    st.session_state.pop("current_enemy_team", None)
                    st.rerun()
                    
        else:
            if "current_enemy_team" not in st.session_state or st.session_state.get("last_match_num") != current_match_num:
                enemy_team = []
                for pos in POSITIONS:
                    pos_pool = [p for p in players if getattr(p, "position", "") == pos]
                    if not pos_pool:
                        pos_pool = players
                    enemy_team.append(random.choice(pos_pool))
                st.session_state.current_enemy_team = enemy_team
                st.session_state.last_match_num = current_match_num
                st.session_state.dynasty_item_drawn = False
                st.session_state.dynasty_my_item = None
                st.session_state.dynasty_enemy_item = None
                st.session_state.popovich_summoned = False
                st.session_state.popovich_attempted = False

            enemy_team = st.session_state.current_enemy_team

            st.divider()
            venue_badge = "🏠 你的主场作战 (+5% 战力加成)" if current_venue == "主场" else "✈️ 你的客场作战 (对手主场)"
            st.subheader(f"⚔️ 第 {current_match_num} 场大战：迎战随机挑战者 | {venue_badge}")

            st.markdown("#### 🔵 我的王朝首发阵容：")
            my_cols = st.columns(5)
            for idx, mp in enumerate(st.session_state.dynasty_my_team):
                with my_cols[idx]:
                    st.success(f"**{mp.name}**\n\n位置: {getattr(mp, 'position', '未知')}\n评分: {mp.rating}")

            st.markdown("#### 🔴 对手阵容预览：")
            cols = st.columns(5)
            for idx, ep in enumerate(enemy_team):
                with cols[idx]:
                    st.error(f"**{ep.name}**\n\n位置: {getattr(ep, 'position', '未知')}\n评分: {ep.rating}")

            st.divider()

            # ----------------- 👨‍🦳 战术微操小游戏 (区间 40~60) -----------------
            st.subheader("👨‍🦳 战术召唤：传奇教练波波维奇")
            
            if not st.session_state.popovich_attempted:
                st.markdown("🎯 **玩法规则**：战术指针正在刻度盘上自动左右摆动，看准时机，当指针进入 **40 ~ 60** 的黄金区域时，点击右侧按钮立刻锁定")

                if "popo_live_pos" not in st.session_state:
                    st.session_state.popo_live_pos = 10
                if "popo_live_dir" not in st.session_state:
                    st.session_state.popo_live_dir = 5

                pos = st.session_state.popo_live_pos + st.session_state.popo_live_dir
                if pos >= 95:
                    pos = 95
                    st.session_state.popo_live_dir = -5
                elif pos <= 5:
                    pos = 5
                    st.session_state.popo_live_dir = 5
                
                st.session_state.popo_live_pos = pos

                col_p1, col_p2 = st.columns([3, 1])
                with col_p1:
                    st.markdown(f"🎯 **当前动态指针位置：【 {pos} / 100 】** (🎯 黄金目标区: 40 ~ 60)")
                    st.progress(pos / 100.0, text=f"指针实时位置: {pos}")
                with col_p2:
                    st.write("")
                    if st.button("🔴 【🎯 点击停止】", type="primary", key="lock_live_popo_btn"):
                        st.session_state.popovich_attempted = True
                        st.session_state.popo_final_val = pos
                        if 40 <= pos <= 60:
                            st.session_state.popovich_summoned = True
                        else:
                            st.session_state.popovich_summoned = False
                        st.rerun()

                import time
                time.sleep(0.06)
                st.rerun()

            else:
                final_val = st.session_state.get("popo_final_val", 50)
                st.markdown(f"📊 **你按下瞬间定格的刻度：{final_val} / 100**")
                st.progress(final_val / 100.0, text=f"定格位置: {final_val}")

                if st.session_state.popovich_summoned:
                    st.success(f"🎉 **完美卡在黄金区间 (40~60)** **+10%**！")
                    st.balloons()
                else:
                    st.warning(f"❌ 定格在 {final_val}，未能在黄金区间！")

            st.divider()

            items_pool = [
                {"name": "🧪 佳得乐", "desc": "佳得乐补充体力", "effect_detail": "⚡ 效果：队伍总战力 +10", "effect": "self_add_10"},
                {"name": "🎮 游戏机", "desc": "昨晚打游戏", "effect_detail": "💤 效果：队伍总战力 -10", "effect": "self_sub_10"},
                {"name": "👁️ 红色的眼睛", "desc": "全员觉醒", "effect_detail": "🔥 效果：队伍总战力 +20", "effect": "self_add_20"},
                {"name": "🍾 酒瓶", "desc": "昨晚夜店喝酒", "effect_detail": "😵 效果：队伍总战力 -20", "effect": "self_sub_20"},
                {"name": "👄 嘴", "desc": "喷垃圾话", "effect_detail": "💢 效果：对方队伍总战力 -20", "effect": "opp_sub_20"},
                {"name": "🦶 脚", "desc": "垫脚", "effect_detail": "🚑 效果：对方评分最高的球员能力值降为 80", "effect": "ankle_breaker"},
                {"name": "🚽 教练上厕所", "desc": "教练不在场", "effect_detail": "🔀 效果：己方随机两位球员的位置互换", "effect": "swap_positions"}
            ]

            st.subheader("🎁 赛前道具抽取与选择")
            col_item_my, col_item_enemy = st.columns(2)

            with col_item_my:
                if not st.session_state.dynasty_item_drawn:
                    c_btn1, c_btn2 = st.columns(2)
                    with c_btn1:
                        if st.button("🎲 抽取我的道具", key="draw_my_item_btn"):
                            avail_pool = [item for item in items_pool if item["name"] != (st.session_state.dynasty_enemy_item.get("name") if st.session_state.dynasty_enemy_item else "")]
                            st.session_state.dynasty_my_item = random.choice(avail_pool)
                            st.session_state.dynasty_item_drawn = True
                            st.rerun()
                    with c_btn2:
                        if st.button("🚫 放弃使用道具", key="skip_item_btn"):
                            if not st.session_state.dynasty_enemy_item:
                                st.session_state.dynasty_enemy_item = random.choice(items_pool)
                            st.session_state.dynasty_my_item = None
                            st.session_state.dynasty_item_drawn = True
                            st.rerun()
                else:
                    if st.session_state.dynasty_my_item:
                        item = st.session_state.dynasty_my_item
                        st.info(f"🔵 **你选择的道具：[{item.get('name')}]**\n\n{item.get('effect_detail')}")
                    else:
                        st.info("🔵 **本场选择不使用道具**")

            with col_item_enemy:
                if not st.session_state.dynasty_enemy_item and st.session_state.dynasty_item_drawn:
                    avail_enemy_pool = items_pool
                    if st.session_state.dynasty_my_item:
                        avail_enemy_pool = [item for item in items_pool if item["name"] != st.session_state.dynasty_my_item["name"]]
                    st.session_state.dynasty_enemy_item = random.choice(avail_enemy_pool)

                if st.session_state.dynasty_enemy_item:
                    e_item = st.session_state.dynasty_enemy_item
                    st.error(f"🔴 **对手抽到：[{e_item.get('name')}]**\n\n{e_item.get('effect_detail')}")
                else:
                    st.caption("🔴 对手道具准备中...")

            st.divider()

            if st.session_state.dynasty_item_drawn:
                if st.button("🚀 模拟本场王朝对决", type="primary", key="simulate_dynasty_match_btn"):
                    my_power_bonus = 0
                    enemy_power_bonus = 0

                    active_my_team = [Player(p.name, p.age, p.team, p.rating, getattr(p, "position", "未知")) for p in st.session_state.dynasty_my_team]
                    active_enemy_team = [Player(p.name, p.age, p.team, p.rating, getattr(p, "position", "未知")) for p in enemy_team]

                    if st.session_state.dynasty_my_item:
                        eff = st.session_state.dynasty_my_item.get("effect", "")
                        if eff == "self_add_10": my_power_bonus += 10
                        elif eff == "self_sub_10": my_power_bonus -= 10
                        elif eff == "self_add_20": my_power_bonus += 20
                        elif eff == "self_sub_20": my_power_bonus -= 20
                        elif eff == "opp_sub_20": enemy_power_bonus -= 20
                        elif eff == "ankle_breaker":
                            top_enemy = max(active_enemy_team, key=lambda p: p.rating)
                            if top_enemy.rating > 80: top_enemy.rating = 80
                        elif eff == "swap_positions":
                            idx1, idx2 = random.sample(range(5), 2)
                            active_my_team[idx1], active_my_team[idx2] = active_my_team[idx2], active_my_team[idx1]

                    if st.session_state.dynasty_enemy_item:
                        eff = st.session_state.dynasty_enemy_item.get("effect", "")
                        if eff == "self_add_10": enemy_power_bonus += 10
                        elif eff == "self_sub_10": enemy_power_bonus -= 10
                        elif eff == "self_add_20": enemy_power_bonus += 20
                        elif eff == "self_sub_20": enemy_power_bonus -= 20
                        elif eff == "opp_sub_20": my_power_bonus -= 20
                        elif eff == "ankle_breaker":
                            top_my = max(active_my_team, key=lambda p: p.rating)
                            if top_my.rating > 80: top_my.rating = 80

                    my_raw_power = sum([p.rating for p in active_my_team])
                    enemy_raw_power = sum([p.rating for p in active_enemy_team])

                    my_base_power = max(10, my_raw_power + my_power_bonus)
                    enemy_base_power = max(10, enemy_raw_power + enemy_power_bonus)

                    my_venue_str = "无 (+0%)"
                    enemy_venue_str = "无 (+0%)"
                    if current_venue == "主场":
                        my_venue_str = "主场作战 (+5%)"
                        my_base_power *= 1.05
                    else:
                        enemy_venue_str = "客场对手主场 (+5%)"
                        enemy_base_power *= 1.05

                    my_popo_str = "未召唤 (+0%)"
                    if st.session_state.popovich_summoned:
                        my_popo_str = "成功召唤波波维奇 (+10%)"
                        my_base_power *= 1.10

                    my_item_str = f"{st.session_state.dynasty_my_item.get('name')} (战力修正: {my_power_bonus})" if st.session_state.dynasty_my_item else "无道具 (0)"
                    enemy_item_str = f"{st.session_state.dynasty_enemy_item.get('name')} (战力修正: {enemy_power_bonus})" if st.session_state.dynasty_enemy_item else "无道具 (0)"

                    raw_my_score = max(10, int(my_base_power * random.uniform(0.88, 1.12)))
                    raw_enemy_score = max(10, int(enemy_base_power * random.uniform(0.88, 1.12)))

                    game_base_total = random.randint(195, 225)
                    real_my_score = round(game_base_total * (raw_my_score / (raw_my_score + raw_enemy_score)))
                    real_enemy_score = game_base_total - real_my_score

                    if real_my_score == real_enemy_score:
                        real_my_score += 2

                    if real_my_score > real_enemy_score:
                        match_status = "胜利"
                        st.session_state.dynasty_wins += 1
                    else:
                        match_status = "失败"
                        st.session_state.dynasty_losses += 1

                    st.session_state.dynasty_history.append((match_status, real_my_score, real_enemy_score))

                    mvp_weights = [max(1, p.rating - 60) for p in active_my_team]
                    mvp_player = random.choices(active_my_team, weights=mvp_weights, k=1)[0]

                    st.session_state.dynasty_last_result = {
                        "status": match_status,
                        "my_score": real_my_score,
                        "enemy_score": real_enemy_score,
                        "mvp": mvp_player,
                        "venue": current_venue,
                        "my_base_power": round(my_raw_power, 1),
                        "enemy_base_power": round(enemy_raw_power, 1),
                        "my_venue_str": my_venue_str,
                        "enemy_venue_str": enemy_venue_str,
                        "my_popo_str": my_popo_str,
                        "my_item_str": my_item_str,
                        "enemy_item_str": enemy_item_str,
                        "my_final_power": round(my_base_power, 1),
                        "enemy_final_power": round(enemy_base_power, 1)
                    }
                    st.session_state.dynasty_match_finished = True
                    st.rerun()

        st.divider()
        if st.button("🏳️ 放弃当前征程并重新选人", key="give_up_dynasty_btn"):
            st.session_state.dynasty_active = False
            st.session_state.dynasty_match_finished = False
            st.session_state.dynasty_last_result = None
            st.session_state.dynasty_venue = None
            st.session_state.popovich_summoned = False
            st.session_state.popovich_attempted = False
            st.session_state.pop("current_enemy_team", None)
            st.rerun()

# ----------------- 8. 🏆 黄金季后赛 -----------------
elif menu == "🏆 黄金季后赛":
    col_t_play, col_btn_play = st.columns([4, 1])
    with col_t_play:
        st.header("🏆 黄金季后赛 (东西部分区 · 七场四胜制)")
    with col_btn_play:
        st.write("")
        if st.button("🔄 重新开始", key="restart_playoffs"):
            st.session_state.playoffs_active = False
            st.session_state.playoffs_round = 0
            st.session_state.playoffs_series = []
            st.session_state.playoffs_champion = None
            for key in list(st.session_state.keys()):
                if key.startswith("playoffs_"):
                    del st.session_state[key]
            st.rerun()
    st.caption("系统将东西部球队分别按实力抽签选出各自的黄金四强，分区内部先打半决赛、再打分区决赛；只有西部冠军和东部冠军才会在总决赛相遇，每点击一次「下一步」模拟一场比赛。")

    if "playoffs_active" not in st.session_state:
        st.session_state.playoffs_active = False
    if "playoffs_round" not in st.session_state:
        st.session_state.playoffs_round = 0
    if "playoffs_series" not in st.session_state:
        st.session_state.playoffs_series = []
    if "playoffs_champion" not in st.session_state:
        st.session_state.playoffs_champion = None

    ROUND_NAMES = ["🥉 黄金八强赛（分区半决赛）", "🥈 分区决赛（东部/西部）", "🥇 总决赛（西部冠军 vs 东部冠军）"]

    def weighted_sample_without_replacement(pop, weights, k):
        pool = list(zip(pop, weights))
        result = []
        for _ in range(k):
            total = sum(w for _, w in pool)
            r = random.uniform(0, total)
            upto = 0
            for i, (item, w) in enumerate(pool):
                upto += w
                if upto >= r:
                    result.append(item)
                    pool.pop(i)
                    break
        return result

    def simulate_playoff_game(power_a, power_b):
        raw_a = max(10, int(power_a * random.uniform(0.85, 1.15)))
        raw_b = max(10, int(power_b * random.uniform(0.85, 1.15)))
        game_total = random.randint(195, 225)
        score_a = round(game_total * (raw_a / (raw_a + raw_b)))
        score_b = game_total - score_a
        if score_a == score_b:
            if raw_a >= raw_b:
                score_a += random.choice([2, 3])
            else:
                score_b += random.choice([2, 3])
        return score_a, score_b

    WEST_KEYWORDS = ["Lakers", "Clippers", "Warriors", "Kings", "Suns", "Nuggets", "Timberwolves", "Thunder", "Mavericks", "Grizzlies", "Pelicans", "Spurs", "Jazz", "Trail Blazers", "Rockets"]
    EAST_KEYWORDS = ["76ers", "Bucks", "Bulls", "Cavaliers", "Celtics", "Hawks", "Heat", "Hornets", "Knicks", "Magic", "Pacers", "Pistons", "Raptors", "Nets", "Wizards"]

    def get_conference(team_name):
        for kw in WEST_KEYWORDS:
            if kw in team_name: return "西部"
        for kw in EAST_KEYWORDS:
            if kw in team_name: return "东部"
        return None

    def build_conference_seeds(team_power_list, guaranteed_count, lucky_count, power_exponent):
        guaranteed_names = [t for t, _ in team_power_list[:guaranteed_count]]
        remaining_pool = team_power_list[guaranteed_count:]
        remaining_names = [t for t, _ in remaining_pool]
        remaining_weights = [max(1.0, p) ** power_exponent for _, p in remaining_pool]
        lucky_names = weighted_sample_without_replacement(remaining_names, remaining_weights, lucky_count)

        chosen_names = guaranteed_names + lucky_names
        power_lookup = dict(team_power_list)
        chosen_with_power = [(n, power_lookup[n]) for n in chosen_names]
        chosen_with_power.sort(key=lambda x: x[1], reverse=True)

        seeds = []
        for i, (t_name, t_power) in enumerate(chosen_with_power):
            seeds.append({
                "seed": i + 1,
                "team": t_name,
                "power": round(t_power * 5, 1)
            })
        return seeds

    if not st.session_state.playoffs_active:
        team_players_map = {}
        for p in players:
            team_players_map.setdefault(p.team, []).append(p)

        west_list = []
        east_list = []
        unknown_teams = []
        for t_name, plist in team_players_map.items():
            avg_rating = sum(pp.rating for pp in plist) / len(plist)
            conf = get_conference(t_name)
            if conf == "西部": west_list.append((t_name, avg_rating))
            elif conf == "东部": east_list.append((t_name, avg_rating))
            else: unknown_teams.append(t_name)

        west_list.sort(key=lambda x: x[1], reverse=True)
        east_list.sort(key=lambda x: x[1], reverse=True)

        if unknown_teams:
            st.warning(f"⚠️ 以下球队名称无法识别所属分区，暂不参与黄金季后赛分区赛程：{'、'.join(unknown_teams)}")

        if len(west_list) < 4 or len(east_list) < 4:
            st.error(f"⚠️ 东西部球队数量不足，无法开启分区赛程！（西部：{len(west_list)} 支 / 东部：{len(east_list)} 支，各分区至少需要 4 支）")
        else:
            col_w, col_e = st.columns(2)
            with col_w:
                st.subheader("🌵 西部实力榜")
                st.table([{"排名": i + 1, "球队": t, "平均能力值": f"{p:.1f}"} for i, (t, p) in enumerate(west_list)])
            with col_e:
                st.subheader("🗽 东部实力榜")
                st.table([{"排名": i + 1, "球队": t, "平均能力值": f"{p:.1f}"} for i, (t, p) in enumerate(east_list)])

            if st.button("🎲 开始抽签，产生东西部黄金四强！", type="primary"):
                west_seeds = build_conference_seeds(west_list, 2, 2, 4)
                east_seeds = build_conference_seeds(east_list, 2, 2, 4)

                def make_series(a, b, conf_label):
                    return {
                        "seed_a": a["seed"], "team_a": a["team"], "power_a": a["power"], "conf_a": conf_label,
                        "seed_b": b["seed"], "team_b": b["team"], "power_b": b["power"], "conf_b": conf_label,
                        "wins_a": 0, "wins_b": 0, "finished": False, "winner": None, "game_log": []
                    }

                first_round = [
                    make_series(west_seeds[0], west_seeds[3], "西部"),
                    make_series(west_seeds[1], west_seeds[2], "西部"),
                    make_series(east_seeds[0], east_seeds[3], "东部"),
                    make_series(east_seeds[1], east_seeds[2], "东部"),
                ]

                st.session_state.playoffs_series = first_round
                st.session_state.playoffs_round = 0
                st.session_state.playoffs_champion = None
                st.session_state.playoffs_active = True
                st.rerun()

    else:
        round_idx = st.session_state.playoffs_round
        series_list = st.session_state.playoffs_series

        st.subheader(ROUND_NAMES[round_idx])

        cols = st.columns(len(series_list))
        for i, s in enumerate(series_list):
            with cols[i]:
                status = "✅ 已晋级" if s["finished"] else "⏳ 进行中"
                conf_tag = f"[{s['conf_a']}]" if s.get("conf_a") == s.get("conf_b") else "[总决赛]"
                st.caption(conf_tag)
                st.markdown(f"**[{s['seed_a']}号种子]**\n\n**{s['team_a']}**")
                st.markdown(f"### `{s['wins_a']} : {s['wins_b']}`")
                st.markdown(f"**{s['team_b']}**\n\n**[{s['seed_b']}号种子]**")
                st.caption(status + (f" — 晋级：**{s['winner']}**" if s["finished"] else ""))
                if s["game_log"]:
                    with st.expander(f"📜 系列赛日志 ({len(s['game_log'])}场)"):
                        for log in s["game_log"]:
                            st.write(log)

        st.divider()

        all_finished = all(s["finished"] for s in series_list)

        if not all_finished:
            if st.button("👉 下一步：模拟下一场比赛", type="primary", key=f"playoffs_next_{round_idx}"):
                for s in series_list:
                    if s["finished"]: continue
                    score_a, score_b = simulate_playoff_game(s["power_a"], s["power_b"])
                    if score_a > score_b:
                        s["wins_a"] += 1
                        game_winner = s["team_a"]
                    else:
                        s["wins_b"] += 1
                        game_winner = s["team_b"]
                    game_num = s["wins_a"] + s["wins_b"]
                    s["game_log"].append(f"第{game_num}场：{s['team_a']} {score_a} : {score_b} {s['team_b']}（{game_winner} 获胜）")

                    if s["wins_a"] == 4:
                        s["finished"] = True
                        s["winner"] = s["team_a"]
                    elif s["wins_b"] == 4:
                        s["finished"] = True
                        s["winner"] = s["team_b"]
                st.rerun()
        else:
            if round_idx < 2:
                next_round_label = ROUND_NAMES[round_idx + 1]
                if st.button(f"🚀 下一步：晋级 {next_round_label}", type="primary", key=f"playoffs_advance_{round_idx}"):
                    winners = []
                    for s in series_list:
                        if s["winner"] == s["team_a"]:
                            winners.append({"seed": s["seed_a"], "team": s["team_a"], "power": s["power_a"], "conf": s["conf_a"]})
                        else:
                            winners.append({"seed": s["seed_b"], "team": s["team_b"], "power": s["power_b"], "conf": s["conf_b"]})

                    next_series = []
                    for i in range(0, len(winners), 2):
                        a = winners[i]
                        b = winners[i + 1]
                        next_series.append({
                            "seed_a": a["seed"], "team_a": a["team"], "power_a": a["power"], "conf_a": a["conf"],
                            "seed_b": b["seed"], "team_b": b["team"], "power_b": b["power"], "conf_b": b["conf"],
                            "wins_a": 0, "wins_b": 0, "finished": False, "winner": None, "game_log": []
                        })
                    st.session_state.playoffs_series = next_series
                    st.session_state.playoffs_round += 1
                    st.rerun()
            else:
                champion = series_list[0]["winner"]
                st.session_state.playoffs_champion = champion
                st.balloons()
                st.success(f"🏆🏆🏆 恭喜 **{champion}** 夺得本届黄金季后赛总冠军！🏆🏆🏆")
                if st.button("🔄 重新开始新一届黄金季后赛", type="primary", key="playoffs_restart_btn"):
                    st.session_state.playoffs_active = False
                    st.session_state.playoffs_round = 0
                    st.session_state.playoffs_series = []
                    st.session_state.playoffs_champion = None
                    st.rerun()

# ----------------- 9.  资本家之战 -----------------
elif menu == " 资本家之战":
    col_t_cap, col_btn_cap = st.columns([4, 1])
    with col_t_cap:
        st.header(" 资本家之战 (人机对决  球员拍卖交易与先拿7胜者胜)")
    with col_btn_cap:
        st.write("")
        if st.button(" 重新开始", key="restart_cap"):
            st.session_state.cap_inited = False
            for key in list(st.session_state.keys()):
                if key.startswith("cap_") or key.startswith("cap_p_slot_"):
                    del st.session_state[key]
            st.rerun()
    st.caption("资本运作与赛场博弈的终极对决！支持玩家发起拍卖交易、AI 也会随机发起拍卖交易，搭配首发指派与赛前道具。每局胜者 +$4 美元，败者加 +$2 美元，败者必须割爱淘汰一名【当局首发】球员！")
    all_teams = sorted(list(set(p.team for p in players if p.team)))

    if "cap_inited" not in st.session_state:
        st.session_state.cap_inited = False

    if not st.session_state.cap_inited:
        st.subheader(" 赛前准备：选择你的主队")
        p_team_choice = st.selectbox("选择玩家控制的球队：", all_teams)
        
        if st.button(" 开始资本家之战！", type="primary"):
            ai_teams = [t for t in all_teams if t != p_team_choice]
            ai_team_choice = random.choice(ai_teams) if ai_teams else p_team_choice
            
            p_roster = [Player(p.name, p.age, p.team, p.rating, getattr(p, "position", "未知")) for p in players if p.team == p_team_choice]
            ai_roster = [Player(p.name, p.age, p.team, p.rating, getattr(p, "position", "未知")) for p in players if p.team == ai_team_choice]
            
            if len(p_roster) < 5:
                extra = random.sample(players, 5 - len(p_roster))
                p_roster.extend([Player(p.name, p.age, p.team, p.rating, getattr(p, "position", "未知")) for p in extra])
            if len(ai_roster) < 5:
                extra = random.sample(players, 5 - len(ai_roster))
                ai_roster.extend([Player(p.name, p.age, p.team, p.rating, getattr(p, "position", "未知")) for p in extra])

            st.session_state.cap_player_team = p_team_choice
            st.session_state.cap_ai_team = ai_team_choice
            st.session_state.cap_player_roster = p_roster
            st.session_state.cap_ai_roster = ai_roster
            st.session_state.cap_player_money = 30
            st.session_state.cap_ai_money = 30
            st.session_state.cap_player_wins = 0
            st.session_state.cap_ai_wins = 0
            st.session_state.cap_round = 1
            st.session_state.cap_phase = "actions"
            st.session_state.cap_p_actions_count = 0
            st.session_state.cap_bribe_p = False
            st.session_state.cap_bribe_ai = False
            st.session_state.cap_encouraged_p = []
            st.session_state.cap_encouraged_ai = []
            st.session_state.cap_item_p = None
            st.session_state.cap_item_ai = None
            st.session_state.cap_fusion_mode = False
            st.session_state.cap_match_finished = False
            st.session_state.cap_discard_phase = False
            st.session_state.cap_last_match_result = None
            
            st.session_state.cap_player_money_history = [("初始资金", "系统发放", 30, 30)]
            st.session_state.cap_ai_money_history = [("初始资金", "系统发放", 30, 30)]
            
            st.session_state.cap_auction_target = None
            st.session_state.cap_auction_current_bid = 10
            st.session_state.cap_auction_bidder = None 
            st.session_state.cap_auction_owner = None  
            st.session_state.cap_inited = True
            
            for pos in POSITIONS:
                st.session_state.pop(f"cap_p_slot_{pos}", None)
            st.rerun()

    else:
        st.markdown(f"###  战局比分:  玩家 [{st.session_state.cap_player_team}] `{st.session_state.cap_player_wins}` vs `{st.session_state.cap_ai_wins}`  AI [{st.session_state.cap_ai_team}]")
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric(" 玩家资金", f"${st.session_state.cap_player_money}", f"阵容人数: {len(st.session_state.cap_player_roster)}")
        col_m2.metric(" AI 资金", f"${st.session_state.cap_ai_money}", f"阵容人数: {len(st.session_state.cap_ai_roster)}")
        col_m3.metric(" 当前局数", f"第 {st.session_state.cap_round} 局", f"目标: 7胜")

        hist_col1, hist_col2 = st.columns(2)
        with hist_col1:
            with st.expander("  查看玩家历史资金流"):
                if st.session_state.get("cap_player_money_history"):
                    for h_desc, h_act, h_diff, h_bal in st.session_state.cap_player_money_history:
                        diff_str = f"+${h_diff}" if h_diff > 0 else (f"-${abs(h_diff)}" if h_diff < 0 else "$0")
                        st.markdown(f"- **[{h_desc}]** {h_act} | 变动: `{diff_str}` | 余额: **${h_bal}**")
                else:
                    st.caption("暂无资金变动记录")
        with hist_col2:
            with st.expander("  查看 AI 历史资金流"):
                if st.session_state.get("cap_ai_money_history"):
                    for h_desc, h_act, h_diff, h_bal in st.session_state.cap_ai_money_history:
                        diff_str = f"+${h_diff}" if h_diff > 0 else (f"-${abs(h_diff)}" if h_diff < 0 else "$0")
                        st.markdown(f"- **[{h_desc}]** {h_act} | 变动: `{diff_str}` | 余额: **${h_bal}**")

        st.divider()

        if st.session_state.cap_player_wins >= 7:
            st.balloons()
            st.success(f" 恭喜！你成功率先赢得 7 局胜利，击败了  AI [{st.session_state.cap_ai_team}]，赢得了资本家之战！")
            if st.button(" 重新开启资本家之战"):
                st.session_state.cap_inited = False
                st.rerun()
            st.stop()
        elif st.session_state.cap_ai_wins >= 7:
            st.error(f" 很遗憾， AI [{st.session_state.cap_ai_team}] 率先拿到 7 胜，你在资本家之战中败北！")
            if st.button(" 重新开启资本家之战"):
                st.session_state.cap_inited = False
                st.rerun()
            st.stop()

        # ================= AI 主动发起拍卖交易处理逻辑 =================
        if st.session_state.get("cap_ai_initiated_auction", False):
            st.warning(" **【突发事件】对方 AI 发起了拍卖交易！** 意图通过竞拍获取你阵中的一名球员！")
            target_p = st.session_state.cap_auction_target
            st.info(f" AI 盯上了你的球员：**{target_p.name}** [位置: {getattr(target_p, 'position', '未知')}] (能力值: {target_p.rating}分)")
            st.write(f"当前拍卖价：**${st.session_state.cap_auction_current_bid}** (固定 10 美元起拍) | 当前领先方：**{' AI 方' if st.session_state.cap_auction_bidder == 'ai' else ' 你 (防守方)'}**")
            
            c_ai_act1, c_ai_act2 = st.columns(2)
            min_follow_bid = st.session_state.cap_auction_current_bid + 1
            with c_ai_act1:
                can_follow = (st.session_state.cap_player_money >= min_follow_bid)
                follow_val = st.number_input("跟价保留球员 ($)", min_value=min_follow_bid, max_value=max(min_follow_bid, st.session_state.cap_player_money), value=min_follow_bid, step=1, disabled=not can_follow, key="ai_auction_follow_input")
                if st.button(" 跟价保留该球员", disabled=not can_follow):
                    st.session_state.cap_auction_current_bid = follow_val
                    st.session_state.cap_auction_bidder = "player"
                    ai_max_afford = st.session_state.cap_ai_money
                    if ai_max_afford >= follow_val + 1 and random.random() < 0.7:
                        ai_new_bid = follow_val + 1
                        st.session_state.cap_auction_current_bid = ai_new_bid
                        st.session_state.cap_auction_bidder = "ai"
                        st.success(f"你跟价至 ${follow_val}，但 AI 紧咬不放，反跟价至 ${ai_new_bid}！")
                        st.rerun()
                    else:
                        st.session_state.cap_player_money -= follow_val
                        st.session_state.cap_player_money_history.append((f"第{st.session_state.cap_round}局-防守拍卖", f"跟价保住 {target_p.name}", -follow_val, st.session_state.cap_player_money))
                        
                        st.session_state.cap_ai_money += follow_val
                        st.session_state.cap_ai_money_history.append((f"第{st.session_state.cap_round}局-防守拍卖保住补偿", f"对手跟价补偿 {target_p.name}", follow_val, st.session_state.cap_ai_money))
                        
                        st.session_state.cap_ai_initiated_auction = False
                        st.session_state.cap_auction_target = None
                        st.success(f" AI 资金不足或选择放弃！你以 ${follow_val} 成功跟价保住了 **{target_p.name}**！资金已严格按成交金额支付给对方。")
                        st.rerun()

            with c_ai_act2:
                if st.button(" 放弃抵抗 (让 AI 拍走)"):
                    if target_p in st.session_state.cap_player_roster:
                        st.session_state.cap_player_roster.remove(target_p)
                        st.session_state.cap_ai_roster.append(target_p)
                    cost = st.session_state.cap_auction_current_bid
                    
                    st.session_state.cap_ai_money = max(0, st.session_state.cap_ai_money - cost)
                    st.session_state.cap_ai_money_history.append((f"第{st.session_state.cap_round}局-拍卖成功", f"拍得 {target_p.name}", -cost, st.session_state.cap_ai_money))
                    
                    st.session_state.cap_player_money += cost
                    st.session_state.cap_player_money_history.append((f"第{st.session_state.cap_round}局-球员售出赔偿", f"失去 {target_p.name} 补偿", cost, st.session_state.cap_player_money))
                    
                    st.session_state.cap_ai_initiated_auction = False
                    st.session_state.cap_auction_target = None
                    st.error(f" 你选择放弃，AI 以 ${cost} 成功将你的 **{target_p.name}** 拍走，拍卖资金已严格转入你的账户！")
                    st.rerun()
            st.stop()

        # ================= 玩家主动发起拍卖交易的弹窗/交互逻辑 =================
        if st.session_state.get("cap_player_initiated_auction", False):
            target_p = st.session_state.cap_auction_target
            st.subheader(f" 球员拍卖行：正在对 AI 的 **{target_p.name}** 发起拍卖交易！")
            st.info(f"目标球员：**{target_p.name}** [位置: {getattr(target_p, 'position', '未知')}] (能力值: {target_p.rating}分)")
            st.write(f"当前出价：**${st.session_state.cap_auction_current_bid}** (固定 10 美元起拍) | 当前领先方：**{' 你' if st.session_state.cap_auction_bidder == 'player' else ' AI (防守方)'}**")

            p_bid_col1, p_bid_col2 = st.columns(2)
            min_p_bid = st.session_state.cap_auction_current_bid + 1
            with p_bid_col1:
                can_p_bid = (st.session_state.cap_player_money >= min_p_bid)
                p_bid_val = st.number_input("提高出价 ($)", min_value=min_p_bid, max_value=max(min_p_bid, st.session_state.cap_player_money), value=min_p_bid, step=1, disabled=not can_p_bid, key="player_auction_bid_input")
                if st.button(" 加价竞拍", disabled=not can_p_bid):
                    st.session_state.cap_auction_current_bid = p_bid_val
                    st.session_state.cap_auction_bidder = "player"
                    ai_afford = st.session_state.cap_ai_money
                    if ai_afford >= p_bid_val + 1 and random.random() < 0.65:
                        ai_bid = p_bid_val + 1
                        st.session_state.cap_auction_current_bid = ai_bid
                        st.session_state.cap_auction_bidder = "ai"
                        st.warning(f"你加价到 ${p_bid_val}，但 AI 随即跟价保球员至 ${ai_bid}！")
                        st.rerun()
                    else:
                        cost = p_bid_val
                        st.session_state.cap_player_money = max(0, st.session_state.cap_player_money - cost)
                        st.session_state.cap_player_money_history.append((f"第{st.session_state.cap_round}局-拍卖成功", f"拍得 {target_p.name}", -cost, st.session_state.cap_player_money))
                        
                        st.session_state.cap_ai_money += cost
                        st.session_state.cap_ai_money_history.append((f"第{st.session_state.cap_round}局-售出球员补偿", f"售出 {target_p.name} 补偿", cost, st.session_state.cap_ai_money))
                        
                        st.session_state.cap_ai_roster.remove(target_p)
                        st.session_state.cap_player_roster.append(target_p)
                        st.session_state.cap_player_initiated_auction = False
                        st.session_state.cap_auction_target = None
                        st.success(f" 竞拍成功！AI 放弃跟价，你以 **${cost}** 成功将 **{target_p.name}** 拍入己方阵容，资金已严格按照成交金额支付给对方！")
                        st.session_state.cap_p_actions_count += 1
                        st.rerun()

            with p_bid_col2:
                pass_disabled = (st.session_state.cap_auction_bidder != "ai")
                if pass_disabled:
                    st.caption(" 你是当前领先方，无法放弃竞拍（需先被 AI 反超才能选择放弃）")
                if st.button(" 放弃竞拍 (Pass)", disabled=pass_disabled):
                    winner = st.session_state.cap_auction_bidder
                    if winner == "ai":
                        st.info("你放弃了竞拍，AI 成功保留了该球员。")
                    else:
                        cost = st.session_state.cap_auction_current_bid
                        st.session_state.cap_player_money = max(0, st.session_state.cap_player_money - cost)
                        st.session_state.cap_player_money_history.append((f"第{st.session_state.cap_round}局-拍卖成功", f"拍得 {target_p.name}", -cost, st.session_state.cap_player_money))
                        
                        st.session_state.cap_ai_money += cost
                        st.session_state.cap_ai_money_history.append((f"第{st.session_state.cap_round}局-售出球员补偿", f"售出 {target_p.name} 补偿", cost, st.session_state.cap_ai_money))
                        
                        st.session_state.cap_ai_roster.remove(target_p)
                        st.session_state.cap_player_roster.append(target_p)
                        st.success(f"你以最终成交价 **${cost}** 成功拍得该球员，资金已严格按照成交金额支付给对方！")
                        st.session_state.cap_p_actions_count += 1
                    st.session_state.cap_player_initiated_auction = False
                    st.session_state.cap_auction_target = None
                    st.rerun()
            st.stop()

        # ================= 阶段 1: 资本功能操作 =================
        if st.session_state.cap_phase == "actions":
            if len(st.session_state.cap_player_roster) < 5:
                st.session_state.cap_ai_wins = 7
                st.rerun()

            if len(st.session_state.cap_ai_roster) < 5:
                st.session_state.cap_player_wins = 7
                st.rerun()

            st.subheader(f" 第 {st.session_state.cap_round} 局  资本运作阶段（每局最多选 0~3 次功能）")
            st.caption(f"当前剩余操作数：**{3 - st.session_state.cap_p_actions_count}** / 3 | 当前可用资金：**${st.session_state.cap_player_money}**")

            r_col1, r_col2 = st.columns(2)
            with r_col1:
                st.markdown("** 己方阵容：**")
                st.dataframe(players_to_dict_list(st.session_state.cap_player_roster), use_container_width=True)
            with r_col2:
                st.markdown("** 对方阵容：**")
                st.dataframe(players_to_dict_list(st.session_state.cap_ai_roster), use_container_width=True)

            st.markdown("####  购买资本功能：")
            act_col1, act_col2 = st.columns(2)

            can_act = (st.session_state.cap_p_actions_count < 3)

            with act_col1:
                bribe_disabled = (not can_act) or (st.session_state.cap_player_money < 2) or st.session_state.cap_bribe_p
                if st.button(" 1. 贿赂裁判 ($2) [全队战力当局+10%]", disabled=bribe_disabled):
                    st.session_state.cap_player_money -= 2
                    st.session_state.cap_player_money_history.append((f"第{st.session_state.cap_round}局", "贿赂裁判", -2, st.session_state.cap_player_money))
                    st.session_state.cap_bribe_p = True
                    st.session_state.cap_p_actions_count += 1
                    st.success("已成功贿赂裁判！当局战力提升 10%")
                    st.rerun()

                draw_disabled = (not can_act) or (st.session_state.cap_player_money < 5)
                if st.button(" 3. 抽取球员 ($5) [抽1名球员放进阵容]", disabled=draw_disabled):
                    new_p = random.choice(players)
                    st.session_state.cap_player_roster.append(Player(new_p.name, new_p.age, new_p.team, new_p.rating, getattr(new_p, "position", "未知")))
                    st.session_state.cap_player_money -= 5
                    st.session_state.cap_player_money_history.append((f"第{st.session_state.cap_round}局", f"抽取球员 {new_p.name}", -5, st.session_state.cap_player_money))
                    st.session_state.cap_p_actions_count += 1
                    st.success(f"成功抽取球员：{new_p.name} ({new_p.rating}分)")
                    st.rerun()

                fusion_disabled = (not can_act) or (st.session_state.cap_player_money < 7) or (len(st.session_state.cap_player_roster) < 3)
                if st.button(" 5. 球员合成 ($7) [3个球员合成库内80+球员]", disabled=fusion_disabled):
                    st.session_state.cap_fusion_mode = True
                    st.rerun()

            with act_col2:
                enc_disabled = (not can_act) or (st.session_state.cap_player_money < 1) or len(st.session_state.cap_player_roster) == 0
                enc_p_names = [f"{p.name} ({p.rating}分)" for p in st.session_state.cap_player_roster if p.name not in st.session_state.cap_encouraged_p]
                if enc_p_names:
                    sel_enc = st.selectbox("选择要鼓励的球员：", enc_p_names, key="enc_sel_box")
                    if st.button(" 2. 鼓励该球员 ($1) [评分当局增加20%]", disabled=enc_disabled):
                        target_name = sel_enc.split(" (")[0]
                        st.session_state.cap_encouraged_p.append(target_name)
                        st.session_state.cap_player_money -= 1
                        st.session_state.cap_player_money_history.append((f"第{st.session_state.cap_round}局", f"鼓励球员 {target_name}", -1, st.session_state.cap_player_money))
                        st.session_state.cap_p_actions_count += 1
                        st.success(f"成功鼓励 {target_name}！当局能力值 +20%")
                        st.rerun()

                poach_disabled = (not can_act) or (st.session_state.cap_player_money < 10) or len(st.session_state.cap_ai_roster) == 0
                poach_ai_names = [f"{p.name} [{getattr(p, 'position', '未知')}] ({p.rating}分)" for p in st.session_state.cap_ai_roster]
                sel_poach = st.selectbox("选择要拍卖交易的 AI 球员：", poach_ai_names, key="auction_sel_box")
                if st.button(" 4. 发起拍卖交易 ($10起拍)", disabled=poach_disabled):
                    target_name = sel_poach.split(" [")[0]
                    target_p = next((p for p in st.session_state.cap_ai_roster if p.name == target_name), None)
                    if target_p:
                        st.session_state.cap_auction_target = target_p
                        st.session_state.cap_auction_current_bid = 10  # 严格固定从 10 美元起拍
                        st.session_state.cap_auction_bidder = "player"
                        st.session_state.cap_player_initiated_auction = True
                        st.rerun()

            # 球员合成弹窗子界面
            if st.session_state.get("cap_fusion_mode", False):
                st.divider()
                st.subheader(" 球员合成工坊（选择 3 名己方球员合成 1 名随机 80+ 强力球员）")
                fusion_p_names = [f"{p.name} [{getattr(p, 'position', '未知')}] ({p.rating}分)" for p in st.session_state.cap_player_roster]
                selected_fusion_keys = st.multiselect("请选择要作为材料融合的 3 名球员：", fusion_p_names, max_selections=3, key="fusion_multiselect")
                
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    if st.button(" 确认消耗并合成！", type="primary"):
                        if len(selected_fusion_keys) == 3:
                            to_remove = []
                            for k in selected_fusion_keys:
                                n = k.split(" [")[0]
                                found = next((p for p in st.session_state.cap_player_roster if p.name == n), None)
                                if found: to_remove.append(found)
                            for p in to_remove:
                                st.session_state.cap_player_roster.remove(p)
                            
                            high_pool = [p for p in players if p.rating >= 80]
                            if not high_pool: high_pool = players
                            new_f = random.choice(high_pool)
                            st.session_state.cap_player_roster.append(Player(new_f.name, new_f.age, new_f.team, new_f.rating, getattr(new_f, "position", "未知")))
                            
                            st.session_state.cap_player_money -= 7
                            st.session_state.cap_player_money_history.append((f"第{st.session_state.cap_round}局", f"合成获得 {new_f.name}", -7, st.session_state.cap_player_money))
                            st.session_state.cap_p_actions_count += 1
                            st.session_state.cap_fusion_mode = False
                            st.balloons()
                            st.success(f" 合成成功！你获得了高强球员：**{new_f.name}** ({new_f.rating}分)")
                            st.rerun()
                        else:
                            st.warning(" 必须且只能选择恰好 3 名球员作为合成材料！")
                with col_f2:
                    if st.button(" 取消合成"):
                        st.session_state.cap_fusion_mode = False
                        st.rerun()

            st.divider()
            if st.button(" 资本运作完毕，进入首发指派与对决阶段", type="primary"):
                # AI 资本阶段行为模拟
                if st.session_state.cap_ai_money >= 5 and random.random() < 0.6 and len(st.session_state.cap_ai_roster) < 8:
                    ai_draw = random.choice(players)
                    st.session_state.cap_ai_roster.append(Player(ai_draw.name, ai_draw.age, ai_draw.team, ai_draw.rating, getattr(ai_draw, "position", "未知")))
                    st.session_state.cap_ai_money -= 5
                    st.session_state.cap_ai_money_history.append((f"第{st.session_state.cap_round}局", f"AI抽取球员 {ai_draw.name}", -5, st.session_state.cap_ai_money))
                
                if st.session_state.cap_ai_money >= 2 and random.random() < 0.5:
                    st.session_state.cap_bribe_ai = True
                    st.session_state.cap_ai_money -= 2
                    st.session_state.cap_ai_money_history.append((f"第{st.session_state.cap_round}局", "AI贿赂裁判", -2, st.session_state.cap_ai_money))

                if st.session_state.cap_ai_money >= 10 and random.random() < 0.35 and len(st.session_state.cap_player_roster) > 0:
                    ai_auction_target = random.choice(st.session_state.cap_player_roster)
                    st.session_state.cap_auction_target = ai_auction_target
                    st.session_state.cap_auction_current_bid = 10  # 严格固定从 10 美元起拍
                    st.session_state.cap_auction_bidder = "ai"
                    st.session_state.cap_ai_initiated_auction = True
                    st.rerun()

                st.session_state.cap_phase = "lineup"
                st.rerun()

        # ================= 阶段 2: 首发指派与比赛模拟 =================
        elif st.session_state.cap_phase == "lineup":
            st.subheader(f" 第 {st.session_state.cap_round} 局  首发指派与赛前博弈")
            st.markdown("请将己方阵容中的球员指派到 5 个位置槽位中（支持位置偏移折损计算）：")

            p_dict = {f"{p.name} [{getattr(p, 'position', '未知')}] ({p.rating}分)": p for p in st.session_state.cap_player_roster}
            player_assigned = []
            selected_names = []
            
            for pos in POSITIONS:
                val = st.session_state.get(f"cap_p_slot_{pos}", "-- 请选择 --")
                if val != "-- 请选择 --":
                    selected_names.append(val)

            col_l1, col_l2 = st.columns(2)
            for idx, pos in enumerate(POSITIONS):
                with (col_l1 if idx % 2 == 0 else col_l2):
                    curr_val = st.session_state.get(f"cap_p_slot_{pos}", "-- 请选择 --")
                    avail = ["-- 请选择 --"] + [k for k in p_dict.keys() if k not in selected_names or k == curr_val]
                    if curr_val not in avail:
                        curr_val = "-- 请选择 --"
                        st.session_state[f"cap_p_slot_{pos}"] = "-- 请选择 --"
                    
                    choice = st.selectbox(f"指派己方 [{pos}] 首发：", avail, index=avail.index(curr_val), key=f"cap_p_slot_{pos}")
                    if choice != "-- 请选择 --":
                        p_obj = p_dict[choice]
                        pen, note = calculate_position_penalty(p_obj, pos)
                        st.caption(f" {note}")
                        player_assigned.append((p_obj, pos, pen))

            st.divider()

            # ----------------- AI 阵容指派（严格按照位置的最强五个人） -----------------
            ai_assigned = []
            for pos in POSITIONS:
                pos_matched = [p for p in st.session_state.cap_ai_roster if getattr(p, "position", "") == pos]
                if not pos_matched:
                    pos_matched = sorted(st.session_state.cap_ai_roster, key=lambda x: x.rating, reverse=True)
                else:
                    pos_matched.sort(key=lambda x: x.rating, reverse=True)
                
                best_p = pos_matched[0] if pos_matched else random.choice(st.session_state.cap_ai_roster)
                pen_ai, _ = calculate_position_penalty(best_p, pos)
                ai_assigned.append((best_p, pos, pen_ai))

            st.divider()

            # ----------------- 赛前道具抽取（严格计入总战力） -----------------
            items_pool = [
                {"name": " 佳得乐", "desc": "补充体力", "effect_detail": " 效果：队伍总战力 +10", "effect": "self_add_10"},
                {"name": " 游戏机", "desc": "打游戏", "effect_detail": " 效果：队伍总战力 -10", "effect": "self_sub_10"},
                {"name": " 红色的眼睛", "desc": "全员觉醒", "effect_detail": " 效果：队伍总战力 +20", "effect": "self_add_20"},
                {"name": " 酒瓶", "desc": "夜店喝酒", "effect_detail": " 效果：队伍总战力 -20", "effect": "self_sub_20"},
                {"name": " 嘴", "desc": "喷垃圾话", "effect_detail": " 效果：对方队伍总战力 -20", "effect": "opp_sub_20"},
                {"name": " 脚", "desc": "垫脚", "effect_detail": " 效果：对方评分最高的球员能力值降为 80", "effect": "ankle_breaker"},
                {"name": " 教练上厕所", "desc": "教练不在场", "effect_detail": " 效果：己方随机两位球员位置互换", "effect": "swap_positions"}
            ]

                        st.subheader(" 赛前道具抽取")
            
            # 1. 初始化本局可用的道具池与已抽记录（如果还没有）
            if "cap_available_items" not in st.session_state or st.session_state.get("cap_round_checked") != st.session_state.cap_round:
                st.session_state.cap_available_items = list(items_pool)
                st.session_state.cap_round_checked = st.session_state.cap_round

            c_it1, c_it2 = st.columns(2)
            with c_it1:
                if st.button(" 抽取我的赛前道具", key="cap_draw_item_p") and not st.session_state.get("cap_item_p"):
                    if st.session_state.cap_available_items:
                        # 随机抽取一个，并从可用池中弹出（确保绝不重复）
                        it = random.choice(st.session_state.cap_available_items)
                        st.session_state.cap_available_items.remove(it)
                        st.session_state.cap_item_p = it
                        
                        # 顺便为 AI 也从剩余池中不重复地抽一个
                        if st.session_state.cap_available_items:
                            it_ai = random.choice(st.session_state.cap_available_items)
                            st.session_state.cap_available_items.remove(it_ai)
                            st.session_state.cap_item_ai = it_ai
                        st.rerun()
                    else:
                        st.warning("道具池已经空了！")

                if st.session_state.get("cap_item_p"):
                    it = st.session_state.cap_item_p
                    st.info(f" 你抽到了：**[{it['name']}]**  {it['effect_detail']}")
            with c_it2:
                if st.session_state.get("cap_item_ai"):
                    it_ai = st.session_state.cap_item_ai
                    ai_name = it_ai['name']
                    ai_effect = it_ai['effect_detail']
                    st.caption(f" AI 抽到：**[{ai_name}]** - {ai_effect}")


            st.divider()

            can_simulate = (len(player_assigned) == 5)
            if not can_simulate:
                st.warning(" 请将己方 5 个位置槽位全部指派完毕才能开启模拟比赛！")

            if st.button(" 模拟本局资本家之战！", type="primary", disabled=not can_simulate):
                calc_p_team = [Player(p.name, p.age, p.team, max(0, p.rating - pen), pos) for p, pos, pen in player_assigned]
                calc_ai_team = [Player(p.name, p.age, p.team, max(0, p.rating - pen), pos) for p, pos, pen in ai_assigned]

                p_bonus = 0
                ai_bonus = 0

                if st.session_state.cap_bribe_p: p_bonus += 15
                if st.session_state.cap_bribe_ai: ai_bonus += 15

                for name in st.session_state.cap_encouraged_p:
                    target_p = next((p for p in calc_p_team if p.name == name), None)
                    if target_p: target_p.rating = int(target_p.rating * 1.2)

                if st.session_state.cap_item_p:
                    eff = st.session_state.cap_item_p.get("effect", "")
                    if eff == "self_add_10": p_bonus += 10
                    elif eff == "self_sub_10": p_bonus -= 10
                    elif eff == "self_add_20": p_bonus += 20
                    elif eff == "self_sub_20": p_bonus -= 20
                    elif eff == "opp_sub_20": ai_bonus -= 20
                    elif eff == "ankle_breaker":
                        top_ai = max(calc_ai_team, key=lambda x: x.rating)
                        if top_ai.rating > 80: top_ai.rating = 80
                    elif eff == "swap_positions":
                        if len(calc_p_team) >= 2:
                            idx1, idx2 = random.sample(range(5), 2)
                            calc_p_team[idx1], calc_p_team[idx2] = calc_p_team[idx2], calc_p_team[idx1]

                if st.session_state.get("cap_item_ai"):
                    eff_ai = st.session_state.cap_item_ai.get("effect", "")
                    if eff_ai == "self_add_10": ai_bonus += 10
                    elif eff_ai == "self_sub_10": ai_bonus -= 10
                    elif eff_ai == "self_add_20": ai_bonus += 20
                    elif eff_ai == "self_sub_20": ai_bonus -= 20
                    elif eff_ai == "opp_sub_20": p_bonus -= 20
                    elif eff_ai == "ankle_breaker":
                        top_p = max(calc_p_team, key=lambda x: x.rating)
                        if top_p.rating > 80: top_p.rating = 80

                p_base = sum(p.rating for p in calc_p_team) + p_bonus
                ai_base = sum(p.rating for p in calc_ai_team) + ai_bonus

                raw_p_score = max(10, int(p_base * random.uniform(0.88, 1.12)))
                raw_ai_score = max(10, int(ai_base * random.uniform(0.88, 1.12)))

                total_pts = random.randint(195, 225)
                real_p_score = round(total_pts * (raw_p_score / (raw_p_score + raw_ai_score)))
                real_ai_score = total_pts - real_p_score

                if real_p_score == real_ai_score:
                    real_p_score += 2

                if real_p_score > real_ai_score:
                    match_res = "胜利"
                    st.session_state.cap_player_wins += 1
                    earn_p, earn_ai = 4, 2
                else:
                    match_res = "失败"
                    st.session_state.cap_ai_wins += 1
                    earn_p, earn_ai = 2, 4

                st.session_state.cap_player_money += earn_p
                st.session_state.cap_player_money_history.append((f"第{st.session_state.cap_round}局赛果({match_res})", "比赛奖金收入", earn_p, st.session_state.cap_player_money))

                st.session_state.cap_ai_money += earn_ai
                st.session_state.cap_ai_money_history.append((f"第{st.session_state.cap_round}局赛果", "比赛奖金收入", earn_ai, st.session_state.cap_ai_money))

                st.session_state.cap_last_match_result = {
                    "match_res": match_res,
                    "p_score": real_p_score,
                    "ai_score": real_ai_score,
                    "calc_p_team": calc_p_team,
                    "calc_ai_team": calc_ai_team,
                    "p_base": round(p_base, 1),
                    "ai_base": round(ai_base, 1)
                }
                st.session_state.cap_match_finished = True
                st.session_state.cap_phase = "result"
                st.rerun()

        # ================= 阶段 3: 比赛结果与败者淘汰环节 =================
        elif st.session_state.cap_phase == "result" and st.session_state.cap_match_finished:
            res = st.session_state.cap_last_match_result
            st.subheader(f" 第 {st.session_state.cap_round} 局  比赛最终结果")

            st.markdown("####  赛后揭晓：本场 AI 指派的最强首发五虎阵容：")
            st.dataframe(players_to_dict_list(res["calc_ai_team"]), use_container_width=True)

            rc1, rc2 = st.columns(2)
            rc1.metric(" 你的得分", f"{res['p_score']} 分", f"战力合计: {res['p_base']}")
            rc2.metric(" AI 得分", f"{res['ai_score']} 分", f"战力合计: {res['ai_base']}")

            if res["match_res"] == "胜利":
                st.balloons()
                st.success(f" 恭喜！你赢得了第 {st.session_state.cap_round} 局比赛！获得资金 **+$4**，AI 获得 **+$2**。")
            else:
                st.error(f" 很遗憾，你在第 {st.session_state.cap_round} 局比赛中落败！AI 获得 **+$4**，你获得 **+$2**。")

            st.divider()

            if res["match_res"] == "失败":
                st.warning(" **【资本家惩罚】作为本局败者，你必须从当局首发阵容中裁掉（淘汰）一名球员！**")
                discard_names = [f"{p.name} [{getattr(p, 'position', '未知')}] ({p.rating}分)" for p in res["calc_p_team"]]
                sel_discard = st.selectbox("选择要裁掉的首发球员：", discard_names, key="discard_player_select")
                
                if st.button(" 确认裁掉该球员并进入下一局", type="primary"):
                    target_name = sel_discard.split(" [")[0]
                    target_obj = next((p for p in st.session_state.cap_player_roster if p.name == target_name), None)
                    if target_obj:
                        st.session_state.cap_player_roster.remove(target_obj)
                    
                    st.session_state.cap_round += 1
                    st.session_state.cap_phase = "actions"
                    st.session_state.cap_p_actions_count = 0
                    st.session_state.cap_bribe_p = False
                    st.session_state.cap_bribe_ai = False
                    st.session_state.cap_encouraged_p = []
                    st.session_state.cap_encouraged_ai = []
                    st.session_state.cap_item_p = None
                    st.session_state.cap_item_ai = None
                    st.session_state.cap_match_finished = False
                    st.session_state.cap_last_match_result = None
                    for pos in POSITIONS:
                        st.session_state.pop(f"cap_p_slot_{pos}", None)
                    st.rerun()
            else:
                st.info(" 你赢得了本局比赛，AI 作为败者需要裁掉一名其当局首发球员！")
                ai_starters = res["calc_ai_team"]
                if ai_starters:
                    ai_starters.sort(key=lambda x: x.rating)
                    victim = ai_starters[0]
                    ai_real_victim = next((p for p in st.session_state.cap_ai_roster if p.name == victim.name), None)
                    if ai_real_victim and ai_real_victim in st.session_state.cap_ai_roster:
                        st.session_state.cap_ai_roster.remove(ai_real_victim)
                        st.write(f" AI 裁员通告：AI 阵中首发球员 **{ai_real_victim.name}** 被无情裁掉！")

                if st.button(" 进入下一局资本家之战", type="primary"):
                    st.session_state.cap_round += 1
                    st.session_state.cap_phase = "actions"
                    st.session_state.cap_p_actions_count = 0
                    st.session_state.cap_bribe_p = False
                    st.session_state.cap_bribe_ai = False
                    st.session_state.cap_encouraged_p = []
                    st.session_state.cap_encouraged_ai = []
                    st.session_state.cap_item_p = None
                    st.session_state.cap_item_ai = None
                    st.session_state.cap_match_finished = False
                    st.session_state.cap_last_match_result = None
                    for pos in POSITIONS:
                        st.session_state.pop(f"cap_p_slot_{pos}", None)
                    st.rerun()

# ----------------- 10. 数据保存 -----------------
elif menu == "💾 数据保存":
    st.header("💾 数据保存与导出")
    st.markdown("将当前最新的球员数据保存到对应的文本文件中。")
    
    filename_to_save = "alltimeplayers.txt" if st.session_state.player_mode == "Alltime" else "players.txt"
    
    if st.button(f"💾 保存当前修改到 {filename_to_save}", type="primary"):
        try:
            with open(filename_to_save, "w", encoding="utf-8") as f:
                for p in players:
                    pos = getattr(p, "position", "未知")
                    f.write(f"{p.name},{p.age},{p.team},{p.rating},{pos}\n")
            st.success(f"成功保存所有球员数据到 {filename_to_save}！")
        except Exception as e:
            st.error(f"保存失败: {e}")
