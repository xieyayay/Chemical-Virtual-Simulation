# 项目概览

> 打开项目 → 了解结构 → 开始开发。

## 环境要求

- **UE 版本**：5.4.4及以上
- **目标平台**：Window
- **编程语言**：蓝图（无 C++）

### 必需插件

以下插件需要**提前下载安装**，否则可能打不开项目：

| 插件      | 费用  | 用途                 |
| ------- | --- | ------------------ |
| VaRest  | 免费  | HTTP 请求（AI 对话 API） |
| EasyCsv | ¥30 | CSV 数据读写（实验报告导出）   |

> 其他插件是引擎内置或项目已包含，不需要单独下载。

## 打开项目

1. 双击 `aa.uproject` 打开
2. 首次打开需编译着色器（右下角有进度条，约 5-10 分钟）
3. 编译完成后进入登录界面 `L_Login`

## 项目目录

Content 下按**模块**组织，每个人管理自己负责的文件夹：

```
Content/
├── UI/              ← 登录界面、GameMode（我的根据地）
├── main_UI/         ← 主界面：任务系统、实验报告
├── Anim/            ← 关卡序列动画（区分创建者：LS_YYF、LS_lcz）
├── chemistry_model/ ← 化学模型 & 贴图
├── model/           ← 3D 器材模型
├── Game_MoShi/      ← GameInstance、游戏模式
├── Deepseek/        ← AI 对话系统
├── JiaZai_ui/       ← 加载界面
├── movies/          ← 视频（登录动画）
└── _ZiTi/           ← 中文字体
```

### 命名规则

| 分类       | 前缀      | 示例                   |
| -------- | ------- | -------------------- |
| 静态网格     | `SM_`   | `SM_Beaker`          |
| 骨骼网格     | `SK_`   | `SK_Character`       |
| 基础材质     | `M_`    | `M_Glass`            |
| 材质实例     | `MI_`   | `MI_Glass_Blue`      |
| 蓝图 Actor | `BP_`   | `BP_TaskManager1`    |
| 动画蓝图     | `ABP_`  | `ABP_Character`      |
| 控件蓝图     | `WBP_`  | `WBP_gameover`       |
| 关卡序列     | `LS_`   | `LS_YYF`             |
| 枚举       | `E_`    | `E_PlayMode`         |
| 数据表      | `DT_`   | `DT_ExperimentData`  |
| 结构体      | `S_`    | `S_ExperimentRecord` |
| 字体       | `Font_` | `Font_HanChan`       |

## 核心配置

`Config/DefaultEngine.ini` 中的关键项：

### 渲染

```ini
[/Script/Engine.RendererSettings]
r.DynamicGlobalIlluminationMethod=1   ; 1 = Lumen（全局光照）
r.ReflectionMethod=1                  ; 1 = Lumen（反射）
r.Shadow.Virtual.Enable=1             ; Virtual Shadow Maps（虚拟阴影贴图）
r.Substrate=True                      ; Substrate 材质系统
r.GenerateMeshDistanceFields=True     ; 网格距离场（Lumen 需要）
```

### Windows 打包

```ini
[/Script/WindowsTargetPlatform.WindowsTargetSettings]
DefaultGraphicsRHI=DefaultGraphicsRHI_DX12   ; 渲染后端：DirectX 12
+D3D12TargetedShaderFormats=PCD3D_SM6        ; 打包着色器格式：SM6
+D3D11TargetedShaderFormats=PCD3D_SM5        ; 兼容 SM5
```

### 游戏入口

```ini
[/Script/EngineSettings.GameMapsSettings]
EditorStartupMap=/Game/UI/L_Login                                  ; 编辑器启动关卡
GameDefaultMap=/Game/UI/L_Login                                    ; 打包后默认关卡
GameInstanceClass=/Game/Game_MoShi/BP_ChemistryGameInstance        ; 全局 GameInstance
GlobalDefaultGameMode=/Game/UI/BP/NewGameMode                      ; 默认 GameMode
```

### 硬件 & UI

```ini
[/Script/HardwareTargeting.HardwareTargetingSettings]
DefaultGraphicsPerformance=Maximum    ; 画质预设：最高
TargetedHardwareClass=Desktop         ; 硬件等级：桌面端

[/Script/Engine.UserInterfaceSettings]
UIScaleRule=ScaleToFit                ; 不同分辨率自动缩放适配
```

### 自定义碰撞通道

```ini
[/Script/Engine.CollisionProfile]
+DefaultChannelResponses=(Channel=ECC_GameTraceChannel1, Name="interact")
; 自定义 Trace 通道 "interact"，用于实验器材的交互检测
```
