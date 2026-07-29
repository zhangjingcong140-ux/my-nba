import streamlit as st
import pandas as pd
import random
import copy

# ==========================================
# 1. 基础配置与常量定义
# ==========================================
st.set_page_config(page_title="NBA 5v5 斗牛模拟器", page_icon="🏀", layout="wide")

# 标准五个位置
POSITIONS = ["PG", "SG", "SF", "PF", "C"]
POSITION_INDEX = {pos: i for i, pos in enumerate(POSITIONS)}

# 六维基础属性列表
ATTRIBUTES = ["得分", "三分", "扣篮", "防守", "篮板", "组织"]

# 默认位置属性权重配置
DEFAULT_WEIGHTS = {
    "PG": {"得分": 0.15, "三分": 0.20, "扣篮": 0.05, "防守": 0.15, "篮板": 0.05, "组织": 0.40},
    "SG": {"得分": 0.30, "三分": 0.30, "扣篮": 0.10, "防守": 0.15, "篮板": 0.05, "组织": 0.10},
    "SF": {"得分": 0.25, "三分": 0.20, "扣篮": 0.15, "防守": 0.20, "篮板": 0.10, "组织": 0.10},
    "PF": {"得分": 0.20, "三分": 0.10, "扣篮": 0.20, "防守": 0.20, "篮板": 0.25, "组织": 0.05},
    "C":  {"得分": 0.15, "三分": 0.05, "扣篮": 0.25, "防守": 0.25, "篮板": 0.25, "组织": 0.05},
}

# 道具库列表
BUFF_CARDS = [
    {"name": "☕ 状态极佳", "effect": "rating_boost", "val": 5, "desc": "全队能力值统一 +5 分"},
    {"name": "🤕 主力拉伤", "effect": "rating_nerf", "val": -5, "desc": "全队能力值统一 -5 分"},
    {"name": "🚽 教练上厕所", "effect": "swap_positions", "val": 0, "desc": "随机交换两个位置的球员，并根据新位置扣除偏离分数"},
    {"name": "🔥 战术大师", "effect": "ignore_penalty", "val": 0, "desc": "全队无视位置偏离惩罚（恢复原始加权评分）"},
    {"name": "🎯 绝杀时刻", "effect": "clutch_boost", "val": 10, "desc": "全队主力得分手能力值额外 +10 分"}
]

# ==========================================
# 2. 数据结构定义与初始化
# ==========================================
class Player:
    def __init__(self, name, position, scores, price=10):
        self.name = name
        self.position = position  # 原始偏好位置
        self.scores = scores      # 字典: {"得分": 80, ...}
        self.price = price
        self.rating = 0.0         # 动态能力值

    def calculate_rating(self, weight_dict):
        """根据当前偏好位置计算基础加权评分"""
        w = weight_dict.get(self.position, DEFAULT_WEIGHTS[self.position])
        score = sum(self.scores[attr] * w[attr] for attr in ATTRIBUTES)
        self.rating = round(score, 1)
        return self.rating

# 预设初始球员库
DEFAULT_PLAYERS = [
    Player("库里", "PG", {"得分": 95, "三分": 99, "扣篮": 40, "防守": 75, "篮板": 60, "组织": 92}, 35),
    Player("哈登", "SG", {"得分": 92, "三分": 88, "扣篮": 75, "防守": 70, "篮板": 70, "组织": 95}, 32),
    Player("詹姆斯", "SF", {"得分": 90, "三分": 80, "扣篮": 92, "防守": 85, "篮板": 82, "组织": 90}, 38),
    Player("字母哥", "PF", {"得分": 88, "三分": 60, "扣篮": 98, "防守": 92, "篮板": 92, "组织": 75}, 36),
    Player("约基奇", "C",  {"得分": 92, "三分": 82, "扣篮": 65, "防守": 80, "篮板": 95, "组织": 98}, 39),
    Player("欧文", "PG", {"得分": 90, "三分": 88, "扣篮": 65, "防守": 65, "篮板": 50, "组织": 85}, 28),
    Player("克莱", "SG", {"得分": 82, "三分": 90, "扣篮": 60, "防守": 80, "篮板": 55, "组织": 60}, 22),
    Player("杜兰特", "SF", {"得分": 95, "三分": 90, "扣篮": 85, "防守": 82, "篮板": 75, "组织": 75}, 35),
    Player("戴维斯", "PF", {"得分": 86, "三分": 65, "扣篮": 88, "防守": 95, "篮板": 90, "组织": 60}, 33),
    Player("恩比德", "C",  {"得分": 92, "三分": 75, "扣篮": 85, "防守": 88, "篮板": 90, "组织": 65}, 34),
]

# 初始化 Session State
if "players" not in st.session_state:
    st.session_state.players = DEFAULT_PLAYERS

if "position_weights" not in st.session_state:
    st.session_state.position_weights = copy.deepcopy(DEFAULT_WEIGHTS)

# ==========================================
# 3. 核心计算函数
# ==========================================
def calculate_position_penalty(player, assigned_position):
    """计算位置错位惩罚（每偏离 1 级扣 2 分）"""
    orig_idx = POSITION_INDEX[player.position]
    assign_idx = POSITION_INDEX[assigned_position]
    diff = abs(orig_idx - assign_idx)
    penalty = diff * 2.0
    return penalty, diff

def get_player_effective_rating(player, assigned_position, weights):
    """获取球员在特定位置上的最终加权能力值（含惩罚扣分）"""
    w = weights.get(assigned_position, DEFAULT_WEIGHTS[assigned_position])
    base_rating = sum(player.scores[attr] * w[attr] for attr in ATTRIBUTES)
    penalty, _ = calculate_position_penalty(player, assigned_position)
    return max(0.0, round(base_rating - penalty, 1))

# ==========================================
# 4. Streamlit 页面布局
# ==========================================
st.title("🏀 NBA 5v5 斗牛模拟系统")
st.markdown("---")

menu = st.sidebar.radio("📌 导航菜单", ["📋 球员数据库", "⚙️ 位置权重设置", "⚔️ 5v5 斗牛对决"])

# ------------------------------------------
# 菜单 1：球员数据库
# ------------------------------------------
if menu == "📋 球员数据库":
    st.header("📋 球员数据库管理")
    
    # 1.1 添加新球员
    with st.expander("➕ 添加新球员", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            new_name = st.text_input("球员姓名", value="新球员")
            new_pos = st.selectbox("偏好位置", POSITIONS)
            new_price = st.number_input("身价 (万)", min_value=1, max_value=100, value=15)
        
        scores_input = {}
        with col2:
            scores_input["得分"] = st.slider("得分", 0, 100, 75)
            scores_input["三分"] = st.slider("三分", 0, 100, 70)
            scores_input["扣篮"] = st.slider("扣篮", 0, 100, 65)
        with col3:
            scores_input["防守"] = st.slider("防守", 0, 100, 70)
            scores_input["篮板"] = st.slider("篮板", 0, 100, 65)
            scores_input["组织"] = st.slider("组织", 0, 100, 70)
            
        if st.button("提交添加"):
            p = Player(new_name, new_pos, scores_input, new_price)
            p.calculate_rating(st.session_state.position_weights)
            st.session_state.players.append(p)
            st.success(f"成功添加球员：{new_name}！")
            st.rerun()

    # 1.2 展示球员数据表格
    st.subheader("当前球员列表")
    data_list = []
    for p in st.session_state.players:
        p.calculate_rating(st.session_state.position_weights)
        row = {
            "姓名": p.name,
            "偏好位置": p.position,
            "身价(万)": p.price,
            "基础能力值": p.rating,
            **p.scores
        }
        data_list.append(row)
    
    df = pd.DataFrame(data_list)
    st.dataframe(df, use_container_width=True)

# ------------------------------------------
# 菜单 2：位置权重设置
# ------------------------------------------
elif menu == "⚙️ 位置权重设置":
    st.header("⚙️ 各位置评分权重设置")
    st.info("调整各个位置在计算整体能力值时的属性占比，总和应为 1.0 (100%)。")
    
    selected_pos = st.selectbox("选择要修改的位置", POSITIONS)
    cur_w = st.session_state.position_weights[selected_pos]
    
    col1, col2 = st.columns(2)
    new_w = {}
    with col1:
        new_w["得分"] = st.slider("得分权重", 0.0, 1.0, float(cur_w["得分"]), 0.05)
        new_w["三分"] = st.slider("三分权重", 0.0, 1.0, float(cur_w["三分"]), 0.05)
        new_w["扣篮"] = st.slider("扣篮权重", 0.0, 1.0, float(cur_w["扣篮"]), 0.05)
    with col2:
        new_w["防守"] = st.slider("防守权重", 0.0, 1.0, float(cur_w["防守"]), 0.05)
        new_w["篮板"] = st.slider("篮板权重", 0.0, 1.0, float(cur_w["篮板"]), 0.05)
        new_w["组织"] = st.slider("组织权重", 0.0, 1.0, float(cur_w["组织"]), 0.05)
        
    total_w = sum(new_w.values())
    st.write(f"**当前权重总和：** `{total_w:.2f}`")
    
    if abs(total_w - 1.0) > 0.001:
        st.warning("⚠️ 权重总和建议等于 1.0！")
        
    if st.button("保存当前位置权重"):
        st.session_state.position_weights[selected_pos] = new_w
        st.success(f"{selected_pos} 位置权重已成功更新！")

# ------------------------------------------
# 菜单 3：5v5 斗牛对决
# ------------------------------------------
elif menu == "⚔️ 5v5 斗牛对决":
    st.header("⚔️ 5v5 斗牛对决模拟")
    
    if len(st.session_state.players) < 10:
        st.error("数据库中球员少于 10 名，请先在【球员数据库】中添加足够的球员！")
        st.stop()
        
    # 模式选择
    team_mode = st.radio("组队方式", ["🎲 随机自动组队", "🖐️ 手动指定首发"], horizontal=True)
    
    blue_team = []
    red_team = []
    
    if team_mode == "🎲 随机自动组队":
        if st.button("🔀 重新随机生成阵容"):
            st.session_state.pop("blue_selection", None)
            st.session_state.pop("red_selection", None)
            
        sampled_players = random.sample(st.session_state.players, 10)
        blue_team = sampled_players[:5]
        red_team = sampled_players[5:]
        
    else:  # 手动选择
        col_b, col_r = st.columns(2)
        all_p_names = [p.name for p in st.session_state.players]
        
        with col_b:
            st.subheader("🔵 蓝方阵容 (PG, SG, SF, PF, C)")
            b_selected = []
            for pos in POSITIONS:
                p_name = st.selectbox(f"蓝方 {pos}", all_p_names, key=f"blue_{pos}")
                p_obj = next(p for p in st.session_state.players if p.name == p_name)
                b_selected.append(p_obj)
            blue_team = b_selected

        with col_r:
            st.subheader("🔴 红方阵容 (PG, SG, SF, PF, C)")
            r_selected = []
            for pos in POSITIONS:
                p_name = st.selectbox(f"红方 {pos}", all_p_names, key=f"red_{pos}")
                p_obj = next(p for p in st.session_state.players if p.name == p_name)
                r_selected.append(p_obj)
            red_team = r_selected

    st.markdown("---")
    
    # 开战模拟按钮
    if st.button("🔥 开始 5v5 斗牛模拟", type="primary", use_container_width=True):
        st.subheader("📊 比赛过程与计算日志")
        
        # 1. 深拷贝阵型对象用于独立计算
        calc_blue_team = [copy.deepcopy(p) for p in blue_team]
        calc_red_team = [copy.deepcopy(p) for p in red_team]
        
        # 预先计算每位球员在分配位置上的初始能力值（含惩罚）
        for i, pos in enumerate(POSITIONS):
            calc_blue_team[i].rating = get_player_effective_rating(calc_blue_team[i], pos, st.session_state.position_weights)
            calc_red_team[i].rating = get_player_effective_rating(calc_red_team[i], pos, st.session_state.position_weights)

        logs = []
        
        # 2. 随机抽卡/触发道具机制
        blue_buff = random.choice(BUFF_CARDS)
        red_buff = random.choice(BUFF_CARDS)
        
        logs.append(f"🔵 蓝方抽到道具卡：【{blue_buff['name']}】({blue_buff['desc']})")
        logs.append(f"🔴 红方抽到道具卡：【{red_buff['name']}】({red_buff['desc']})")
        
        # --- 应用蓝方道具效果 ---
        if blue_buff["effect"] == "rating_boost":
            for p in calc_blue_team:
                p.rating += blue_buff["val"]
        elif blue_buff["effect"] == "rating_nerf":
            for p in calc_blue_team:
                p.rating = max(0, p.rating + blue_buff["val"])
        elif blue_buff["effect"] == "ignore_penalty":
            for i, pos in enumerate(POSITIONS):
                calc_blue_team[i].calculate_rating(st.session_state.position_weights)
        elif blue_buff["effect"] == "clutch_boost":
            best_p = max(calc_blue_team, key=lambda x: x.scores["得分"])
            best_p.rating += blue_buff["val"]
            logs.append(f"   -> 蓝方王牌得分手【{best_p.name}】获得 +10 爆种加成！")
        elif blue_buff["effect"] == "swap_positions":
            # 1. 随机挑选两个位置索引
            idx1, idx2 = random.sample(range(5), 2)
            pos1, pos2 = POSITIONS[idx1], POSITIONS[idx2]
            
            # 2. 获取交换前的球员对象
            p1, p2 = calc_blue_team[idx1], calc_blue_team[idx2]
            
            # 3. 交换球员在阵容中的位置
            calc_blue_team[idx1], calc_blue_team[idx2] = p2, p1
            
            # 4. 【核心修复】为换位后的两人重新计算新位置的偏离惩罚并扣减能力值
            pen1, _ = calculate_position_penalty(calc_blue_team[idx1], pos1)
            pen2, _ = calculate_position_penalty(calc_blue_team[idx2], pos2)
            calc_blue_team[idx1].rating = max(0, calc_blue_team[idx1].rating - pen1)
            calc_blue_team[idx2].rating = max(0, calc_blue_team[idx2].rating - pen2)
            
            # 5. 记录日志
            logs.append(f"🚽 蓝方触发了 [教练上厕所]！阵型混乱，【{pos1} - {p1.name}】与【{pos2} - {p2.name}】互换了位置，并重新扣除了位置偏离分数！")

        # --- 应用红方道具效果 ---
        if red_buff["effect"] == "rating_boost":
            for p in calc_red_team:
                p.rating += red_buff["val"]
        elif red_buff["effect"] == "rating_nerf":
            for p in calc_red_team:
                p.rating = max(0, p.rating + red_buff["val"])
        elif red_buff["effect"] == "ignore_penalty":
            for i, pos in enumerate(POSITIONS):
                calc_red_team[i].calculate_rating(st.session_state.position_weights)
        elif red_buff["effect"] == "clutch_boost":
            best_p = max(calc_red_team, key=lambda x: x.scores["得分"])
            best_p.rating += red_buff["val"]
            logs.append(f"   -> 红方王牌得分手【{best_p.name}】获得 +10 爆种加成！")
        elif red_buff["effect"] == "swap_positions":
            # 1. 随机挑选两个位置索引
            idx1, idx2 = random.sample(range(5), 2)
            pos1, pos2 = POSITIONS[idx1], POSITIONS[idx2]
            
            # 2. 获取交换前的球员对象
            p1, p2 = calc_red_team[idx1], calc_red_team[idx2]
            
            # 3. 交换球员在阵容中的位置
            calc_red_team[idx1], calc_red_team[idx2] = p2, p1
            
            # 4. 【核心修复】为换位后的两人重新计算新位置的偏离惩罚并扣减能力值
            pen1, _ = calculate_position_penalty(calc_red_team[idx1], pos1)
            pen2, _ = calculate_position_penalty(calc_red_team[idx2], pos2)
            calc_red_team[idx1].rating = max(0, calc_red_team[idx1].rating - pen1)
            calc_red_team[idx2].rating = max(0, calc_red_team[idx2].rating - pen2)
            
            # 5. 记录日志
            logs.append(f"🚽 红方触发了 [教练上厕所]！阵型混乱，【{pos1} - {p1.name}】与【{pos2} - {p2.name}】互换了位置，并重新扣除了位置偏离分数！")

        # 显示计算日志
        with st.expander("查看详细对局日志", expanded=True):
            for log in logs:
                st.write(f"- {log}")

        # 3. 结果汇总展示
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        blue_total = round(sum(p.rating for p in calc_blue_team), 1)
        red_total = round(sum(p.rating for p in calc_red_team), 1)

        with col1:
            st.subheader(f"🔵 蓝方总战力：{blue_total}")
            b_data = []
            for i, pos in enumerate(POSITIONS):
                p = calc_blue_team[i]
                pen, _ = calculate_position_penalty(p, pos)
                b_data.append({
                    "出战位置": pos,
                    "球员": p.name,
                    "原位置": p.position,
                    "偏离扣分": f"-{pen:.1f}" if blue_buff["effect"] != "ignore_penalty" else "0 (无视)",
                    "最终计算能力值": round(p.rating, 1)
                })
            st.table(pd.DataFrame(b_data))

        with col2:
            st.subheader(f"🔴 红方总战力：{red_total}")
            r_data = []
            for i, pos in enumerate(POSITIONS):
                p = calc_red_team[i]
                pen, _ = calculate_position_penalty(p, pos)
                r_data.append({
                    "出战位置": pos,
                    "球员": p.name,
                    "原位置": p.position,
                    "偏离扣分": f"-{pen:.1f}" if red_buff["effect"] != "ignore_penalty" else "0 (无视)",
                    "最终计算能力值": round(p.rating, 1)
                })
            st.table(pd.DataFrame(r_data))

        # 4. 胜负判定与比分模拟
        st.markdown("---")
        st.subheader("🏆 比赛最终结果")
        
        # 简单比分换算模拟（基础分 100 + 战力差值 * 0.5 + 随机微调）
        score_diff = (blue_total - red_total) * 0.4
        base_blue_score = int(105 + score_diff + random.randint(-5, 5))
        base_red_score = int(105 - score_diff + random.randint(-5, 5))
        
        if blue_total > red_total:
            st.balloons()
            st.success(f"🎉 **🔵 蓝方胜出！** 模拟最终比分：**蓝方 {base_blue_score} : {base_red_score} 红方**")
        elif red_total > blue_total:
            st.snow()
            st.error(f"🎉 **🔴 红方胜出！** 模拟最终比分：**蓝方 {base_blue_score} : {base_red_score} 红方**")
        else:
            st.warning(f"🤝 **双方打成平手！** 模拟最终比分：**蓝方 {base_blue_score} : {base_red_score} 红方**")
