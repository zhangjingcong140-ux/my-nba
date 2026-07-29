import streamlit as st
import random
import untils
from player import Player

# 頁面基礎配置
st.set_page_config(page_title="NBA 球員管理系統", page_icon="🏀", layout="wide")

# 初始化數據到 Session State（確保網頁刷新後數據不丟失）
if "players" not in st.session_state:
    st.session_state.players = untils.load_players()

players = st.session_state.players

st.title("🏀 NBA 球員交易與管理系統")

# 側邊欄菜單分類
menu = st.sidebar.radio(
    "功能導航",
    [
        "📋 球員列表與查詢",
        "➕ 添加與刪除",
        "⚙️ 修改與交易",
        "📊 數據統計與分析",
        "🔀 排序與展示",
        "🏀 5v5 鬥牛對決",
        "💾 數據保存"
    ]
)

# 輔助函數：把 Player 列表轉成標準字典，方便 Streamlit 美化表格
def players_to_dict_list(player_list):
    return [
        {
            "姓名": p.name,
            "年齡": p.age,
            "球隊": p.team,
            "能力值": p.rating
        }
        for p in player_list
    ]

# ----------------- 1. 球員列表與查詢 -----------------
if menu == "📋 球員列表與查詢":
    st.header("📋 球員列表與模糊查詢")
    
    col1, col2 = st.columns(2)
    with col1:
        search_part = st.text_input("🔍 搜索球員全名/部分名字（對應功能 10）：")
    with col2:
        search_team = st.text_input("🏟️ 搜索球隊查看信息（對應功能 15）：")

    if search_part:
        st.subheader("搜索結果")
        matched = [p for p in players if search_part.lower() in p.name.lower()]
        if matched:
            st.dataframe(players_to_dict_list(matched), use_container_width=True)
        else:
            st.warning("未匹配到相關球員。")

    elif search_team:
        st.subheader(f"球隊 '{search_team}' 信息")
        team_players = [p for p in players if search_team.lower() in p.team.lower()]
        if team_players:
            st.dataframe(players_to_dict_list(team_players), use_container_width=True)
            high_rating_players = [p for p in team_players if p.rating > 75]
            if high_rating_players:
                avg = sum(p.rating for p in high_rating_players) / len(high_rating_players)
                st.info(f"🏀 該球隊能力值 >75 的球員平均能力值為：**{avg:.2f}**")
        else:
            st.warning("未找到該球隊信息。")

    else:
        st.subheader("全部球員列表")
        st.dataframe(players_to_dict_list(players), use_container_width=True)

# ----------------- 2. 添加與刪除 -----------------
elif menu == "➕ 添加與刪除":
    st.header("➕ 添加 / 🗑️ 刪除球員")
    
    tab1, tab2 = st.tabs(["添加新球員", "刪除球員"])
    
    with tab1:
        with st.form("add_player_form"):
            name = st.text_input("球員姓名：")
            age = st.number_input("年齡：", min_value=15, max_value=50, value=20)
            team = st.text_input("球隊：")
            rating = st.number_input("能力值 (50-99)：", min_value=50, max_value=99, value=75)
            submit = st.form_submit_button("確認添加")
            
            if submit:
                if not name or not team:
                    st.error("姓名和球隊不能為空！")
                else:
                    new_player = Player(name, age, team, rating)
                    players.append(new_player)
                    st.success(f"成功添加球員：{name}")

    with tab2:
        del_name = st.text_input("輸入要刪除的球員姓名：")
        if st.button("確認刪除"):
            p_found = untils.find_player(players, del_name)
            if p_found:
                players.remove(p_found)
                st.success(f"已刪除球員：{p_found.name}")
            else:
                st.error("未找到該球員！")

# ----------------- 3. 修改與交易 -----------------
elif menu == "⚙️ 修改與交易":
    st.header("⚙️ 修改能力值 / 🔄 球員交易")
    
    tab1, tab2 = st.tabs(["修改能力值", "球員交易"])
    
    with tab1:
        mod_name = st.text_input("輸入要修改能力值的球員姓名：")
        p_target = untils.find_player(players, mod_name) if mod_name else None
        
        if p_target:
            st.info(f"當前球員：{p_target.name} | 當前能力值：{p_target.rating}")
            action = st.radio("選擇操作：", ["增加能力值", "減少能力值"])
            amount = st.number_input("調整數值：", min_value=1, max_value=50, value=1)
            
            if st.button("提交修改"):
                try:
                    if action == "增加能力值":
                        p_target.increase_rating(amount)
                    else:
                        p_target.decrease_rating(amount)
                    st.success(f"修改成功！{p_target.name} 當前能力值為：{p_target.rating}")
                except ValueError as e:
                    st.error(f"錯誤：{e}")
        elif mod_name:
            st.warning("未找到該球員。")

    with tab2:
        trade_player_name = st.text_input("選擇要交易的球員姓名（模糊匹配）：")
        target_team_name = st.text_input("選擇目標球隊（模糊匹配）：")
        
        if st.button("執行交易"):
            fteam = None
            for p in players:
                if target_team_name.lower() in p.team.lower():
                    fteam = p.team
                    break
            
            if fteam is None:
                st.error("未找到目標球隊！")
            else:
                player_found = False
                for p in players:
                    if trade_player_name.lower() in p.name.lower():
                        p.team = fteam
                        player_found = True
                        st.success(f"🎉 交易成功！{p.name} 已轉會至 **{fteam}**")
                if not player_found:
                    st.error("未找到交易球員！")

# ----------------- 4. 數據統計與分析 -----------------
elif menu == "📊 數據統計與分析":
    st.header("📊 數據統計與極限分析")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if players:
            avg_all = sum(p.rating for p in players) / len(players)
            st.metric("所有球員平均能力值", f"{avg_all:.2f}")
            
    with col2:
        if players:
            best_p = max(players, key=lambda p: p.rating)
            st.metric("🏆 最高能力值球員", f"{best_p.name} ({best_p.rating})")

    with col3:
        if players:
            youngest_p = min(players, key=lambda p: p.age)
            st.metric("👶 最年輕球員", f"{youngest_p.name} ({youngest_p.age}歲)")
            
    st.divider()
    
    st.subheader("⭐ 傳奇球員 (Rating >= 95)")
    legend_players = [p for p in players if p.rating >= 95]
    if legend_players:
        st.dataframe(players_to_dict_list(legend_players), use_container_width=True)
        if st.button("📥 導出傳奇球員到 LegendPlayers.txt（功能 11）"):
            with open("LegendPlayers.txt", "w") as f:
                for p in legend_players:
                    f.write(f"{p.name},{p.age},{p.team},{p.rating}\n")
            st.success("成功導出 LegendPlayers.txt！")
    else:
        st.write("暫無傳奇球員。")

    st.divider()

    st.subheader("📈 各隊伍平均評分排行榜")
    team_data = {}
    for p in players:
        t_name = p.team
        if t_name not in team_data:
            team_data[t_name] = [0, 0]
        team_data[t_name][0] += 1
        team_data[t_name][1] += p.rating
    
    team_averages = {t: info[1]/info[0] for t, info in team_data.items()}
    sorted_teams = sorted(team_averages.items(), key=lambda x: x[1], reverse=True)
    st.table([{"球隊": t, "平均能力值": f"{avg:.2f}"} for t, avg in sorted_teams])

# ----------------- 5. 排序與展示 -----------------
elif menu == "🔀 排序與展示":
    st.header("🔀 排序與特色展示")
    
    sub_option = st.selectbox(
        "選擇功能",
        [
            "能力值升序 (功能 6-1)",
            "能力值降序 (功能 6-2)",
            "按年齡升序 (功能 6-3)",
            "查看年輕球員 (Age <= 22) (功能 7)",
            "所有球員名字大寫 (功能 8)",
            "🎲 隨機抽取全池一位球員 (功能 9)",
            "🌟 隨機抽取優質球員 (Rating >= 80)",
            "按隊伍後綴排序 (功能 16)"
        ]
    )

    if sub_option == "能力值升序 (功能 6-1)":
        players.sort(key=lambda p: p.rating)
        st.dataframe(players_to_dict_list(players), use_container_width=True)

    elif sub_option == "能力值降序 (功能 6-2)":
        players.sort(key=lambda p: p.rating, reverse=True)
        st.dataframe(players_to_dict_list(players), use_container_width=True)

    elif sub_option == "按年齡升序 (功能 6-3)":
        players.sort(key=lambda p: p.age)
        st.dataframe(players_to_dict_list(players), use_container_width=True)

    elif sub_option == "查看年輕球員 (Age <= 22) (功能 7)":
        young_players = list(filter(lambda p: p.age <= 22, players))
        st.dataframe(players_to_dict_list(young_players), use_container_width=True)

    elif sub_option == "所有球員名字大寫 (功能 8)":
        names_upper = list(map(lambda p: p.name.upper(), players))
        st.write(names_upper)

    elif sub_option == "🎲 隨機抽取全池一位球員 (功能 9)":
        if st.button("開始抽卡！"):
            chosen = random.choice(players)
            st.balloons()
            st.success(f"🎉 抽中的球員是：**{chosen.name}** | 球隊：{chosen.team} | 能力值：{chosen.rating}")

    elif sub_option == "🌟 隨機抽取優質球員 (Rating >= 80)":
        high_rating_pool = [p for p in players if p.rating >= 80]
        st.caption(f"當前全庫共有 **{len(high_rating_pool)}** 位能力值 $\ge$ 80 的優質球員。")
        
        if st.button("🌟 抽取精銳球員！"):
            if high_rating_pool:
                chosen = random.choice(high_rating_pool)
                st.balloons()
                st.success(f"🔥 歐氣爆發！抽中優質球員：**{chosen.name}** | 球隊：{chosen.team} | 能力值：**{chosen.rating}**")
            else:
                st.warning("⚠️ 當前沒有能力值 $\ge$ 80 的球員，快去添加或修改球員能力值吧！")

    elif sub_option == "按隊伍後綴排序 (功能 16)":
        players.sort(key=lambda p: p.team.split()[-1])
        st.dataframe(players_to_dict_list(players), use_container_width=True)

# ----------------- 6. 🏀 5v5 鬥牛對決（限制抽一次 + 防快取錯） -----------------
elif menu == "🏀 5v5 鬥牛對決":
    st.header("🏀 5v5 陣容鬥牛模擬器")
    st.caption("綜合評分決定戰力，支持賽前抽選隨機Buff/Debuff道具與對決模擬！")

    if len(players) < 10:
        st.error("⚠️ 球員總數不足 10 人，無法開啟 5v5 鬥牛，請先添加更多球員！")
    else:
        battle_mode = st.radio("選擇鬥牛模式：", ["🔥 盲盒抽卡 5v5", "🎯 自選陣容 5v5"], horizontal=True)
        
        player_dict = {f"{p.name} ({p.team} - {p.rating}分)": p for p in players}
        player_names = list(player_dict.keys())

        my_team = []
        opp_team = []

        if battle_mode == "🔥 盲盒抽卡 5v5":
            if st.button("🎲 一鍵隨機抽取雙方 5v5 陣容！"):
                selected_10 = random.sample(players, 10)
                st.session_state.my_team = selected_10[:5]
                st.session_state.opp_team = selected_10[5:]
                # 重新生成陣容時，重置道具和抽取次數限制
                st.session_state.pop("my_item", None)
                st.session_state.pop("opp_item", None)
                st.session_state.my_drawn = False
                st.session_state.opp_drawn = False

            if "my_team" in st.session_state and "opp_team" in st.session_state:
                my_team = st.session_state.my_team
                opp_team = st.session_state.opp_team

        elif battle_mode == "🎯 自選陣容 5v5":
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("🔵 我方陣容（選5位）")
                my_selected_names = st.multiselect("挑選我方首發：", player_names, max_selections=5, key="my_select")
                my_team = [player_dict[name] for name in my_selected_names]

            with col_b:
                st.subheader("🔴 敵方陣容（選5位）")
                remaining_names = [n for n in player_names if n not in my_selected_names]
                opp_selected_names = st.multiselect("挑選敵方首發：", remaining_names, max_selections=5, key="opp_select")
                opp_team = [player_dict[name] for name in opp_selected_names]

            # 當自選陣容發生改變時，如果未滿5人，可重置狀態
            if len(my_team) != 5 or len(opp_team) != 5:
                st.session_state.pop("my_item", None)
                st.session_state.pop("opp_item", None)
                st.session_state.my_drawn = False
                st.session_state.opp_drawn = False

        # 展示雙方陣容與比賽流程
        if len(my_team) == 5 and len(opp_team) == 5:
            st.divider()
            
            # 初始化抽取狀態標記
            if "my_drawn" not in st.session_state:
                st.session_state.my_drawn = False
            if "opp_drawn" not in st.session_state:
                st.session_state.opp_drawn = False

            # 道具池定義
            items_pool = [
                {"name": "🧪 佳得樂", "desc": "佳得樂補充體力", "effect_detail": "⚡ 效果：最終得分 +10", "effect": "self_add_10"},
                {"name": "🎮 遊戲機", "desc": "昨晚打遊戲", "effect_detail": "💤 效果：最終得分 -10", "effect": "self_sub_10"},
                {"name": "👁️ 紅色的眼睛", "desc": "全員覺醒", "effect_detail": "🔥 效果：最終得分 +20", "effect": "self_add_20"},
                {"name": "🍾 酒瓶", "desc": "昨晚夜店喝酒", "effect_detail": "😵 效果：最終得分 -20", "effect": "self_sub_20"},
                {"name": "👄 嘴", "desc": "噴垃圾話", "effect_detail": "💢 效果：對方最終得分 -20", "effect": "opp_sub_20"},
                {"name": "🦶 腳", "desc": "墊腳", "effect_detail": "🚑 效果：對方評分最高的球員能力值變為 80", "effect": "ankle_breaker"}
            ]

            # ----------------- 🎁 抽道具環節 -----------------
            st.subheader("🎁 賽前隨機抽取道具事件（每局限抽一次）")
            col_item1, col_item2 = st.columns(2)

            with col_item1:
                # 抽過後按鈕自動禁用 disabled=True
                btn_my = st.button("🎲 我方抽取賽前道具", disabled=st.session_state.my_drawn, key="btn_my_draw")
                if btn_my:
                    st.session_state.my_item = random.choice(items_pool)
                    st.session_state.my_drawn = True
                    st.rerun()

                if "my_item" in st.session_state and st.session_state.my_drawn:
                    item = st.session_state.my_item
                    st.success(f"🔵 **我方抽到：[{item.get('name', '道具')}]**（{item.get('desc', '')}）")
                    st.caption(f"{item.get('effect_detail', '⚡ 效果已生效')}")

            with col_item2:
                # 抽過後按鈕自動禁用 disabled=True
                btn_opp = st.button("🎲 敵方抽取賽前道具", disabled=st.session_state.opp_drawn, key="btn_opp_draw")
                if btn_opp:
                    st.session_state.opp_item = random.choice(items_pool)
                    st.session_state.opp_drawn = True
                    st.rerun()

                if "opp_item" in st.session_state and st.session_state.opp_drawn:
                    item = st.session_state.opp_item
                    st.error(f"🔴 **敵方抽到：[{item.get('name', '道具')}]**（{item.get('desc', '')}）")
                    st.caption(f"{item.get('effect_detail', '⚡ 效果已生效')}")

            st.divider()

            # 複製陣容進行計算
            calc_my_team = [Player(p.name, p.age, p.team, p.rating) for p in my_team]
            calc_opp_team = [Player(p.name, p.age, p.team, p.rating) for p in opp_team]

            my_score_bonus = 0
            opp_score_bonus = 0
            logs = []

            # 結算我方道具
            if "my_item" in st.session_state and st.session_state.my_drawn:
                eff = st.session_state.my_item.get("effect", "")
                if eff == "self_add_10":
                    my_score_bonus += 10
                elif eff == "self_sub_10":
                    my_score_bonus -= 10
                elif eff == "self_add_20":
                    my_score_bonus += 20
                elif eff == "self_sub_20":
                    my_score_bonus -= 20
                elif eff == "opp_sub_20":
                    opp_score_bonus -= 20
                    logs.append("🗣️ 我方使用了 [嘴 - 噴垃圾話]，敵方最終得分 -20！")
                elif eff == "ankle_breaker":
                    top_opp = max(calc_opp_team, key=lambda p: p.rating)
                    old_r = top_opp.rating
                    top_opp.rating = 80
                    logs.append(f"🦶 我方使用了 [腳 - 墊腳]！敵方最高能力值球員 **{top_opp.name}** 能力值從 {old_r} 降至 **80**！")

            # 結算敵方道具
            if "opp_item" in st.session_state and st.session_state.opp_drawn:
                eff = st.session_state.opp_item.get("effect", "")
                if eff == "self_add_10":
                    opp_score_bonus += 10
                elif eff == "self_sub_10":
                    opp_score_bonus -= 10
                elif eff == "self_add_20":
                    opp_score_bonus += 20
                elif eff == "self_sub_20":
                    opp_score_bonus -= 20
                elif eff == "opp_sub_20":
                    my_score_bonus -= 20
                    logs.append("🗣️ 敵方使用了 [嘴 - 噴垃圾話]，我方最終得分 -20！")
                elif eff == "ankle_breaker":
                    top_my = max(calc_my_team, key=lambda p: p.rating)
                    old_r = top_my.rating
                    top_my.rating = 80
                    logs.append(f"🦶 敵方使用了 [腳 - 墊腳]！我方最高能力值球員 **{top_my.name}** 能力值從 {old_r} 降至 **80**！")

            # 展現陣容
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("🔵 我方首發五虎")
                st.dataframe(players_to_dict_list(calc_my_team), use_container_width=True)
                my_base_score = sum(p.rating for p in calc_my_team)
                st.info(f"基礎戰力（總綜評）：**{my_base_score}** | 均分：**{my_base_score/5:.1f}**")

            with c2:
                st.subheader("🔴 敵方首發五虎")
                st.dataframe(players_to_dict_list(calc_opp_team), use_container_width=True)
                opp_base_score = sum(p.rating for p in calc_opp_team)
                st.info(f"基礎戰力（總綜評）：**{opp_base_score}** | 均分：**{opp_base_score/5:.1f}**")

            if logs:
                st.warning("⚠️ **賽前特殊事件生效：**\n\n" + "\n\n".join(logs))

            st.divider()
            
            if st.button("🚀 開啟模擬對決！", type="primary"):
                my_luck = random.uniform(0.88, 1.12)
                opp_luck = random.uniform(0.88, 1.12)
                
                my_final_score = int(my_base_score * my_luck) + my_score_bonus
                opp_final_score = int(opp_base_score * opp_luck) + opp_score_bonus

                st.subheader("📊 比賽最終比分")
                res_col1, res_col2 = st.columns(2)
                res_col1.metric("🔵 我方得分", my_final_score, delta=f"手感修正: {my_luck*100:.1f}% | 道具修正: {my_score_bonus:+d}")
                res_col2.metric("🔴 敵方得分", opp_final_score, delta=f"手感修正: {opp_luck*100:.1f}% | 道具修正: {opp_score_bonus:+d}")

                if my_final_score > opp_final_score:
                    st.balloons()
                    st.success(f"🏆 恭喜！我方以 **{my_final_score} : {opp_final_score}** 贏得了這場 5v5 鬥牛賽！")
                elif my_final_score < opp_final_score:
                    st.error(f"💔 遺憾！敵方以 **{opp_final_score} : {my_final_score}** 拿下了勝利。")
                else:
                    st.warning(f"🤝 雙方手感平平，以 **{my_final_score} : {opp_final_score}** 打成平手！")
        else:
            if battle_mode == "🎯 自選陣容 5v5":
                st.warning("💡 請在左右兩側各選滿 5 名球員以啟動比賽模擬！")

# ----------------- 7. 數據保存 -----------------
elif menu == "💾 數據保存":
    st.header("💾 數據保存 (功能 19)")
    st.write("點擊下方按鈕把當前網頁中的修改保存回文件中：")
    if st.button("💾 保存數據", type="primary"):
        untils.save_players(players)
        st.success("數據已成功保存到本地！")
