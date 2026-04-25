import mesa
from model import FactoryModel, WorkerAgent, GasAgent, ExitAgent, ObstacleAgent

def agent_portrayal(agent):
    """定义不同 Agent 在网页上的长相"""
    if agent is None:
        return

    portrayal = {"Shape": "rect", "w": 1, "h": 1, "Filled": "true", "Layer": 0}

    # 1. 障碍物/墙壁：黑色方块
    if isinstance(agent, ObstacleAgent):
        portrayal["Color"] = "black"
        portrayal["Layer"] = 1

    # 2. 安全出口：绿色方块
    elif isinstance(agent, ExitAgent):
        portrayal["Color"] = "green"
        portrayal["Layer"] = 1

    # 3. 毒气：红色方块（半透明，Layer设高一点遮住地表）
    elif isinstance(agent, GasAgent):
        portrayal["Color"] = "#ff0000aa" # 半透明红
        portrayal["Layer"] = 3

    # 4. 工人：蓝色圆点
    elif isinstance(agent, WorkerAgent):
        portrayal["Shape"] = "circle"
        portrayal["r"] = 0.8
        portrayal["Filled"] = "true"
        portrayal["Layer"] = 2
        portrayal["Color"] = "blue"
        # 如果工人死了，变灰色；安全了，变黄色（或消失）
        if agent.is_dead:
            portrayal["Color"] = "gray"
        elif agent.is_safe:
            portrayal["Color"] = "yellow"

    return portrayal

# ==========================================
# 定义画布：20x20 网格，网页显示尺寸 500x500 像素
# ==========================================
canvas_element = mesa.visualization.CanvasGrid(agent_portrayal, 20, 20, 500, 500)

# (可选) 增加一个实时折线图，直接在网页侧边看数据
chart_element = mesa.visualization.ChartModule([
    {"Label": "Dead (Poisoned)", "Color": "Red"},
    {"Label": "Safe (Evacuated)", "Color": "Green"}
])

# ==========================================
# 配置服务器：绑定模型、可视化元素和初始参数
# ==========================================
server = mesa.visualization.ModularServer(
    FactoryModel,
    [canvas_element, chart_element], # 包含画布和图表
    "Factory Crisis ABM Simulation",
    {
        "width": 20,
        "height": 20,
        "num_workers": 40,
        "mode": "smart",  # 录完这个记得改回 "traditional" 再录一个对比
        "seed": 30        # 锁定库里号码，确保地形和刚才的折线图完全一致！
    }
)

server.port = 8521 # 设置端口
if __name__ == "__main__":
    server.launch()