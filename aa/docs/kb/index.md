# 知识地图

> 70 张卡，按「你接手时需要能回答的问题」组织。每张卡写一页，40–80 行，套 `docs/_template.md`。

**状态**：草稿　**最后核对**：2026-11-19　**适用版本**：UE 5.7.4

## 怎么用

**不要按顺序背定义。** 用法是：

1. 先读卡名与「必须能回答的问题」，圈出你现在答不上来的
2. 只写圈出来的那些卡
3. 每张卡写完，回到 `docs/复盘/路线图.md` 打勾
4. 每组的最后一张是「自测卡」，闭卷做一遍

卡片格式统一为六段（见 `docs/复盘/写作规范.md`），其中第 3 段必须落到本项目资产。

**出处约定**：`〔O〕` 官方文档（链接末尾带 `?application_version=5.7` 才是 5.7 文本）、`〔M〕` 本机实测、`〔I〕` 推断待验证。

---

## A 组 · 编程模型（10 卡）

| 卡 | 卡名 | 必须能回答的问题 | 本项目落点 |
|---|---|---|---|
| A1 | Blueprint 是什么 | 蓝图的资产类型有哪几种？编译后变成什么？ | 131 个 BP / 53 个 WBP |
| A2 | Blueprint Class 与 Instance | 类和实例的差别？改类会怎样影响关卡里的实例？ | `BP_ThirdPersonCharacter` vs `Start` 里的实例 |
| A3 | 事件图 vs 函数图 vs 宏 | 三者各自什么时候用？Tick 写在哪？ | `BP_TaskManager1` 的事件图 |
| A4 | 纯函数与副作用 | 纯函数不能有什么？为什么 Sequence 节点不能当流程控制用 | 交互点里的分支逻辑 |
| A5 | Cast 的本质与代价 | Cast 失败会发生什么？为什么大量 Cast 是坏味道 | `Cast To BP_ThirdPersonCharacter` 的存量 |
| A6 | Blueprint Interface | 接口解决什么问题？与 Cast 的取舍 | `BPI_interact` |
| A7 | Event Dispatcher（多播委托） | 一对多广播怎么实现？跨关卡能不能活？ | TaskManager → UI 的通知 |
| A8 | 变量的作用域与复制 | Instance Editable / Expose on Spawn / Replicated 的差别 | 50 个交互点的默认值 |
| A9 | 构造脚本（Construction Script） | 什么时候执行？能做什么不能做什么 | 交互点的组件初始化 |
| A10 | 蓝图性能陷阱 | 哪些写法会拖帧？Tick 的替代方案 | 单例管理器的 Tick |

〔O〕[Blueprints Visual Scripting](https://dev.epicgames.com/documentation/en-us/unreal-engine/blueprints-visual-scripting-in-unreal-engine?application_version=5.7) · [Interfaces](https://dev.epicgames.com/documentation/en-us/unreal-engine/interfaces-in-unreal-engine?application_version=5.7) · [Event Dispatchers](https://dev.epicgames.com/documentation/en-us/unreal-engine/event-dispatchers-in-unreal-engine?application_version=5.7)

## B 组 · 对象模型（12 卡）

| 卡 | 卡名 | 必须能回答的问题 | 本项目落点 |
|---|---|---|---|
| B1 | Actor | 什么样的东西必须是 Actor？Actor 的生命周期钩子有哪些 | 376 个 actor |
| B2 | Pawn 与 Controller | Pawn 为什么能被「占有」？Possess 做了什么 | `BP_ThirdPersonCharacter` |
| B3 | Character | Character 比 Pawn 多了什么？胶囊体与移动组件 | 同上 |
| B4 | Component 三层结构 | UActorComponent / USceneComponent / UPrimitiveComponent 各多出什么能力 | 交互点组件树 |
| B5 | 常用组件速查 | StaticMesh / SkeletalMesh / Widget / Audio / Collision 各自职责 | 同上 |
| B6 | Transform 与层级 | 父子组件的 Transform 是怎么叠加的？Attach 规则 | 复合物体（Child15 的 4 个 Mesh） |
| B7 | 碰撞通道与 Preset | Channel 与 Preset 的区别？自定义 `interact` 通道怎么用 | `DefaultEngine.ini` 的 `ECC_GameTraceChannel1` |
| B8 | Overlap vs Hit | 什么时候只报 Overlap？什么时候需要 Block | 器材拾取 |
| B9 | Trace 查询 | Line / Sphere / Capsule Trace 的差别？多通道查询怎么写 | 视线检测 |
| B10 | 生成与销毁 | Spawn 参数怎么传？销毁时机与 GC | 交互产生的临时物体 |
| B11 | 物理与 Chaos | Physics Asset 干什么？简单碰撞与复杂碰撞的取舍 | `SKM_niezi2` 等骨骼网格 |
| B12 | 组件复用的边界 | 什么时候该抽 Component，什么时候该用 Actor 组合 | 交互点模板的抽取方案 |

〔O〕[Actors](https://dev.epicgames.com/documentation/en-us/unreal-engine/actors-in-unreal-engine?application_version=5.7) · [Components](https://dev.epicgames.com/documentation/en-us/unreal-engine/components-in-unreal-engine?application_version=5.7) · [Collision](https://dev.epicgames.com/documentation/en-us/unreal-engine/collision-in-unreal-engine?application_version=5.7)

## C 组 · 运行时框架（12 卡）

| 卡 | 卡名 | 必须能回答的问题 | 本项目落点 |
|---|---|---|---|
| C1 | Gameplay Framework 全景 | 五件套谁创建谁、谁活多久 | 见 L0-3 |
| C2 | GameMode | 为什么 GameMode 只该放规则？换关会怎样 | `UI/BP/NewGameMode` |
| C3 | GameState | 单机项目需要它吗？什么时候需要 | 本项目未用 |
| C4 | PlayerController | 为什么它跨 Pawn 存续？输入该绑在哪 | `BP_playercontroller` |
| C5 | PlayerState | 玩家数据放这里还是 GameInstance | 本项目未用 |
| C6 | GameInstance | 跨关卡常驻的代价是什么？什么该放这里 | `BP_ChemistryGameInstance` |
| C7 | HUD | UE5 里 HUD 还有用吗？与 UMG 的分工 | `BP_HUD` |
| C8 | World 与 Level | `.umap` 里到底存了什么？Persistent 与 Sublevel | `Start.umap` |
| C9 | Level Blueprint | 什么时候该用关卡蓝图，什么时候是坏味道 | 待查 |
| C10 | Level Streaming | 流送与 OpenLevel 的差别？什么时候触发 | `JiaZai_ui` 加载流程 |
| C11 | World Partition | 小场景该不该开？开了的代价 | 本项目未开 |
| C12 | 子系统（Subsystem） | 不用 Actor 也能有全局逻辑？适合放什么 | 可选的改造方向 |

〔O〕[Gameplay Framework](https://dev.epicgames.com/documentation/en-us/unreal-engine/gameplay-framework-in-unreal-engine?application_version=5.7) · [Game Mode and Game State](https://dev.epicgames.com/documentation/en-us/unreal-engine/game-mode-and-game-state-in-unreal-engine?application_version=5.7) · [Programming Subsystems](https://dev.epicgames.com/documentation/en-us/unreal-engine/programming-subsystems-in-unreal-engine?application_version=5.7)

## D 组 · 表现（16 卡）

| 卡 | 卡名 | 必须能回答的问题 | 本项目落点 |
|---|---|---|---|
| D1 | PBR 四通道 | BaseColor / Metallic / Roughness / Specular 各控制什么 | 294 个 Materia |
| D2 | 材质与材质实例 | 为什么 163 个槽用同一个父材质？改父材质的代价 | `M_Opt_Surface_Var` |
| D3 | Material Function | 什么该抽成函数？参数怎么传 | 78 个 MF |
| D4 | Substrate | 它替代了什么？为什么文档还标 Beta | `r.Substrate=True` |
| D5 | Lumen GI | 它凭什么实时？代价在哪 | 已启用 |
| D6 | Lumen 反射 | `MaxRoughnessToTrace` 在限制什么 | 0.4 |
| D7 | Nanite | 什么几何适合 Nanite？什么时候反而更慢 | 301 个 SM |
| D8 | 阴影三档 Mobility | Static / Stationary / Movable 的差别与选择 | 13 盏灯全 Movable |
| D9 | 为什么关 VSM 改 CSM | 两者的代价模型差别 | `r.Shadow.Virtual.Enable=0` |
| D10 | 后处理链 | Bloom / 曝光 / 调色 / 锐化 的执行顺序 | `PP_Opt` |
| D11 | TSR | 时域超分靠什么工作？什么情况下会糊 | `TSR.Sharpness=0.7` |
| D12 | 雾与体积效果 | 指数高度雾与体积雾的差别 | `ExpFog_Room` 密度 0.0008 |
| D13 | MetaHuman 组成 | DNA / RigLogic / 骨骼 / Groom 各是什么 | 840 个文件 |
| D14 | Skeleton 与 Retargeter | 两套骨骼怎么映射？IK Rig 的角色 | 5 个 IKRig / 5 个 Retargeter |
| D15 | AnimBlueprint 与 Montage | 状态机管什么？Montage 管什么 | `ABP_walk`、189 个 AnimSequence |
| D16 | Sequencer | Level Sequence 与 Montage 的边界？Event Track 能干什么 | 79 个 LS |

〔O〕[Materials](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-materials?application_version=5.7) · [Substrate](https://dev.epicgames.com/documentation/en-us/unreal-engine/substrate-materials-in-unreal-engine?application_version=5.7) · [Lumen](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-global-illumination-and-reflections-in-unreal-engine?application_version=5.7) · [Light Mobility](https://dev.epicgames.com/documentation/en-us/unreal-engine/light-types-and-their-mobility-in-unreal-engine?application_version=5.7) · [MetaHuman](https://dev.epicgames.com/documentation/en-us/metahuman/metahuman-documentation) · [IK Retargeting](https://dev.epicgames.com/documentation/en-us/unreal-engine/ik-rig-animation-retargeting-in-unreal-engine?application_version=5.7)

## E 组 · UI 与数据（12 卡）

| 卡 | 卡名 | 必须能回答的问题 | 本项目落点 |
|---|---|---|---|
| E1 | Slate 与 UMG | 谁是谁的封装？什么时候必须碰 Slate | 53 个 WBP |
| E2 | Widget 生命周期 | Construct / OnInitialized / Tick 各什么时候跑 | 各 WBP |
| E3 | 输入模式三态 | UI Only / Game Only / Game and UI 怎么选 | 登录页 vs 实验页 |
| E4 | CommonUI | 它解决什么问题？输入栈怎么用 | 项目已启 |
| E5 | Enhanced Input | IA / IMC / Modifier / Trigger 各是什么 | 3 IA + 1 IMC |
| E6 | 新旧输入并存 | 旧式 Axis Mapping 与 Enhanced Input 谁生效 | `DefaultInput.ini` |
| E7 | DPI 缩放 | ScaleToFit 怎么换算？为什么 4K 下 UI 会糊 | `UIScaleRule` |
| E8 | DataTable | 行类型必须是 Struct？怎么从 CSV 导入 | 10 个 DT |
| E9 | Struct 与 Enum | Struct 能不能嵌套？Enum 存的是什么 | 9 Struct / 5 Enum |
| E10 | DataAsset | 什么时候用 DataAsset 而不是 DataTable | 可选改造 |
| E11 | 富文本与装饰器 | RichText 怎么插图片？装饰器在哪注册 | `NewRichTextBlockDecorator` |
| E12 | 本地化 | 本项目为什么只 stage en？中文怎么处理 | `CulturesToStage=en` |

〔O〕[UMG](https://dev.epicgames.com/documentation/en-us/unreal-engine/creating-user-interfaces-with-umg-and-slate-in-unreal-engine?application_version=5.7) · [CommonUI](https://dev.epicgames.com/documentation/en-us/unreal-engine/common-ui-plugin-for-advanced-user-interfaces-in-unreal-engine?application_version=5.7) · [Enhanced Input](https://dev.epicgames.com/documentation/en-us/unreal-engine/enhanced-input-in-unreal-engine?application_version=5.7) · [Data Driven Gameplay](https://dev.epicgames.com/documentation/en-us/unreal-engine/data-driven-gameplay-elements-in-unreal-engine?application_version=5.7)

## F 组 · 工程化（8 卡）

| 卡 | 卡名 | 必须能回答的问题 | 本项目落点 |
|---|---|---|---|
| F1 | Cook 到底做了什么 | 为什么编辑器能跑、打包就丢资产 | `bCookAll=False` |
| F2 | Pak 与 IoStore | 两者关系？Oodle 压缩在哪一步 | `UsePakFile/bUseIoStore=True` |
| F3 | Shader 编译与 DDC | 为什么换机器要重编几十分钟 | `DerivedDataCache/` |
| F4 | 性能工具 | `stat unit` 四项各代表什么 | 见 L3-3 |
| F5 | 蓝图项目的性能上限 | 纯蓝图能做多大？瓶颈通常在哪 | 无 C++ 模块 |
| F6 | 资产命名与目录 | 前缀规范怎么定？谁维护 | 见 L1-3 |
| F7 | 版本管理与 Git LFS | 哪些文件必须 LFS？指针文件是什么 | `.gitattributes` |
| F8 | 自动化 | RemoteControl / Python 能替人做什么 | `Saved/opt` 30 个脚本 |

〔O〕[Packaging](https://dev.epicgames.com/documentation/en-us/unreal-engine/packaging-your-project?application_version=5.7) · [Zen Loader](https://dev.epicgames.com/documentation/en-us/unreal-engine/zen-loader-in-unreal-engine?application_version=5.7) · [DDC](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-derived-data-cache-in-unreal-engine?application_version=5.7) · [Stat Commands](https://dev.epicgames.com/documentation/en-us/unreal-engine/stat-commands-in-unreal-engine?application_version=5.7)

---

## 附录卡

| 卡 | 内容 | 产出 |
|---|---|---|
| AP-1 | 术语中英对照 | 一张表：Blueprint / Actor / Component / GameMode … 共 80 条，右侧写「本项目里的具体指代」 |
| AP-2 | 答辩 10 问 | 每问：30 秒版答案 + 追问预案 + 证据位置 |
| AP-3 | 自测 40 题 | 每卡 1 题，答案折叠，含 10 道推演题 |

## 写作顺序建议

```text
第一周：A1-A5（编程模型骨架）+ B1-B5（对象模型骨架）
第二周：C1-C6（框架）+ E1-E5（UI 与输入）
第三周：D1-D5（渲染主干）+ F1-F3（打包）
第四周：其余按你实际要改的模块挑
```

宁可 20 张写透，不要 70 张写空。
