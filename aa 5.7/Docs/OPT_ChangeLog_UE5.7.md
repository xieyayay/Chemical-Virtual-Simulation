# UE 5.7 虚拟仿真项目 · 视觉优化变更日志

> 项目：`D:\UE5\Chemistry\aa 5.7`（大学生参赛虚拟仿真 · 化学实验室）
> 引擎：UE 5.7.4 / DX12 SM6 / `r.Substrate=True` / Lumen + VSM
> 记录原则：只记**实际执行并保存成功**的改动，参数值必须能在资产里复查。
> 每步之间等效果确认再走下一步，禁止一次改多个变量。

---

## 0. 原始基线（回退锚点）

| 项 | 值 |
|---|---|
| `Content/Start.umap` | 4,042,640 B（2026-11-09 22:00） |
| `Config/DefaultEngine.ini` | 37,533 B |
| 备份位置 | `Saved/opt/backup_20261109/` |
| 灯光 | 全部新建默认值：Spot/Point = 8 cd、Rect = 25.133 lm、Directional = 10 lux，全部 6500K |
| 后处理 | **0 个 PostProcessVolume** |
| 材质 | `models/material/` 下纯色常量材质（white/black/gray/red/...），无粗糙度/法线控制 |
| Nanite | 306/306 个网格组件未启用 |

回退方法：覆盖 `Start.umap` + `DefaultEngine.ini` 即可，`Content/_Opt/` 删不删都不影响画面（无引用时）。

---

## 1. 光照与视觉的物理基线（后面每一步都靠这个判断）

### 1.1 照度

```
点光源 / 聚光：E = I / d²          （I: candela, d: 米）
面光源：      E = Φ / A · cosθ     （Φ: lumen, A: 面积 m²）
```

天花开到工作面约 4.5 m 时：

| 目标照度 | 所需 I（cd） |
|---|---|
| 30 lux（走廊级） | 600 |
| 70 lux（看得清台面） | 1400 |
| 150 lux（实验操作） | 3000 |
| 300 lux（GB 50034 教学用房） | 6000 |

**原始 8 cd 在 4.5 m 处只有 0.4 lux** —— 等于没开灯，这是"看起来假"的第一因。

### 1.2 材质可见性

```
L_out = f_r(材质) × L_in(入射光)
```

**没有方向性入射光，PBR 的高光和粗糙度差异全部为零。**
这就是为什么先换 86 个材质槽完全看不出变化 —— 不是材质没生效，是光照不足让差异无法显现。

顺序结论：**先有光，再谈材质**。

### 1.3 曝光

```
Exposure = 1 / (2^(EV100 + ExposureCompensation))
B = Exposure × L
```

- `Manual` 模式下 **EV100 = 0**（除非开 Apply Physical Camera Exposure）
- `Exposure Compensation` 每 +1 = 亮 2 倍，+2 = 亮 4 倍
- 自动曝光默认开启，且对 Level Viewport 与 Asset Editor 视口都生效

---

## 2. 变更日志

### Step 1 · 白色系材质（2026-11-09 23:05:34）

**目的**：验证"材质替换通道是否通"，选面积最大、风险最低的不透明白色系。

| 项 | 内容 |
|---|---|
| 母材质 | `Content/_Opt/M_Opt_Surface`（重建） |
| 结构 | **纯 4 参数**：VectorParameter `BaseColor` → Base Color；ScalarParameter `Roughness` → Roughness；`Metallic` → Metallic；`Specular` → Specular |
| 节点数 | 4 个表达式，**不含** Noise / WorldPosition / TextureSample / AppendVector |
| Blend / Shading | OPAQUE / DEFAULT_LIT / TwoSided=False |
| 实例 | `MI_Opt_white`（0.82, 0.82, 0.81 / R 0.45 / M 0 / S 0.50）、`MI_Opt_white1`（0.78 / R 0.42 / 0 / 0.50） |
| 替换范围 | **45 槽**：`white` 37 + `white1` 8 |
| 未动 | 灯光、后处理、雾、玻璃、gray/black、彩色材质 |
| 关卡大小 | 4,037,051 B |

**关键决策**：母材质去掉了噪声节点。理由：`r.Substrate=True` 下，Noise + WorldPosition + 空 TextureSample 任一编译失败，引擎会把整个材质槽 fallback 成灰色默认材质，118 个槽会一起变灰。宁可粗糙度空间变化少一点，也不能翻车。

---

### Step 2 · 灰系与黑色材质（2026-11-09 23:10:09）

母材质复用 `M_Opt_Surface`（同一套 4 参数）。

| 材质 | 槽数 | BaseColor | Roughness | Metallic | Specular |
|---|---|---|---|---|---|
| `black` | 19 | 0.025 | 0.55 | 0 | 0.35 |
| `gray2` | 15 | 0.340 | 0.48 | 0 | 0.45 |
| `gray` | 2 | 0.380 | 0.48 | 0 | 0.45 |
| `gray4` | 2 | 0.220 | 0.52 | 0 | 0.45 |
| `gray1` | 1 | 0.420 | 0.45 | 0 | 0.45 |
| `gray3` | 1 | 0.280 | 0.50 | 0 | 0.45 |
| `gray6` | 1 | 0.180 | 0.55 | 0 | 0.45 |
| **合计** | **41** | | | | |

关卡大小 4,038,817 B。累计 86 槽。

**观察结果**：视觉上几乎无变化。原因见 §1.2 —— 光照不足，材质差异不可见。

---

### Step 3 · 灯光调到物理照度（2026-11-09 23:17:55）★ 效果最直观的一步

只改灯，材质/后处理/雾/天光全部不动。

| 灯 | 数量 | 原值 | 新值 | 色温 | VolumetricScattering |
|---|---|---|---|---|---|
| DirectionalLight | 1 | 10 Lux | **250 Lux** | 6500 → **5500K** | 1.0 → 0.15 |
| SpotLight（含 SpotLight7） | 7 | 8 / 1.027 cd | **1200 cd** | 6500 → **3800K** | 1.0 → 0.10 |
| PointLight | 1 | 8 cd | **1600 cd** | 6500 → **4000K** | 1.0 → 0.10 |
| RectLight | 5 | 25.133 lm | **2200 lm** | 6500 → **5000K** | 1.0 → 0.15 |

全部 `use_temperature=True`、`cast_shadows=True`。

关卡大小 4,039,884 B。

**为什么这次不会翻车**：自动曝光保持开启（原始状态），它会把画面平均亮度拉回中灰。提灯光只增加**对比度与色温分离**，不改变整体亮度。上一轮过曝是因为同时锁死了手动曝光。

**效果（用户确认）**：暖色层次、光斑衰减、材质高光三者同时出现，直观。

---

### Step 4 · 玻璃组（2026-11-09 23:28:46）

只换 `/Game/models/material/glass` 与 `glass3`，`MI_Glass_01a`（DekoClass 46 槽）不动。

| 项 | 内容 |
|---|---|
| 母材质 | `M_Opt_Glass`：TRANSLUCENT / TwoSided / `TLM_SURFACE` |
| 参数 | `GlassTint` → BaseColor、`Roughness` → Roughness、`Specular` → Specular、`Opacity` → Opacity、`Refraction` → Refraction |
| 实例 | `MI_Opt_glass`（R 0.030 / Spec 0.532 / Op 0.12 / Refr 1.020）、`MI_Opt_glass3`（R 0.025 / Op 0.10） |
| 替换 | **30 槽** |
| 关卡大小 | 4,040,920 B |

累计 116 槽。

**第一版做错的地方**：`GlassTint` 给了 `(0.02, 0.03, 0.035)`。在半透明材质里 BaseColor 是**透射色**，不是 albedo —— 这个值意味着 98% 的光被吸收，结果玻璃像黑曜石/实心树脂，用户反馈"太厚、透光不好"。

---

### Step 4b · 修玻璃厚度与透光（2026-11-09 23:38:32）★ 关键概念修正

| 参数 | Step 4 | Step 4b |
|---|---|---|
| `GlassTint`（透射色） | (0.02, 0.03, 0.035) | **(0.93, 0.96, 0.94)** |
| `Opacity` | 常量 0.12 | **Fresnel 驱动**：正面 0.03 / 边缘 0.85 |
| `Refraction` | 1.020 | 1.020 |
| `Specular` | 0.532 | 0.532 |
| `Roughness` | 0.030 | 0.030 |
| 半透明光照模式 | 默认 Volumetric | **`TLM_SURFACE`** |

节点结构：

```
ScalarParameter OpacityCore (0.03) ┐
                                   ├─ LinearInterpolate ──► Opacity
ScalarParameter OpacityEdge (0.85) ┘
              Fresnel(Exp=5, BaseReflect=0.04) ──► Alpha
```

**两条必须记住的规则**：

1. **半透明材质的 BaseColor = 透射色，不是 albedo。**
   无色玻璃要接近白 (0.9+)，有色溶液才是低值。给 0.02 = 吸收 98% 光 = 黑玻璃。
2. **玻璃的 Opacity 必须由 Fresnel 驱动。**
   常量 Opacity 会让正面和侧面一样透明 —— 那是玻璃纸/赛璐珞，不是玻璃。
   正面 0.03（几乎全透）+ 边缘 0.85（掠射角全反射）才是菲涅耳曲线的形状。

**踩坑记录**：`unreal.TranslucencyLightingMode.TLM_SURFACE_FORWARD_SHADING` 在 5.7 Python 里不存在，
正确枚举是 **`TLM_SURFACE`**。`allow_front_layer_translucent_lighting` 也不是 `Material` 的属性，赋值会报 fail（无害）。

关卡大小 4,040,920 B，30 槽重新绑定成功。

---

### Step 5 · 彩色材质组（2026-11-09 23:51:46）

母材质沿用 `M_Opt_Surface`。**47 槽**。

| 材质 | 槽数 | BaseColor | Roughness | 实际挂在什么物体上（采样） |
|---|---|---|---|---|
| `red` | 18 | (0.48, 0.04, 0.04) | 0.35 | `miehuoq119`（**灭火器钢瓶**）、`jiaotoudiguan*`（**胶头滴管的橡胶头**）、`Circuit_Breaker`（按钮） |
| `green` | 14 | (0.04, 0.18, 0.07) | 0.35 | `shoutao`（**手套**）、`shuilongtou`（水龙头）、`Circuit_Breaker` |
| `red1` | 6 | (0.42, 0.05, 0.05) | 0.38 | `Merge_90E6BFE5..E9`、`BP_interact_Child14` |
| `green2` | 4 | (0.03, 0.14, 0.06) | 0.35 | `Merge6/7`、`wuchenzhi_Box001`（无尘纸盒） |
| `blue` | 2 | (0.02, 0.05, 0.24) | 0.35 | `Merge6/7` |
| `green3` / `purple` / `purple1` | 各 1 | — | 0.35–0.38 | `shoutao2` / `zhiyangji`（制氧机）/ `BP_interact_Child22` |

关卡大小 4,041,990 B。累计 **163 槽**。

**诚实的局限**：同一个材质名 `red` 同时挂在「灭火器钢瓶（烤漆金属，R 应 0.25）」和「胶头滴管的橡胶头（R 应 0.7）」上。
单一 MI 无法同时满足两者，取 0.35 折中。要精确必须拆成两个材质实例并按 actor 单独挂 —— 那属于逐物件精修，不在本轮范围。

---

### Step 5b · 颜色误伤修正（2026-11-09 23:59:37）★ 重要教训

**误伤现象**：电热板外壳由原色变亮绿、加热盘网格变红（用户截图确认）。

**根因**：Step 1/2/5 的 BaseColor 全部是**按材质名字猜的**。实测原材质真实颜色后，名字的误导程度如下：

| 材质名 | 我猜的值 | **实际值** | 偏差 |
|---|---|---|---|
| `gray5` | 0.48 灰 | **(0.977, 0.293, 0.018) 橙色** | 完全错 |
| `gray6` | 0.18 灰 | **(0.227, 0.213, 0.890) 蓝色** | 完全错 |
| `gray2` | 0.34 灰 | **(0.092, 0.088, 0.094)** | 亮了 3.7 倍 |
| `gray4` | 0.22 灰 | **(0.074, 0.065, 0.077)** | 亮了 3 倍 |
| `green2` | 0.03, 0.14, 0.06 绿 | **(0.994, 0.880, 0.588) 米黄** | 完全错 |
| `green3` | 0.08, 0.26, 0.10 绿 | **(0, 0, 0) 纯黑** | 完全错 |
| `blue2` | 0.06, 0.14, 0.42 蓝 | **(0.604, 0.613, 0.790) 淡蓝紫** | 偏亮 |
| `pink` | 0.55, 0.24, 0.27 粉 | **(0.990, 0.153, 0.734) 洋红** | 色相错 |
| `pink1` | 0.62, 0.30, 0.32 粉 | **(0.220, 0.055, 0.569) 紫** | 色相错 |
| `white1` | 0.78 灰白 | **(1.000, 0.963, 0.894) 暖白** | 偏冷 |
| `glass` | (0.02,0.03,0.035) | **(0.544, 0.544, 0.544)** | Step4 的"黑玻璃"就是这么来的 |

**结论：`/Game/models/material/` 下的材质名与颜色没有任何对应关系**，必须从资产里读。

#### 正确的读取 API（试了 4 条路才通）

```python
# 唯一可靠路径：
mat = EAL.load_asset("/Game/models/material/white.white")
c = MEL.get_material_default_vector_parameter_value(mat, "Param")   # 普通材质
c = MEL.get_material_default_vector_parameter_value(mat, "基础颜色")  # glass 系

# 以下全部失败，不要再试：
# MEL.get_material_expressions(mat)              -> 方法不存在
# MEL.get_material_expression(mat, i)            -> 抛异常
# MEL.get_material_property_input_node(mat, ...)  -> 部分材质返回 None
# mat.get_editor_property("editor_only_data")    -> 返回 MaterialInterfaceEditorOnlyData，无 base_color
# mat.get_editor_property("base_color")          -> 属性不存在
```

所有材质的 BaseColor 都接在名为 **`Param`** 的 VectorParameter 上（glass 系是 **`基础颜色`**）。

#### 修复动作

1. 用真实颜色重建全部 29 个 MI（颜色 100% 等于原材质，只改 Roughness / Metallic / Specular）
2. 删除重建会导致 actor 上的旧引用失效 → 必须**重新绑定**：扫描槽位，按 `MI_Opt_<name>` 反查名，`set_material` 重新挂 —— 实际重绑 **167 槽**
3. 读不到颜色的（`jingshixian` 是 Texture2D 不是 Material、各种哈希材质、`anquanchukou_mat`）保持原材质不动

关卡大小 4,042,134 B。

**关于电热板**：外壳的深绿 `(0.018, 0.090, 0.038)` 和网格的红 `(0.381, 0.004, 0.016)` **就是原材质的真实颜色**，色相没有被我改动。
看起来变鲜艳是因为：① 材质从"无高光的纯常量"变成有 Specular 的 PBR；② 灯光从 8 cd 提到 1200 cd。
如果这个设备本来就该是白色/金属灰，那属于**模型赋色错误**，需要按 actor 单独指定材质，不能按材质名批量改。

---

### Step 6 · 后处理体积（2026-11-10 00:04:44）

创建 `PP_Opt`（unbound / enabled / blend_weight 1）。**只 override 8 项**：

| 参数 | 引擎默认 | 设定 | 作用 |
|---|---|---|---|
| `BloomIntensity` | 0.675 | **0.45** | 降低辉光，避免画面发糊 |
| `BloomThreshold` | **−1.0** | **0.9** | 只有超过 0.9 的亮度才参与 Bloom |
| `VignetteIntensity` | 0.400 | **0.35** | 轻微暗角 |
| `FilmGrainIntensity` | 0.0 | **0.02** | 胶片颗粒，消数字感 |
| `SceneFringeIntensity` | 0.0 | **0.18** | 轻微色散 |
| `ColorContrast` | **(1,1,1,1)** | **(1.08,1.08,1.08,1)** | 对比度 +8% |
| `ColorSaturation` | (1,1,1,1) | **(1.08,1.08,1.08,1)** | 饱和度 +8% |
| `Sharpen` | 0.0 | **0.15** | 轻微锐化 |

**曝光链检查（脚本内自动验证）**：`AutoExposure*` / `LocalExposure*` / `WhiteTemp` 的 override 项 = **无** ✓

关卡大小 4,050,325 B。

#### 两个新踩到的坑

**坑 1：`ColorContrast` / `ColorSaturation` 是乘数，不是偏移量**

默认值 `(1,1,1,1)`，表示"乘 1 倍 = 不变"。
我前面几轮写的是 `(0.06,0.06,0.06,1)` 和 `(0.10,0.10,0.10,1)` —— 那是把对比度压到 **6% / 10%**，画面必然糊成一片灰。这是"灰蒙蒙"的第二个来源（第一个是雾）。
正确写法：`1.08` = 提高 8%。

**坑 2：`BloomThreshold` 引擎默认是 −1.0**

`-1` 意味着**任何亮度**都参与 Bloom 计算，相当于全画面泛光。这也是"画面糊"的原因之一。
室内场景合理值：`0.8 – 1.2`。

---

### Step 7 · 手套统一 + 降饱和 + 白平衡修正（2026-11-10 00:20:51）

| 动作 | 内容 |
|---|---|
| 手套 | `shoutao2` 挂的是 `MI_Opt_green3`，而 **`green3` 的原色是 (0,0,0) 纯黑**（名字叫 green，实际是黑）→ 改为 `MI_Opt_green` |
| 降饱和 | `ColorSaturation` 1.08 → **0.90** |
| 白平衡 | 上一版设 `WhiteTemp 5100` 是**方向错误**：UE 里 WhiteTemp 越低画面越暖。已关闭 override，回引擎默认 6500 中性 |

**教训**：`WhiteTemp` 是"白点色温"，数值低 = 画面暖。要画面变冷应该**调高**（7500+），不是调低。

### Step 7b · 水龙头镀铬（2026-11-10 00:20:51）

`shuilongtou_Submesh1–6` 原来挂 `MI_Opt_green`（绿色塑料水龙头）。新建 `MI_Opt_chrome`：

```
BaseColor 0.92 / Roughness 0.12 / Metallic 1.0 / Specular 0.5
```

6 个槽全部替换。这是场景里第一个真正的金属材质。

### Step 8 · SpotLight 色温（2026-11-10 00:29:06）

6 盏 SpotLight：**3800K → 4800K**（用户反馈"太暖"）。

当前四类灯色温：SpotLight 4800K / PointLight 4000K / RectLight 5000K / DirectionalLight 5500K。

> 注：此后灯光由用户手动微调，脚本不再覆盖。

### Step 9 · 粗糙度空间变化试验（2026-11-10 00:39:53）

**目的**：纯色 + 恒定 Roughness 是"塑料板感"的最后来源。真实表面粗糙度有 ±30% 的空间波动。

**做法**：新建 `M_Opt_Surface_Var`，在纯参数版基础上加噪声调制：

```
WorldPosition ──► Noise(scale 0.0015, levels 3, out 0-1) ──► Lerp.Alpha
Roughness × 0.72 ──► Lerp.A
Roughness × 1.28 ──► Lerp.B
Lerp ──► Roughness 引脚
```

**验证结果**：日志 **无 `Failed to compile`**，引脚 `MP_ROUGHNESS ← MaterialExpressionLinearInterpolate` 正常。
→ 说明 `Noise` + `WorldPosition` 在 `r.Substrate=True` 下**编译完全正常**，此前"节点导致编译失败变灰"的假设不成立（真正原因是颜色误伤 + 雾 + 对比度乘数）。

**范围**：只换 3 个 actor 试验 —— `miehuoq119`（灭火器）、`Table_Shelf_EXP_Table-shelf_001`（实验台架）、`adwda`。其余 163 槽不动。

关卡已保存。

---

### Step 10 · 粗糙度变化推广到全局（2026-11-10 00:47:41）

把 27 个 `MI_Opt_*` 的父材质从 `M_Opt_Surface` 换成 `M_Opt_Surface_Var`。

**风险控制**：换父材质可能导致参数丢失（变默认白/灰）。换完逐项读回验证，**颜色零丢失**：

```
white   base=(0.8001,0.7913,0.8030)  R=0.450
gray5   base=(0.9771,0.2927,0.0183)  R=0.450   ← 橙色还在
gray6   base=(0.2273,0.2131,0.8896)  R=0.550   ← 蓝色还在
chrome  base=(0.9200,0.9200,0.9300)  R=0.120
```

### Step 11 · 修两个让变化"看不见"的 bug（2026-11-10 00:54:41）

用户反馈"白墙变化不大"，查节点图发现是两个 bug：

| Bug | 现象 | 修复 |
|---|---|---|
| 噪声 `scale=0.0015` | 特征波长 666 单位（6.6 米），一整面墙只有一个周期，看不出 | 改 **0.008**（波长 ≈1.25 米） |
| Lerp 上下界写成 `Constant 0.72/1.28` | **`RoughnessVar` 参数没接进图，调它完全无效** | 改为 `Roughness × (1 − var)` / `Roughness × (1 + var)` 真正接线 |

同时 `white` var → 0.60、`white1` var → 0.55。

**重建方式**：只 `delete_all_material_expressions` 清空节点、**不删资产**，这样 27 个 MI 的父材质引用不会断。

### Step 12 · 回调幅度（2026-11-10 00:59:55）

用户反馈"太明显像湿掉"。

**根因**：`var=0.60` 时白墙粗糙度最低到 **0.18**，低于 0.2 就是接近镜面，灯光会聚成小高光斑 —— 这是水渍/油污的视觉特征。真实白漆墙粗糙度几乎均匀，波动只在 ±0.05 量级。

| 材质 | var |
|---|---|
| `white` | 0.60 → **0.20** |
| `white1` | 0.55 → **0.18** |
| 其余 26 个 | 0.28 → **0.14** |

白墙实际范围变为 **0.36 ~ 0.54**，全程不低于 0.3，不会再出现镜面斑。

**规则**：`Roughness × (1 − var)` 不能低于 **0.25**，否则室内灯光下会出现湿渍感。

---

## 3. 三次翻车的根因（务必不要重犯）

### 3.1 全场景灰蒙蒙

**现象**：均匀中灰、无对比、物体像蒙纱。
**根因**：`ExponentialHeightFog` 的 `FogDensity` 单位是 **1/cm**。
设 `0.008` 时，3 米处透射率 `exp(-0.008 × 300) = 9%`，20 米处几乎为 0。
再叠加 12 盏灯的 `VolumetricScatteringIntensity = 1.0`，雾被照成灰白色。
**结论**：室内场景 `FogDensity` 应 ≤ 0.0005，且灯的 vol 强度应 ≤ 0.2。

### 3.2 全屏过曝纯白

**根因**：同时做了两件互相放大的事 ——
1. `PPV` 设为 `MANUAL` + `ExposureCompensation 9.5`
2. `Config/DefaultEngine.ini` 写入 `r.DefaultFeature.AutoExposure=0`

`r.DefaultFeature.AutoExposure=0` 会关闭整个自动曝光系统，曝光恒为 1.0（EV100=0），
`B = 1 × L`，场景中任何 `L > 1` 的表面直接冲白，PPV 的设定根本没参与运算。

**结论**：不要关 `r.DefaultFeature.AutoExposure`。要调亮度用 **Exposure Compensation**，不要用手动锁 EV100。

### 3.3 改了 PPV 却"没变化"

**根因**：编辑器视口有独立的曝光覆盖。

> "Each editor viewport provides an option to **override default auto exposure settings or ones set in your Post Process Volume**. Access the exposure override from the **View Mode dropdown**... disable the checkbox next to **Game Settings** or **Auto** to use the EV100 slider."

View Mode 下拉里的 `Game Settings` **未勾选**时，视口用 EV100 滑块，直接盖掉 PPV。
**结论**：在编辑器里判断 PPV 效果，必须先确认 `Game Settings` 勾上；否则只能在 PIE 里看。

---

## 4. 可复用配方

### 4.1 室内实验室灯光配方（已验证有效）

```
DirectionalLight   250 Lux   5500K  vol 0.15   ← 窗光/天光补充
SpotLight（筒灯）  1200 cd   3800K  vol 0.10   ← 主体照明，桌面约 60-70 lux
PointLight         1600 cd   4000K  vol 0.10   ← 局部补光/墙角
RectLight（灯带）  2200 lm   5000K  vol 0.15   ← 顶面柔光，打亮大面积
```

规则：
- 色温分层是"真实感"的关键 —— 筒灯暖（3800K）、灯带中（5000K）、天光冷（5500K），不要全部 6500K
- 灯数 ≥ 6 时不要开 MegaLights（5.7 仍是 Beta）
- `VolumetricScatteringIntensity` 一律 ≤ 0.2，否则室内起雾

### 4.2 PBR 参数表（化工场景）

| 材质 | BaseColor（线性） | Roughness | Metallic | Specular |
|---|---|---|---|---|
| 白色烤漆/石膏 | 0.82 | 0.45 | 0 | 0.50 |
| 灰水泥/喷粉金属 | 0.34–0.42 | 0.48 | 0 | 0.45 |
| 黑色橡胶/哑光塑料 | 0.025 | 0.55 | 0 | 0.35 |
| 钠钙玻璃 | 透明 | 0.03 | 0 | **0.532**（IOR 1.52） |
| 硼硅 Pyrex | 透明 | 0.02 | 0 | **0.459**（IOR 1.474） |
| 纯水 / 乙醇 | 透明 | 0–0.02 | 0 | **0.255 / 0.292** |
| 不锈钢（拉丝） | 0.56 | 0.35 | **1.0** | — |
| 陶瓷釉面台面 | 0.82 | 0.10 | 0 | 0.50 |

换算：`F0 = ((n-1)/(n+1))²`，`Specular = F0 / 0.08`

### 4.3 母材质模板（零编译风险）

```
VectorParameter "BaseColor"  ──► Base Color
ScalarParameter "Roughness"  ──► Roughness
ScalarParameter "Metallic"   ──► Metallic
ScalarParameter "Specular"   ──► Specular
```

**不要**在 Substrate 下往母材质里塞 Noise / WorldPosition / 空 TextureSample / AppendVector，
一旦编译失败，整槽 fallback 灰材质，且日志在 headless 下不报。空间变化宁可用"每个 MI 单独给值"来近似。

---

## 5. 当前状态（截至 Step 3）

| 项 | 状态 |
|---|---|
| 材质 | 86 槽已替换：white/white1（45）+ gray 系/black（41） |
| 待替换 | `glass` 27、`glass3` 3、`MI_Glass_01a` 46、`red` 18、`green` 14、`red1` 6、`green2` 4、`blue` 2、彩色系若干 |
| 灯光 | 13 盏全部物理照度（Step 3） |
| 后处理 | **无 PPV**（原始状态） |
| 雾 | 原始状态 |
| 天光 | 原始状态（`SLS_SPECIFIED_CUBEMAP` + `RealTimeCapture` + `TX_Cubemap_01a`） |
| Nanite | 未启用 |

## 6. 后续计划

- **Step 4**：玻璃组（`glass` 27 + `glass3` 3），半透明母材质，`Specular 0.532`（IOR 1.52），`Refraction 1.02`
- **Step 5**：`MI_Glass_01a` 46 槽（DekoClass 体系，单独评估）
- **Step 6**：彩色材质（red/green/blue，语义不明，需先确认哪些是液体）
- **Step 7**：后处理体积（Bloom / 暗角 / 颗粒 / 色彩分级）—— 最后做，因为它是"调味"，不是"打底"

---

## 附：可用脚本

| 脚本 | 作用 |
|---|---|
| `Saved/opt/step1_surface.py` | 重建纯参数母材质 + 替换 white 系 |
| `Saved/opt/step2_gray_black.py` | 替换 gray/black 系 |
| `Saved/opt/step3_lights.py` | 13 盏灯调物理照度 |
| `Saved/opt/revert_to_baseline.py` | 材质还原 + 后处理最小化（排查用） |
| `Saved/opt/adjust_exposure.py` | 曝光调整（当前未使用，PPV 不存在） |

执行方式（必须用正斜杠，反斜杠会被 UE 当转义）：

```powershell
$env:OPT_APPLY="1"
& "D:\UE\UE_5.7\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" `
  "D:/UE5/Chemistry/aa 5.7/aa.uproject" `
  -run=pythonscript `
  "-script=D:/UE5/Chemistry/aa 5.7/Saved/opt/step4_glass.py" `
  -EnablePlugins=PythonScriptPlugin -unattended -nosplash -nullrhi -stdout
```

执行前必须先关闭编辑器，否则两个实例会互相覆盖关卡文件。
