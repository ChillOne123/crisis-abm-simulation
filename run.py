from model import FactoryModel
import matplotlib.pyplot as plt

# 运行传统模式（信息盲区）
model_traditional = FactoryModel(mode="traditional")
for _ in range(40):
    model_traditional.step()
data_trad = model_traditional.datacollector.get_model_vars_dataframe()

# 运行数智化模式（动态规划）
model_smart = FactoryModel(mode="smart")
for _ in range(40):
    model_smart.step()
data_smart = model_smart.datacollector.get_model_vars_dataframe()

# 绘制数据对比图展示效能提升
plt.figure(figsize=(10, 5))
plt.plot(data_trad["Dead (Poisoned)"], label="Traditional Mode (Greedy Pathing)", color='red', linestyle='--')
plt.plot(data_smart["Dead (Poisoned)"], label="Smart Mode (AI Dynamic Routing)", color='green')
plt.title("Worker Casualties Over Time: Traditional vs Smart Evacuation")
plt.xlabel("Time Steps")
plt.ylabel("Number of Casualties")
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()