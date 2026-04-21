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
# 3. 定义行为主体：工人 Agent
# ==========================================
class WorkerAgent(mesa.Agent):
    def __init__(self, unique_id, model, mode="traditional"):
        super().__init__(unique_id, model)
        self.mode = mode       # "traditional" 或 "smart"
        self.is_safe = False   # 是否已撤离
        self.is_dead = False   # 是否中毒

    def step(self):
        if self.is_safe or self.is_dead:
            return

        # 状态判定 1：是否中毒（与毒气在同一格）
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        if any(isinstance(agent, GasAgent) for agent in cellmates):
            self.is_dead = True
            return

        # 状态判定 2：是否到达出口
        if any(isinstance(agent, ExitAgent) for agent in cellmates):
            self.is_safe = True
            return

        # 根据不同模式执行不同的寻路逻辑
        if self.mode == "traditional":
            self.move_traditional()
        else:
            self.move_smart()

    def move_traditional(self):
        """传统模式痛点：信息盲区，无视毒气直接奔向直线距离最近的出口"""
        exits = [a for a in self.model.schedule.agents if isinstance(a, ExitAgent)]
        if not exits: return
        
        # 找到绝对距离最近的出口
        closest_exit = min(exits, key=lambda e: abs(e.pos[0]-self.pos[0]) + abs(e.pos[1]-self.pos[1]))
        possible_steps = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
        
        # 向着目标移动一步（可能直接走进毒气里）
        best_step = min(possible_steps, key=lambda p: abs(closest_exit.pos[0]-p[0]) + abs(closest_exit.pos[1]-p[1]))
        self.model.grid.move_agent(self, best_step)

    def move_smart(self):
        """数智化模式应用：IoT获取毒气坐标，AI下发 BFS 全局避障路径"""
        path = self.bfs_path()
        if path and len(path) > 1:
            self.model.grid.move_agent(self, path[1]) # 沿着安全路径走下一步

    def bfs_path(self):
        # 基于广度优先搜索(BFS)寻找避开毒气的最短出口路径
        queue = deque([[self.pos]])
        visited = set([self.pos])
        while queue:
            path = queue.popleft()
            x, y = path[-1]

            # 如果当前节点是出口，返回整条路径
            if any(isinstance(a, ExitAgent) for a in self.model.grid.get_cell_list_contents([(x,y)])):
                return path

            # 遍历四个方向
            for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
                nx, ny = x + dx, y + dy
                if not self.model.grid.out_of_bounds((nx, ny)) and (nx, ny) not in visited:
                    # 关键逻辑：AI算法识别并避开毒气格子
                    contents = self.model.grid.get_cell_list_contents([(nx, ny)])
                    if not any(isinstance(a, GasAgent) for a in contents):
                        visited.add((nx, ny))
                        queue.append(path + [(nx, ny)])
        return None # 如果被毒气完全包围则无路可走

# ==========================================
# 4. 定义全局工厂模型
# ==========================================
class FactoryModel(mesa.Model):
    def __init__(self, width=20, height=20, num_workers=40, mode="traditional"):
        self.num_workers = num_workers
        self.grid = mesa.space.MultiGrid(width, height, True)
        self.schedule = mesa.time.RandomActivation(self)
        self.mode = mode

        # 设置两个安全出口（左上角和右下角）
        exits = [(0, 0), (width-1, height-1)]
        for pos in exits:
            exit_agent = ExitAgent(self.next_id(), self)
            self.grid.place_agent(exit_agent, pos)
            self.schedule.add(exit_agent)

        # 随机放置工人
        for _ in range(self.num_workers):
            worker = WorkerAgent(self.next_id(), self, mode=self.mode)
            x = self.random.randrange(width)
            y = self.random.randrange(height)
            self.grid.place_agent(worker, (x, y))
            self.schedule.add(worker)

        # 设定毒气泄漏源（网格正中央附近）
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