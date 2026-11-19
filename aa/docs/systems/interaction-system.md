# 交互系统

> 一次「按 E 拿镊子」背后发生了什么，以及为什么 50 个交互点是这个项目最大的技术债。

**状态**：已核对（结构）· 函数表待补　**最后核对**：2026-11-19　**适用版本**：UE 5.7.4

## 一句话结论

交互系统 = **一个接口**（`BPI_interact`）+ **一套约定**（组件树模板 + 自定义碰撞通道 `interact`）+ **50 份复制粘贴的蓝图**。前两者是设计，第三者是债：新增一个可交互物体要复制一份蓝图，改一句提示语要改 50 处。

## 机制

### 一次交互的完整时序

```text
玩家                角色(Character)            交互点(BP_interact_ChildX)          UI
 │                        │                              │                         │
 ├─ 靠近物体 ────────────→│                              │                         │
 │                        ├─ 视线/球形检测 ────────────→│                         │
 │                        │                              ├─ WidgetComponent 显示 ─→│ 「按 E 拾取」
 ├─ 按 E ───────────────→│                              │                         │
 │                        ├─ 调接口 Interact ──────────→│                         │
 │                        │                              ├─ 判定类型(E_interacttype)
 │                        │                              ├─ 播放动画 / 改状态 / 播音效
 │                        │←──── 返回结果 ───────────────┤                         │
 │                        ├─ 更新任务进度 ──────────────────────────────────────→│ 任务面板刷新
 │                        │                              ├─ 隐藏提示 / 销毁或变形  │
```

关键判断：**角色不认识具体的器材类型**。角色只持有「一个能响应接口的家伙」，具体是镊子还是容量瓶，由 `BPI_interact` 的实现类自己决定。这是本项目做得对的一处设计，也是后续重构必须保住的前提。

### 三个组成件

| 组成件 | 路径 | 作用 |
|---|---|---|
| 接口 | `/Game/UI/BP/BPI_interact` | 定义「可交互」的契约：有哪些函数、返回什么 |
| 类型枚举 | `E_interacttype` | 交互方式（拾取 / 点击 / 靠近触发 / 按住…） |
| 信息结构体 | `S_interact_info` | 一个交互点要对外暴露的全部信息（名称、提示文案、图标…） |
| 输入枚举 | `E_inpute_type` | 玩家侧输入种类（与旧式 `pressE` 映射配合） |
| 碰撞通道 | `defaultengine.ini` → `ECC_GameTraceChannel1` = `interact` | 只让交互检测命中，不污染默认通道 |

〔M〕以上路径来自 AssetRegistry 导出（`Saved/ue_audit/01_blueprints.json`）与 `Config/DefaultEngine.ini`。

### 组件树模板（全项目统一）

```text
BP_interact_ChildX (Actor)
├─ SceneComponent            ← 根，只提供 Transform
├─ BillboardComponent        ← 编辑器里好找，运行时通常关闭
├─ StaticMeshComponent       ← 物体本体（可能多个，见 Child15 的 4 个）
├─ WidgetComponent           ← 世界空间 3D 提示（"按 E"）
├─ BillboardComponent        ← 第二个，用于图标/状态标记
├─ [可选] BoxComponent / SphereComponent  ← 触发体积
├─ [可选] NiagaraComponent / ParticleSystemComponent  ← 特效
└─ [可选] 多个 StaticMeshComponent        ← 复合物体
```

已核对的实例〔M〕：

| 蓝图 | 组件特点 |
|---|---|
| `BP_interact_Child15` | 4 个 StaticMesh + 2 个 WidgetComponent + 3 个 BoxComponent |
| `BP_interact_Child14` | 含 SphereComponent + ParticleSystemComponent |
| `BP_KT`（空调） | StaticMesh + Widget + NavigationInvoker + Box |

同一个模板重复了约 50 次，分布在 `/Game/UI/BP/interact/BP_l/` 下（`Child1..Child35`、`Childf/f1-f4`、`Child7_2`、`Child9_2/3`、`Child12_1_/12_2_`、`Child25_1..3`、`Child26_2`、`Child28_1..3`、`Child_26_3`…）。

## 本项目实例

### 接口函数表

> ★ 待补（你自己填）：打开 `/Game/UI/BP/BPI_interact`，把每个函数的**名称、输入、输出**抄下来。
> 这张表是整个系统的契约，必须准确。

| 函数 | 输入 | 输出 | 谁调用 | 备注 |
|---|---|---|---|---|
| （待填） | | | 角色 | |
| （待填） | | | | |

获取方式（二选一）：

- 编辑器里双击 `BPI_interact` → 左侧「函数」列表
- 或让 RemoteControl 导出（脚本：`tools/rc_dump_bp.py`，见下文「延伸」）

### 一个交互点的完整配置

> ★ 待补：选一个你熟悉的器材（建议从 `BP_interact_Child14` 开始），记录：
>
> - 它挂了哪些组件（逐个列）
> - `WidgetComponent` 里的控件是哪个 WBP、提示文案是什么
> - 触发用的是 Box 还是 Sphere、尺寸多少
> - 交互成功后它做了什么（隐藏？换 Mesh？播 Sequence？写 GameInstance？）

### 角色侧的处理

> ★ 待补：打开 `BP_ThirdPersonCharacter`，找到调用交互接口的那段。
>
> - 检测用的是什么（Line Trace / Sphere Overlap / Distance）
> - 检测频率是 Tick 还是 Timer
> - 命中后怎么拿到接口（`Does Implement Interface` 还是直接 Cast）

## 坑与反例

### 坑 1：50 份复制导致「改文案要改 50 次」

- **症状**：产品要求把「按 E 拾取」改成「按 E 拿取」，需要打开 50 个蓝图逐个改
- **根因**：交互点没有共用父类，也没有数据表驱动；文案硬编码在各自蓝图的 Widget 或默认变量里
- **改法**：见下一节的重构方案
- **出处**：〔M〕`/Game/UI/BP/interact/BP_l/` 下 50 个近似蓝图

### 坑 2：Cast 到具体类导致加一个器材就要改角色

- **症状**：角色蓝图里出现 `Cast To BP_interact_Child14`、`Cast To BP_interact_Child15`… 分支越加越长
- **根因**：用 Cast 代替接口分发
- **改法**：只保留 `Cast To` 到接口（或直接 Message 调用），具体类型由交互点自己处理
- **出处**：〔I〕待验证——请在你读角色蓝图时确认现状是否如此，并在此处更新

### 坑 3：碰撞通道污染

- **症状**：角色走路被器材挡住，或者射线检测打不中器材
- **根因**：交互体用了默认 `BlockAll`，或者检测时用了 `Visibility` 通道而不是自定义 `interact`
- **改法**：交互检测统一走 `interact` 通道；器材本体对 Pawn 可 Block，对 `interact` 必须 Overlap/Block 视需求
- **出处**：〔M〕`DefaultEngine.ini` 的 `+DefaultChannelResponses=(Channel=ECC_GameTraceChannel1, Name="interact")`

## 重构方案（可选，M4 里程碑）

目标：**新增一个交互物体 = 加一行数据表，不改蓝图**。

### 结构

```text
BP_InteractBase  (Actor，唯一父类)
 ├─ 组件树模板（固定）
 ├─ 从 DT_InteractConfig 读自己那一行（按 RowName 或 Actor Tag）
 └─ 统一实现 BPI_interact，行为由「配置里的类型枚举」分支

DT_InteractConfig  (DataTable，行类型 S_InteractConfig)
 └─ 每行 = 一个可交互物体
```

### 字段设计（建议，按你实际需要增删）

| 字段 | 类型 | 说明 |
|---|---|---|
| `DisplayName` | FText | 提示里显示的物体名 |
| `HintText` | FText | 「按 E 拾取」这类文案 |
| `Icon` | TSoftObjectPtr<Texture2D> | 图标（软引用，避免全量加载） |
| `InteractType` | E_interacttype | 交互方式，驱动分支 |
| `TriggerShape` | E_TriggerShape | Box / Sphere / 无 |
| `TriggerSize` | FVector | 体积尺寸 |
| `MeshPath` | TSoftObjectPtr<StaticMesh> | 物体本体 |
| `ResultAction` | E_ResultAction | 隐藏 / 换 Mesh / 播 Sequence / 触发任务 |
| `LinkedTaskStep` | int32 | 关联 `DT_Tasks` 的步骤号 |
| `Sound` | TSoftObjectPtr<SoundBase> | 交互音效 |

### 迁移步骤（不要一次做完）

1. 新建 `BP_InteractBase` + `S_InteractConfig` + `DT_InteractConfig`，**只做 1 个物体**
2. 用 Reference Viewer 确认新物体没有任何旧引用
3. 每迁 5 个，跑一遍该器材相关的任务步骤，确认无回归
4. 全部迁完后，旧蓝图保留一个版本周期再删（用 git 分支隔离）
5. 回归清单：每个实验至少走通首尾两步

### 不要做的事

- 不要为了「统一」把 50 个蓝图合并成 1 个巨型蓝图（那是另一种债）
- 不要在 `BP_InteractBase` 里写 `Cast To` 到任何具体器材
- 不要把配置塞进 `GameInstance`（那是运行时状态，配置该在 DataTable）

## 自测

1. `BPI_interact` 一共有几个函数？分别被谁调用？
2. 一个交互点至少需要哪几个组件才能工作？哪些是可选的？
3. 如果把碰撞通道 `interact` 删掉，改回用 `Visibility`，会发生什么？列出至少两个后果。

<details>
<summary>参考答案</summary>

1. 见你自己的函数表（★ 待补后填入）。调用方通常只有角色一处。
2. 必需：`SceneComponent`（根）+ `StaticMeshComponent`（本体）+ 触发体积（Box/Sphere）或距离检测。可选：`WidgetComponent`（提示）、`BillboardComponent`（编辑器可见性）、特效组件。
3. 后果一：交互检测会打到墙、地面、角色自身，需要额外过滤；后果二：器材如果也想被其他系统（如射线拾取、瞄准）检测，通道会混在一起；后果三：自定义通道原本可以做「只对交互生效」的 Overlap 事件，改回 Visibility 后可能丢失事件或误触发。

</details>

## 延伸

- 相关页面：[任务与流程](task-system.md)（交互成功怎么推进任务）、[可复用蓝图](../blueprints/reusable-blueprints.md)（抽父类的通用做法）
- 官方文档：[Blueprint Interfaces](https://dev.epicgames.com/documentation/en-us/unreal-engine/interfaces-in-unreal-engine?application_version=5.7)、[Collision](https://dev.epicgames.com/documentation/en-us/unreal-engine/collision-in-unreal-engine?application_version=5.7)
- 数据导出：`python tools/audit_to_md.py --bp /Game/UI/BP/BPI_interact`（把接口函数导出成 Markdown 表格）
- 现场查证：编辑器打开 `/Game/Start`，按 `Ctrl+Shift+,` 看 GPU，或选中任一 `BP_interact_Child*` 看细节面板
