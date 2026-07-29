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
            # 切换回现役时，动态替换默认文件名再加载
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
            
            # 直接在 app.py 里读取 alltimeplayers.txt
            try:
                players = []
                with open("alltimeplayers.txt", "r", encoding="utf-8") as f:
                    for line in f:
                        # 如果你的 txt 每一行是一个球员对象、字典或者特定格式
                        # 请在这里写对应的解析代码，例如如果是逗号分隔或 eval：
                        # 比如：temp_players.append(eval(line.strip()))
                        pass # 请把这里换成你解析文件的实际逻辑
                st.session_state.players = players
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

        # 重置比赛状态
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

            # 蓝方自选
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

            # 红方自选
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

            # 初始化竞拍状态
            if "auction_inited" not in st.session_state or not st.session_state.auction_inited:
                st.session_state.blue_money = 20
                st.session_state.red_money = 20
                st.session_state.auction_blue_pool = []
                st.session_state.auction_red_pool = []
                st.session_state.current_target_player = None
                st.session_state.auction_logs = []
                st.session_state.current_bid = 0
                st.session_state.highest_bidder = None
                st.session_state.drawer = "blue"  # 初始抽取方
                st.session_state.turn = "blue"    # 当前应价方
                st.session_state.auction_inited = True

            if st.button("🔄 重置/重新开始拍卖"):
                st.session_state.auction_inited = False
                reset_match_state()
                st.rerun()

            auc_blue_pool = st.session_state.auction_blue_pool
            auc_red_pool = st.session_state.auction_red_pool

            # 顶部面板展示
            col_m1, col_m2 = st.columns(2)
            blue_full = len(auc_blue_pool) >= 5
            red_full = len(auc_red_pool) >= 5
            
            col_m1.metric("🔵 蓝方资金", f"${st.session_state.blue_money}", delta=f"手牌: {len(auc_blue_pool)}/5 {'(已满)' if blue_full else ''}")
            col_m2.metric("🔴 红方资金", f"${st.session_state.red_money}", delta=f"手牌: {len(auc_red_pool)}/5 {'(已满)' if red_full else ''}")

            # 实时已拍得球员清单
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

            # 检查竞拍是否进行（双方未同时满5张）
            if not (blue_full and red_full):
                used_players = set(auc_blue_pool + auc_red_pool)
                available_pool = [p for p in players if p not in used_players]
                high_rating_pool = [p for p in available_pool if p.rating >= 80]
                if not high_rating_pool:
                    high_rating_pool = available_pool  # 优质池若空则降级使用全池

                # 自动跳过已经满了 5 张的人
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

                # 1. 抽取/开价阶段
                if not st.session_state.current_target_player:
                    # 如果抽牌方资金为 0，或者对方手牌已满，直接 $0 免费抽牌
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
                        
                        # 免费抽取模式：不进行竞价，直接划归抽牌方
                        if is_free_draw:
                            if current_drawer == "blue":
                                st.session_state.auction_blue_pool.append(target)
                            else:
                                st.session_state.auction_red_pool.append(target)
                            st.session_state.auction_logs.append(f"{drawer_text} {reason} 以 **$0** 获得 **{target.name}**")
                            st.session_state.current_target_player = None
                            # 轮换给对方抽牌
                            st.session_state.drawer = other_side
                        else:
                            # 正常双人竞价流程
                            st.session_state.current_target_player = target
                            st.session_state.current_bid = 1
                            st.session_state.highest_bidder = current_drawer
                            st.session_state.turn = other_side
                        st.rerun()

                # 2. 竞价应价阶段
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
                        # 如果钱不够加价，禁用加价输入框和按钮
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
                            
                            # 换对方继续应价（前提是对方没满 5 张）
                            other = "red" if turn == "blue" else "blue"
                            other_team_len = len(st.session_state.auction_red_pool) if other == "red" else len(st.session_state.auction_blue_pool)
                            
                            if other_team_len < 5:
                                st.session_state.turn = other
                            else:
                                # 对方满 5 张，直接出价成功结算
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
                        # 放弃应价 (Pass)
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

            # 3. 拍卖结束后的位置布局阶段
            if len(auc_blue_pool) >= 5 and len(auc_red_pool) >= 5:
                st.divider()
                st.subheader("🧩 拍卖结束：请将已拍得球员放入阵容位置框架中")

                col_slot1, col_slot2 = st.columns(2)
                b_assigned = []
                r_assigned = []

                # 🔵 蓝方指派
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

                # 🔴 红方指派
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

            # 1. 道具定义与抽卡
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

            # 2. 应用道具修改
            blue_score_bonus = 0
            red_score_bonus = 0
            logs = []

            # 蓝方道具生效
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
                    logs.append("🗣️ 蓝方使用了 [嘴 - 喷垃圾话]，红方最终得分 -20")
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

            # 红方道具生效
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
                    logs.append("🗣️ 红方使用了 [嘴 - 喷垃圾话]，蓝方最终得分 -20")
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

            # 3. 最终展示更新后的阵容
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("🔵 蓝方首发五虎（包含位置折损与道具影响）")
                st.dataframe(players_to_dict_list(calc_blue_team), use_container_width=True)
                blue_base_score = sum(p.rating for p in calc_blue_team)
                st.info(f"修正后总战力：**{blue_base_score}** | 场上均分：**{blue_base_score/5:.1f}**")

            with c2:
                st.subheader("🔴 红方首发五虎（包含位置折损与道具影响）")
                st.dataframe(players_to_dict_list(calc_red_team), use_container_width=True)
                red_base_score = sum(p.rating for p in calc_red_team)
                st.info(f"修正后总战力：**{red_base_score}** | 场上均分：**{red_base_score/5:.1f}**")

            st.divider()

            # 4. 模拟比赛比分计算
            if st.button("🚀 开启模拟对决！", type="primary"):
                # 1) 计算包含手感波动与道具修正后的“原始战力得分”
                blue_luck = random.uniform(0.88, 1.12)
                red_luck = random.uniform(0.88, 1.12)
                
                raw_blue_score = int(blue_base_score * blue_luck) + blue_score_bonus
                raw_red_score = int(red_base_score * red_luck) + red_score_bonus

                # 确保战力不为负数
                raw_blue_score = max(10, raw_blue_score)
                raw_red_score = max(10, raw_red_score)

                # 2) 比例映射到真实的比赛比分范围（标准单场总分在 195~225 分左右，即单队 100 分上下）
                game_base_total = random.randint(195, 225) 
                
                # 按战力比例等比例缩小计算真实赛场得分
                real_blue_score = round(game_base_total * (raw_blue_score / (raw_blue_score + raw_red_score)))
                real_red_score = game_base_total - real_blue_score

                # 防止同分（如果是平局，随机让某方绝杀）
                if real_blue_score == real_red_score:
                    if raw_blue_score > raw_red_score:
                        real_blue_score += random.choice([2, 3])
                    elif raw_red_score > raw_blue_score:
                        real_red_score += random.choice([2, 3])
                    else:
                        real_blue_score += random.choice([1, 2])

                st.subheader("📊 比赛最终比分")
                
                # 展示【真实赛场比分】（重点展示）与原始战力折算、手感波动标签
                res_col1, res_col2 = st.columns(2)
                res_col1.metric(
                    "🔵 蓝方赛场最终得分", 
                    f"{real_blue_score} 分", 
                    delta=f"手感: {blue_luck:.0%} | 原始战力折算: {raw_blue_score}"
                )
                res_col2.metric(
                    "🔴 红方赛场最终得分", 
                    f"{real_red_score} 分", 
                    delta=f"手感: {red_luck:.0%} | 原始战力折算: {raw_red_score}"
                )

                st.caption(f"💡 赛场真实比分由双方包含手感波动的总战力（蓝 {raw_blue_score} vs 红 {raw_red_score}）等比例映射缩放得出。")

                # 判定胜负
                if real_blue_score > real_red_score:
                    st.balloons()
                    st.success(f"🏆 恭喜！🔵 蓝方以 **{real_blue_score} : {real_red_score}** 赢得了这场 5v5 斗牛赛！")
                elif real_blue_score < real_red_score:
                    st.balloons()
                    st.error(f"🏆 恭喜！🔴 红方以 **{real_red_score} : {real_blue_score}** 赢得了这场 5v5 斗牛赛！")

        else:
            st.info("💡 请将 5 个位置槽位全部选满，自动汇总计算位置折损并生成对战")

# ----------------- 7. 数据保存 -----------------
elif menu == "💾 数据保存":
    st.header("💾 数据保存")
    current_filename = "alltimeplayers.txt" if st.session_state.player_mode == "Alltime" else "players.txt"
    st.write(f"点击下方按钮把当前网页中的修改保存回文件中（当前保存目标：**{current_filename}**）：")
    if st.button("💾 保存数据", type="primary"):
        utils.save_players(players, current_filename)
        st.success(f"数据已成功保存到本地 {current_filename}！")
