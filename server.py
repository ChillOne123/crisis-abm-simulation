from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from model import FactoryModel, WorkerAgent, GasAgent, ExitAgent

# 1. 定义智能体的视觉呈现（长相、颜色、图层）
def agent_portrayal(agent):
    if agent is None:
        return

    portrayal = {"Filled": "true", "Layer": 0}

    if isinstance(agent, WorkerAgent):
        portrayal["Shape"] = "circle"
        portrayal["r"] = 0.6
        # 如果死亡变成灰色，安全撤离会消失，正常跑动是蓝色
        if agent.is_dead:
            portrayal["Color"] = "grey"
            portrayal["Layer"] = 1 # 尸体图层垫底
        else:
            portrayal["Color"] = "blue"
            portrayal["Layer"] = 2 # 活人图层在最上面

    elif isinstance(agent, GasAgent):
        portrayal["Shape"] = "rect"
        portrayal["w"] = 1
        portrayal["h"] = 1
        portrayal["Color"] = "red"
        portrayal["Layer"] = 1 # 毒气覆盖在底层

    elif isinstance(agent, ExitAgent):
        portrayal["Shape"] = "rect"
        portrayal["w"] = 1
        portrayal["h"] = 1
        portrayal["Color"] = "green"
        portrayal["Layer"] = 0 # 绿色安全出口

    return portrayal

# 2. 创建一个 20x20 的网格画布，网页上显示尺寸为 500x500 像素
grid = CanvasGrid(agent_portrayal, 20, 20, 500, 500)

# 3. 建立服务器并加载模型
# 注意：这里我们先默认演示 "smart"（数智化动态规划）模式
server = ModularServer(
    FactoryModel,
    [grid],
    "Factory Evacuation Simulation",
    {"width": 20, "height": 20, "num_workers": 40, "mode": "smart"} 
)

# 设定服务器端口并启动
server.port = 8521 
server.launch()