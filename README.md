# Crisis Management ABM Simulation: Traditional vs. Smart Evacuation

本项目基于 Python `Mesa` 框架构建了一个多智能体模型（Agent-Based Model），用于模拟和对比在化工厂毒气泄漏危机场景下，传统贪心寻路算法与基于 IoT+AI 动态规划（BFS避障算法）在人员疏散效能上的差异。

## 核心功能
* **传统模式 (Traditional Mode)**：模拟信息盲区下，工人依靠贪心算法直线奔向最近出口，容易误入毒气扩散区。
* **数智化模式 (Smart Mode)**：模拟全局信息统筹下，系统为工人实时下发避让毒气的动态安全路线。

## 运行方法
1. 安装依赖：`pip install -r requirements.txt`
2. 运行对比：`python run.py`
3. 动态可视化：`server.py`