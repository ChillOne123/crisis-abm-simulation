import mesa
import random
from collections import deque

# ==========================================
# 1. 定义环境冲击：毒气 Agent
# ==========================================
class GasAgent(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        # 毒气扩散逻辑：每一时间步有 15% 的概率向四周相邻的空白网格蔓延
        neighbors = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
        for neighbor in neighbors:
            # 如果该格子没有毒气，且满足扩散概率
            contents = self.model.grid.get_cell_list_contents([neighbor])
            if not any(isinstance(a, GasAgent) for a in contents) and random.random() < 0.15:
                new_gas = GasAgent(self.model.next_id(), self.model)
                self.model.grid.place_agent(new_gas, neighbor)
                self.model.schedule.add(new_gas)

# ==========================================
# 2. 定义静态节点：安全出口 Agent
# ==========================================
class ExitAgent(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
    def step(self):
        pass # 出口本身不需要动作

# ==========================================
# 定义物理阻挡：墙壁/机床 Agent
# ==========================================
class ObstacleAgent(mesa.Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
    def step(self):
        pass # 障碍物不动

# ==========================================
# 3. 定义行为主体：工人 Agent
# ==========================================
class WorkerAgent(mesa.Agent):
    def __init__(self, unique_id, model, mode="traditional"):
        super().__init__(unique_id, model)
        self.mode = mode
        self.is_safe = False
        self.is_dead = False
        
        # 【新增1：数字鸿沟】70%的工人配备了智能安全帽，30%没有
        self.has_smart_device = random.random() < 0.7 

    def step(self):
        if self.is_safe or self.is_dead:
            return

        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        if any(isinstance(agent, GasAgent) for agent in cellmates):
            self.is_dead = True
            return
        if any(isinstance(agent, ExitAgent) for agent in cellmates):
            self.is_safe = True
            return

        # 【新增2：信息延迟】如果系统还没启动，或者工人没有智能设备，只能传统逃生
        if self.mode == "smart" and self.has_smart_device and self.model.current_step >= self.model.activation_delay:
            self.move_smart()
        else:
            self.move_traditional()

    def check_congestion_and_move(self, target_pos):
        """【新增3：物理拥挤】如果目标格子人数超过容量，则被堵住无法移动"""
        contents = self.model.grid.get_cell_list_contents([target_pos])
        workers_in_cell = sum(1 for a in contents if isinstance(a, WorkerAgent))
        if workers_in_cell < self.model.max_capacity:
            self.model.grid.move_agent(self, target_pos)
        # 如果超出容量，这回合就停留在原地（模拟拥堵）

    def move_traditional(self):
        exits = [a for a in self.model.schedule.agents if isinstance(a, ExitAgent)]
        if not exits: return
        closest_exit = min(exits, key=lambda e: abs(e.pos[0]-self.pos[0]) + abs(e.pos[1]-self.pos[1]))
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
        best_step = min(possible_steps, key=lambda p: abs(closest_exit.pos[0]-p[0]) + abs(closest_exit.pos[1]-p[1]))
        
        self.check_congestion_and_move(best_step) # 替换原来的 move_agent

    def move_smart(self):
        path = self.bfs_path()
        if path and len(path) > 1:
            self.check_congestion_and_move(path[1]) # 替换原来的 move_agent

    def bfs_path(self):
        # 这里的寻路逻辑不变，保持之前的 BFS 代码即可
        queue = deque([[self.pos]])
        visited = set([self.pos])
        while queue:
            path = queue.popleft()
            x, y = path[-1]
            if any(isinstance(a, ExitAgent) for a in self.model.grid.get_cell_list_contents([(x,y)])):
                return path
            for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
                nx, ny = x + dx, y + dy
                if not self.model.grid.out_of_bounds((nx, ny)) and (nx, ny) not in visited:
                    contents = self.model.grid.get_cell_list_contents([(nx, ny)])
                    # AI 不仅要避开毒气，还可以预判极度拥挤的格子（可选）
                    if not any(isinstance(a, GasAgent) for a in contents):
                        visited.add((nx, ny))
                        queue.append(path + [(nx, ny)])
        return None
    
# ==========================================
# 4. 定义全局工厂模型
# ==========================================
class FactoryModel(mesa.Model):
    def __init__(self, width=20, height=20, num_workers=40, mode="traditional"):
        super().__init__()
        self.num_workers = num_workers
        self.grid = mesa.space.MultiGrid(width, height, True)
        self.schedule = mesa.time.RandomActivation(self)
        self.mode = mode

        # 延迟启动与拥挤程度控制变量
        self.current_step = 0
        self.activation_delay = 5 # 系统启动延迟：前5个回合盲目逃生
        self.max_capacity = 3     # 通道拥挤度：一个格子最多

        # 1. 设置两个安全出口
        exits = [(0, 0), (width-1, height-1)]
        for pos in exits:
            exit_agent = ExitAgent(self.next_id(), self)
            self.grid.place_agent(exit_agent, pos)
            self.schedule.add(exit_agent)

        # 2. 【新增】随机生成工厂复杂地形（25%的障碍物密度）
        obstacle_density = 0.25
        for x in range(width):
            for y in range(height):
                # 避开出口和毒气中心点，防止一开始就把路堵死
                if (x, y) in exits or (x == width//2 and y == height//2):
                    continue
                if self.random.random() < obstacle_density:
                    obs = ObstacleAgent(self.next_id(), self)
                    self.grid.place_agent(obs, (x, y))
                    self.schedule.add(obs)

        # 3. 随机放置工人（必须降生在空地上）
        for _ in range(self.num_workers):
            worker = WorkerAgent(self.next_id(), self, mode=self.mode)
            while True:
                x = self.random.randrange(width)
                y = self.random.randrange(height)
                # 检查该格子是否没有障碍物
                contents = self.grid.get_cell_list_contents([(x, y)])
                if not any(isinstance(a, ObstacleAgent) for a in contents):
                    break
            self.grid.place_agent(worker, (x, y))
            self.schedule.add(worker)

        # 4. 设定毒气泄漏源（网格正中央）
        gas = GasAgent(self.next_id(), self)
        self.grid.place_agent(gas, (width//2, height//2))
        self.schedule.add(gas)

        # 数据收集器：记录三种状态的人数
        self.datacollector = mesa.DataCollector(
            model_reporters={
                "Safe (Evacuated)": lambda m: sum(1 for a in m.schedule.agents if isinstance(a, WorkerAgent) and a.is_safe),
                "Dead (Poisoned)": lambda m: sum(1 for a in m.schedule.agents if isinstance(a, WorkerAgent) and a.is_dead)
            }
        )

    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()