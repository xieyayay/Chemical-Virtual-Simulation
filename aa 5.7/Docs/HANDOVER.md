# 项目交接文档 · 虚拟仿真（UE 5.7）

> 生成时间：2026-11-10 17:00
> 用途：上下文压缩 / 换人接手后，凭此文档即可继续工作，不需要重新摸索。

---

## 一、环境

| 项 | 值 |
|---|---|
| 项目路径 | `D:\UE5\Chemistry\aa 5.7` |
| 项目文件 | `aa.uproject` |
| 引擎 | `D:\UE\UE_5.7\Engine\Binaries\Win64\UnrealEditor.exe` |
| 命令行版 | 同目录 `UnrealEditor-Cmd.exe` |
| 引擎版本 | 5.7.4（CL 51494982） |
| 图形 | D3D12 / SM6，RTX 5070 12G，纹理池 7040MB |
| 主关卡 | `/Game/Start`（另有 `L_Login` 登录图 / `menuMap`） |
| 日志真实位置 | `C:\Users\Administrator\AppData\Local\UnrealEngine\5.7\Saved\Logs\aa.log`（**不是项目目录下**） |

---

## 二、RemoteControl API（已打通，最强的自动化手段）

### 2.1 启动方式

```
UnrealEditor.exe "D:\UE5\Chemistry\aa 5.7\aa.uproject" /Game/Start -RCWebControlEnable -RCWebInterfaceEnable
```

端口 **30010**，约 10–25 秒就绪。

### 2.2 已完成的配置（不要重复排查）

**`aa.uproject`** 已启用两个插件：

```json
{ "Name": "RemoteControl", "Enabled": true },
{ "Name": "RemoteControlWebInterface", "Enabled": true }
```

**`Config/DefaultRemoteControl.ini`**（注意文件名和段名，踩过坑）：

```ini
[/Script/RemoteControlCommon.RemoteControlSettings]
bRestrictServerAccess=False
bEnableRemotePythonExecution=True
bAllowConsoleCommandRemoteExecution=True
AllowedOrigin=*
bAutoStartWebServer=True
bAutoStartWebSocketServer=True
RemoteControlHttpServerPort=30010
RemoteControlWebInterfacePort=30000
```

三个易错点：
1. 类定义是 `UCLASS(config = RemoteControl)` → 文件必须是 **`DefaultRemoteControl.ini`**，不是 `DefaultEngine.ini`
2. 模块名带 Common → 段名是 `[/Script/RemoteControlCommon.RemoteControlSettings]`
3. 属性名是 **`bAllowConsoleCommandRemoteExecution`**（不是 `bAllowConsoleCommand`）

### 2.3 调用方法（PowerShell）

**执行任意 Python（最常用）**

```powershell
$base = "http://127.0.0.1:30010"
$code = @'
import unreal
unreal.log("hello from API")
'@
$body = @{
  objectPath = "/Script/PythonScriptPlugin.Default__PythonScriptLibrary"
  functionName = "ExecutePythonCommand"
  parameters = @{ PythonCommand = $code }
} | ConvertTo-Json -Depth 8
Invoke-RestMethod -Uri "$base/remote/object/call" -Method Put -Body $body -ContentType "application/json"
```

**执行控制台命令**

```powershell
function Call($obj,$fn,$params){
  $b = @{ objectPath=$obj; functionName=$fn; parameters=$params } | ConvertTo-Json -Depth 8
  Invoke-RestMethod -Uri "http://127.0.0.1:30010/remote/object/call" -Method Put -Body $b -ContentType "application/json"
}
$w = (Call "/Script/UnrealEd.Default__UnrealEditorSubsystem" "GetEditorWorld" @{}).ReturnValue
Call "/Script/Engine.Default__KismetSystemLibrary" "ExecuteConsoleCommand" @{
  WorldContextObject=$w; Command="stat unit"; SpecificPlayer=$null }
```

**其他可用端点**：`/remote/object/property`（读写属性）、`/remote/object/describe`、`/remote/batch`

### 2.4 已知限制

| 限制 | 说明 |
|---|---|
| PIE 世界对象拿不到 | `get_pie_world()` / `GameplayStatics.get_game_world()` 在 5.7 Python 里**不存在** |
| 编辑器视口后台降频 | 窗口不在前台时 `ProfileGPU` 只记录 Slate UI（0.5ms），场景 pass 为空 |
| headless 无 GPU | `-run=pythonscript` 即使不加 `-nullrhi` 也是 Null RHI（日志 `verbatimrhiname="Null"`） |
| `get_material_property_input_node` | 对 DekoClass 的母材质返回 `None`（输入接了 Material Function，追不到） |

### 2.5 截图方法（编辑器窗口必须在前台）

```powershell
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WA {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
}
"@
$p = Get-Process -Name "UnrealEditor" | Select-Object -First 1
[WA]::ShowWindow($p.MainWindowHandle, 3) | Out-Null   # 3 = 最大化
Start-Sleep -Milliseconds 300
[WA]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
Start-Sleep -Seconds 3
Add-Type -AssemblyName System.Windows.Forms,System.Drawing
$b = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bmp = New-Object System.Drawing.Bitmap $b.Width, $b.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)
$bmp.Save("D:\UE5\Chemistry\aa 5.7\Saved\opt\shot.png", [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
```

编辑器窗口标题：**`aa - 虚幻编辑器`**。
`HighResShot` 命令在编辑器里**不生成可用文件**，别用。

---

## 三、当前状态

### 3.1 材质

| 项 | 状态 |
|---|---|
| 不透明材质 | **163 槽**，父材质 `M_Opt_Surface_Var`（5 参数 + WorldPosition 噪声调制粗糙度） |
| 颜色来源 | **全部取自原材质真实值**（`get_material_default_vector_parameter_value(mat, "Param")`） |
| 玻璃 | 30 槽，`M_Opt_Glass`，Fresnel 驱动 Opacity，`TLM_VOLUMETRIC_DIRECTIONAL` |
| 金属 | `MI_Opt_chrome`（0.92 / R0.12 / Metallic 1.0），水龙头 6 槽 |
| 粗糙度变化 | `RoughnessVar`：white 0.12 / white1 0.10 / 其余 0.08 |
| 大理石 | `M_Opt_Marble` + `MI_Opt_Marble_White` 已建，**当前未应用**（用户暂停） |
| 贴图材质 | `M_Opt_Surface_Tex` 已删除（材质改造暂停） |

### 3.2 灯光（13 盏，全部 Movable）

```
DirectionalLight   250 lux   5500K   投影 ON
SpotLight2/4/5/6    800 cd    4800K   投影 ON
SpotLight3         1200 cd    4800K   投影 ON
SpotLight7 / SpotLight  40 / 8 cd     投影 ON
PointLight6        1600 cd    4000K   投影 ON
RectLight ×5       500 lm     5000K   投影 ON
```

- `ContactShadowLength = 0.03`
- 局部光 `ShadowResolutionScale = 0.5`
- 光源色温由**用户手动微调**，不要覆盖

### 3.3 渲染

```ini
r.AllowStaticLighting=False
r.Shadow.Virtual.Enable=0          ; VSM 关闭，用传统 CSM
r.Shadow.MaxResolution=3072
r.Shadow.MaxCSMResolution=2048
r.Shadow.MaxSoftKernelSize=0
r.Shadow.RadiusThreshold=0.03
r.SSR.Quality=2
r.AOQuality=1
r.ContactShadows=1
r.Lumen.Reflections.MaxRoughnessToTrace=0.4
r.Streaming.PoolSize=3000
r.ScreenPercentage=100
r.AntiAliasingMethod=4
r.TSR.Sharpness=0.7
r.MotionBlurQuality=0
```

### 3.4 后处理 `PP_Opt`（unbound）

| 参数 | 值 |
|---|---|
| Bloom Intensity / Threshold | 0.30 / 1.0 |
| Vignette | 0.15 |
| Film Grain | 0.01 |
| Scene Fringe | 0.0 |
| Sharpen | 0.20 |
| Color Contrast | 1.02 |
| Color Saturation | (0.752, 0.760, 0.752) **用户手调，勿覆盖** |
| 分区调色 | Shadows 饱和 1.06 / 对比 1.05 / 增益 (0.98,0.99,1.02)；Highlights 饱和 0.96 / 对比 0.98 / 增益 (1.02,1.00,0.98) |
| Local Exposure | override 全关 |
| WhiteTemp / Tint | override 关（6500 中性） |
| Motion Blur | 0 |

### 3.5 雾

见 ChangeLog Step 25。当前：普通指数雾，`ExpFog_Room`，密度 0.0008，体积雾**关闭**。

---

## 四、脚本清单（`Saved/opt/`）

| 脚本 | 作用 |
|---|---|
| `step1_surface.py` | 建纯参数母材质 + white 系 |
| `step2_gray_black.py` | gray/black 系 |
| `step3_lights.py` | 灯光调物理照度 |
| `step4_glass.py` / `step4b_glass_fix.py` | 玻璃材质 |
| `step5_colors.py` | 彩色材质 |
| `fix_colors.py` | **用真实颜色重建全部 MI**（关键修复） |
| `rebind.py` | 重新绑定材质槽 |
| `step6_postprocess.py` | PPV 创建 |
| `step6b_sharp.py` | 锐化 |
| `step7_glove_color.py` / `step7b_chrome.py` | 手套/镀铬 |
| `step8_spot_temp.py` | SpotLight 色温 |
| `step9_roughvar.py` / `step10_roughvar_all.py` / `step11_roughvar2.py` / `step12_tone_down.py` / `step13_lower.py` | 粗糙度空间变化（多轮调参） |
| `step14_localexp.py` | Local Exposure |
| `step15_realistic.py` / `step15b_restore.py` | 真实档 |
| `step16_contact.py` | 接触阴影 |
| `step17_shadow.py` | 阴影距离 |
| `step18_movable.py` | 灯改 Movable |
| `step19_perf.py` / `step20_perf2.py` / `step21_restore.py` | 性能优化与还原 |
| `step22_grading.py` | 分区调色 |
| `step23_glass_tlm.py` | 玻璃光照模式 |
| `step24_cleanup.py` | 清理未用资产 |
| `adjust_exposure.py` | 曝光（当前未用） |
| `revert_to_baseline.py` | 还原基线 |

**headless 执行模板**

```powershell
$exe="D:\UE\UE_5.7\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$proj="D:/UE5/Chemistry/aa 5.7/aa.uproject"
$env:OPT_APPLY="1"
& $exe $proj -run=pythonscript "-script=D:/UE5/Chemistry/aa 5.7/Saved/opt/XXX.py" `
  -EnablePlugins=PythonScriptPlugin -unattended -nosplash -nullrhi -stdout
Remove-Item Env:\OPT_APPLY
```

**必须用正斜杠**（反斜杠会被 UE 当转义，报 `Could not load Python file`）。
**执行前必须关闭编辑器**，否则两个实例互相覆盖。
**脚本里 `print()` 不进 stdout**，要写文件或用 `unreal.log()`。

---

## 五、踩过的坑（按严重程度）

### 5.1 编辑器内存覆盖（最高频）

**现象**：通过 API 改了关卡内容（材质槽、雾参数），用户之后保存，改动全没了。

**原因**：编辑器内存里是旧状态，保存时覆盖磁盘。

**解决**：API 改完后，让用户在编辑器里 **File → Reload** 重新加载关卡，或者关闭重开。

### 5.2 材质名与颜色无关

`/Game/models/material/` 下的材质名完全不可靠：

```
gray5 = 橙色 (0.977, 0.293, 0.018)
gray6 = 蓝色 (0.227, 0.213, 0.890)
green2 = 米黄 (0.994, 0.880, 0.588)
green3 = 纯黑 (0, 0, 0)
pink = 洋红
```

**必须从资产里读**：

```python
MEL.get_material_default_vector_parameter_value(mat, "Param")      # 普通材质
MEL.get_material_default_vector_parameter_value(mat, "基础颜色")   # glass 系
```

### 5.3 后处理参数的单位陷阱

| 参数 | 陷阱 |
|---|---|
| `ColorContrast` / `ColorSaturation` | **乘数**，默认 (1,1,1,1)。写 0.1 = 压到 10%，画面必灰 |
| `BloomThreshold` | 默认 **−1.0** = 全画面泛光，必须改成 0.8–1.2 |
| `LocalExposure*ContrastScale` | **<1 是压缩**（变灰），>1 才是增强 |
| `WhiteTemp` | **数值越低画面越暖**，6500 是中性 |

### 5.4 阴影相关

| 问题 | 原因 | 解决 |
|---|---|---|
| 开关 VSM 后出现「光照需要重建」+ `Preview` 水印 | Stationary 灯需要 Lightmap | `r.AllowStaticLighting=False` + 全部改 Movable |
| 阴影全部消失 | `MaxSoftKernelSize=12` 把中小阴影糊没 | 设 0–4 |
| 阴影糊 | 方向光 `DynamicShadowDistanceMovableLight` 默认 20000（200米） | 室内设 4000 |
| 关灯投影后画面变差 | 投影建立的是空间关系，不是照明 | 不要按"灯亮不亮"决定关不关投影 |

### 5.5 雾的三次坑

1. `FogDensity` 单位是 **1/cm**，0.008 = 3 米处只剩 9% 透射
2. 旧的 `ExponentialHeightFog` **数据损坏**：参数全对但不渲染。判定法：密度设 0.1，画面不变就是坏的，删掉重建
3. 体积雾不适合大空间多灯场景（见 ChangeLog Step 25）

### 5.6 材质节点

- `Noise` + `WorldPosition` 在 `r.Substrate=True` 下**编译正常**（之前误判为失败原因）
- 母材质**重建表达式时不要删资产**，用 `delete_all_material_expressions` 清空后重建，否则 MI 的父材质引用会断
- `Roughness × (1 − RoughnessVar)` 不能低于 **0.25**，否则出现"湿渍感"
- 半透明材质的 `BaseColor` 是**透射色**，不是 albedo。无色玻璃要接近白（0.9+），给 0.02 会变成黑玻璃
- 玻璃 `Opacity` 必须由 Fresnel 驱动（正面 0.03 / 边缘 0.85），常量 Opacity 看起来像塑料布

---

## 六、下一步任务：屋顶墙角漏光

### 6.1 现象

墙角（墙面与天花板交界处）出现**三角形亮斑**，形状沿几何边缘分布。这是典型的 **Lumen 距离场光照泄漏（Light Leak）**。

### 6.2 成因分析（按概率排序）

**① Lumen Surface Cache / 距离场精度不足**
Lumen 用体素化的 Scene Capture 近似场景几何。墙角这种"两面相交的锐角"在体素化后容易出现空洞，天光（SkyLight）从缝隙漏进来。

**② 几何本身不闭合**
墙面和天花板是两个独立的 StaticMesh，如果它们之间有 1–2 厘米的缝隙，Lumen 和传统阴影都会漏光。这类问题在 3ds Max 导出的模型里非常常见。

**③ SkyLight 泄漏**
`r.Lumen.SkylightLeaking` 控制 SkyLight 的泄漏量（默认 0），但 `LumenFullSkylightLeakingDistance`（默认 1000）会影响远处。

**④ 方向光阴影距离不足**
`DynamicShadowDistanceMovableLight = 4000`（40 米），如果墙角在阴影距离之外，方向光不会被遮挡。

### 6.3 排查与修复顺序

**第一步：确认是几何缝隙还是 Lumen 泄漏**

把视口切到 **Lumen → Lumen Scene** 或 **Lighting Only** 模式，观察亮斑形状：
- 亮斑边缘**严格贴合几何边缘且呈直线** → 几何缝隙
- 亮斑边缘**模糊、呈块状** → Lumen 体素泄漏

**第二步：如果怀疑几何缝隙**

选中墙面 → 看它的 `Bounds` → 检查与天花板是否重叠。修复方式：
- 把墙体沿法线方向**加厚** 2–5 厘米（缩放或移动）
- 或者在缝隙处补一块贴合的封板

**第三步：如果是 Lumen 泄漏（最可能）**

按顺序尝试这些 CVar（从代价低的开始）：

```ini
; 提高 Lumen 场景分辨率（代价：显存和性能）
r.LumenScene.SurfaceCacheResolution=2          ; 默认 1
; 减小表面偏差
r.Lumen.DiffuseIndirect.SurfaceBias=0.5        ; 默认 1.0
; 关掉天光泄漏
r.Lumen.SkylightLeaking=0
r.Lumen.FullSkylightLeakingDistance=200        ; 默认 1000，改小
; 提高距离场精度
r.AOQuality=4
r.DistanceField.Enable=1
```

**第四步：如果还想更保险**

在墙角放一个 **Post Process Volume**，局部调 `AmbientOcclusionIntensity` 到 1.0 + `AmbientOcclusionRadius` 30，用 SSAO 把亮斑压下去。这是"补丁式"方案，但效果直接。

**第五步：终极方案**

如果漏光始终压不住，把该区域的墙面材质换成 `TwoSided = true`，让背面也参与深度写入，能有效阻挡泄漏。

### 6.4 需要的工具

- RemoteControl API（读写属性、执行 `stat`、截图对比）
- 截图对比：改之前和改之后各截一张，用像素差判断是否有变化
- 日志：`%LOCALAPPDATA%\UnrealEngine\5.7\Saved\Logs\aa.log`

---

## 七、文档索引

| 文档 | 内容 |
|---|---|
| `Docs/OPT_ChangeLog_UE5.7.md` | 全部改动日志（Step 1–25）+ 物理基线 + 可复用配方 |
| `Docs/贴图材质连线教程.md` | PBR 三通道贴图材质的手把手连线教程 |
| `Docs/PBR_Material_Spec_UE5.7.md` | PBR 材质物理参数规范（29KB） |
| `Docs/OPT_Render_UE5.7_2026-11-09.md` | UE5.7 光照与后处理调研（20KB） |
| `Docs/HANDOVER.md` | 本文档 |

## 八、快照与回滚

快照目录：`Saved/opt/snap/<时间戳>/`（含 `Start.umap` + `DefaultEngine.ini`）

关键备份：

```
Saved/opt/backup_20261109/Content/Start.umap   原始 4042640 B（22:00）
Saved/opt/backup_20261109/Start_step1.umap     22:32 中间态
Config/DefaultEngine.ini.bak_*                 各阶段 ini 备份
```

回滚方法：覆盖 `Content/Start.umap` + `Config/DefaultEngine.ini`。
删 `Content/_Opt` 不影响（有引用时会导致材质丢失）。
