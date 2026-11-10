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

### Step 14 · Local Exposure（2026-11-10 10:01:25）

| 参数 | 默认 | 设定 |
|---|---|---|
| `LocalExposureHighlightContrastScale` | 1.0 | **1.25** |
| `LocalExposureShadowContrastScale` | 1.0 | **1.25** |
| `LocalExposureDetailStrength` | 1.0 | **0.70** |
| `LocalExposureMiddleGreyBias` | 0.0 | 0.0 |

用户反馈"感受不大"，故后续在 Step 15 整体关闭。

### Step 15 · 真实/自然档（2026-11-10 10:29:48 + 10:30:32）

**调研结论（如实记录）**：公开网络上**不存在**权威的"UE5 真实感后处理数值模板"。

核实过的三类来源：
- Epic 官方 [Post Process Effects](https://dev.epicgames.com/documentation/en-us/unreal-engine/post-process-effects-in-unreal-engine?application_version=5.7) —— 只有参数定义与默认值，无推荐组合
- [Game-Ace 电影级制作指南](https://game-ace.com/blog/unlocking-cinematic-quality-in-unreal-engine-5-6/) —— 只有方法论（bloom 别太强 / 颗粒要轻 / 暗角色散要克制），无具体数字
- 各类教程/论坛 —— 个人偏好，互相矛盾

**因此这套值是依据「引擎默认值 + 摄影原理」推导的，不是抄来的。**
核心原则：**"真实"靠少干预。后处理参数越多越强，画面越假。**

| 参数 | 改前 | 真实档 | 依据 |
|---|---|---|---|
| `BloomIntensity` | 0.45 | **0.30** | 真实镜头只在极亮处溢光 |
| `BloomThreshold` | 0.90 | **1.00** | 挡住中高光参与泛光 |
| `VignetteIntensity` | 0.35 | **0.15** | 真实视角几乎无暗角 |
| `FilmGrainIntensity` | 0.02 | **0.01** | 仅用于打散数字洁净感 |
| `SceneFringeIntensity` | 0.18 | **0.00** | 真实相机无明显色散 |
| `Sharpen` | 0.45 | **0.20** | 过头产生白边，反而不真实 |
| `ColorContrast` | 1.08 | **1.02** | 只留一点 |
| `ColorSaturation` | 用户手调 | **保留用户值** | 见下 |
| `MotionBlurAmount` | 0 | 0 | 保持关闭 |
| `LocalExposure*`（三项） | override 开 | **override 全关** | 真实相机没有局部动态压缩 |
| `WhiteTemp / WhiteTint` | override 关 | override 关 | 保持 6500 中性 |

保留不动：`BloomMethod = SOG`、`FilmSlope/Toe/Shoulder = 0.88 / 0.55 / 0.26`（Epic 调过的电影曲线）。

#### 教训：写参数前必须先读现值

应用真实档时读到的 `ColorSaturation` 是 **`(0.752475, 0.760000, 0.752475)`** —— 用户自己调过的（我上次设的是 0.90）。真实档要写 `1.0`，等于把用户降下去的饱和又拉回来。

已恢复用户值。`Sharpen` 同样：我设 0.45，用户调到 0.70，真实档改成 0.20 会变软。

**规则：任何批量参数脚本，写之前先把当前值打印出来并判断是否已被用户手动修改过；发现用户改动，保留而不是覆盖。**

---

### Step 16 · 阶段二：反射 / AO / 接触阴影（2026-11-10 10:39:59）

**A. `Config/DefaultEngine.ini` 追加（需重启生效）**

```ini
r.ContactShadows=1
r.Lumen.Reflections.Quality=1
r.Lumen.Reflections.MaxRoughnessToTrace=0.5   ; 默认 0.4，让更多粗糙材质也参与反射
r.SSR.Quality=4
r.AOQuality=2
r.Streaming.PoolSize=3000
```

备份：`DefaultEngine.ini.bak_before_reflect`

**B. 灯级 `ContactShadowLength`（立即生效）**

13 盏灯全部设 `contact_shadow_length = 0.03`（3 cm）。Mobility 实测：DirectionalLight 与 SpotLight3 为 `MOVABLE`，其余 11 盏为 `STATIONARY`，均支持接触阴影。

只改这一个属性，**未触碰用户手动调整过的强度与色温**。

关卡大小 4,052,671 B。

**预期**：柜脚、凳脚、器材底部与地面/台面交界处出现一条紧贴的暗线，物体不再"浮"在表面上。

---

### Step 17 · 阴影距离与分辨率（2026-11-10 10:47:55）

用户反馈"阴影质量看不出效果"。查出关键漏项：**方向光的阴影覆盖距离**。

| 参数 | 旧 | 新 | 说明 |
|---|---|---|---|
| `DynamicShadowDistanceMovableLight` | **20000** | **4000** | 房间纵深仅约 30m，用 200m 覆盖等于把精度摊薄 6.7 倍 |
| `DistanceFieldShadowDistance` | 30000 | 4000 | 同上 |
| `DynamicShadowCascades` | 4 | 3 | |
| 局部光 `ShadowResolutionScale` | 1.0 | 1.5 | 12 盏 |

**结论**：方向光阴影距离对室内清晰度的影响，比采样数大一个数量级。

### Step 18 · 关闭 VSM，改用传统 Shadow Map（2026-11-10 10:59:34）

用户对比后选择"硬边清晰"的视觉风格。

**ini 变更**

```ini
r.Shadow.Virtual.Enable=0            ; 两处都改（RendererSettings + SystemSettings）
r.Shadow.MaxResolution=4096
r.Shadow.MaxCSMResolution=4096
r.Shadow.CSM.MaxCascades=3
r.Shadow.RadiusThreshold=0.01
r.AllowStaticLighting=False           ; 关键：消除"未构建光照"检查
r.Shadow.MaxSoftKernelSize=24         ; 给硬边加羽化
```

**灯属性变更**：13 盏全部 `Stationary → Movable`（DirectionalLight 与 SpotLight3 原本就是 Movable）。

#### 问题：切换后出现「光照需要重建（735 未构建对象）」+ 视口打印 `Preview`

**根因**：11 盏灯是 `Stationary`，需要 Lightmap 预计算。VSM 开启时引擎用虚拟阴影实时补偿，所以看不出来；**VSM 一关，预计算缺失，引擎退化成 Preview 模式**。

**解决**：两件事一起做才彻底 ——
1. `r.AllowStaticLighting=False`（项目级关闭静态光照，引擎根本不做"未构建"判定）
2. 所有灯 `Mobility → Movable`（Stationary 灯的间接光依赖预计算，残留隐患）

**教训**：**在 Lumen 项目里不该有 Stationary 灯**。Lumen 是全动态 GI，Stationary 只会带来 Lightmap 依赖和这类告警。

### Step 19 · 性能优化第一轮（2026-11-10 11:09:48）★ 有翻车

用户反馈"帧率偏低"。按配置推算阴影负载：

```
4096² × 13 盏 × 1.5² ≈ 4.9 亿像素/帧
```

| 动作 | 结果 |
|---|---|
| `MaxResolution` 4096 → 2048 | |
| `MaxCSMResolution` 4096 → 2048 | |
| `MaxSoftKernelSize` 24 → 12 | |
| `SSR.Quality` 4 → 2 | |
| `AOQuality` 2 → 1 | |
| `Lumen.Reflections.MaxRoughnessToTrace` 0.5 → 0.4 | |
| 12 盏局部光 `ShadowResolutionScale` 1.5 → 1.0 | |
| **RectLight ×5 `cast_shadows` → False** | **翻车点** |

#### 翻车：阴影几乎全部消失

**根因是三处叠加**：
1. `MaxSoftKernelSize=12` —— 软阴影核 12 像素，中小物体阴影被彻底抹掉（主因）
2. `RectLight ×5` 关投影 —— 面光提供的大范围柔和环境阴影全没了
3. `MaxResolution 2048` —— 边缘粗糙但不至于消失

**修复**：`MaxSoftKernelSize → 0`、`RadiusThreshold → 0.03`、`MaxResolution → 3072`，RectLight 投影由用户手动恢复。

**教训**：**`MaxSoftKernelSize` 是"让阴影消失"的隐形杀手**。它按像素扩散，在低分辨率下会把小阴影完全糊掉。室内场景应该用 0–4。

### Step 20 · 基于 ProfileVisualizer 数据的第二轮优化（2026-11-10 12:02:13）

用户提供了 `.profViz` 采集文件。二进制格式无法完整逆向（见附录），但**事件名全部提取成功（195 个）**，据此定位真实开销：

```
Nanite Cubemap UEDPIE_0_Start.RectLight   1536x1536   ← 面光 6 面立方体阴影
Nanite Cubemap UEDPIE_0_Start.RectLight2   768x768
Nanite Cubemap UEDPIE_0_Start.RectLight3-5 384x384
WholeScene split0 / split1 / split2       2040x2040   ← 方向光 CSM 3 级
WholeScene MovablePrimitives              多种尺寸     ← 每盏可移动灯
VolumetricCloud / VolCloudComposeOverScene            ← 室内体积云
TranslucencyLightingVolume / FilterTranslucentVolume 64x64x64 Cascades:2
GPUSkinCache_UpdateSkinningBatches + SKM_Quinn 4.6 万顶点
NiagaraGpuComputeDispatch
Nanite::Streaming / Readback / VisBuffer / BasePass
LumenScreenProbeGather / LumenReflections / UpdateLumenSceneBuffers
```

**依此执行的优化**：

| 动作 | 依据 |
|---|---|
| `DirectionalLight.cast_shadows → False` | CSM 3×2040² ≈ 1250 万像素，室内无意义 |
| `RectLight ×5.cast_shadows → False` | 5 盏 × 6 面立方体贴图 ≈ 1900 万像素 |
| 12 盏局部光 `ShadowResolutionScale → 0.5` | 阴影贴图面积 −75% |
| `VolumetricCloud` 隐藏 + `cast_cloud_shadows=False` | 室内不需要 |
| `MaxResolution 3072 → 2048`、`MaxCSMResolution 2048 → 1024` | |

预计阴影负载：**3000 万 → 340 万像素/帧（−88%）**。

关卡大小 4,052,134 B。

**profViz 里另外三条待办线索**（等 `stat unit` 数据决定是否动）：
- GPU 蒙皮（SKM_Quinn 4.6 万顶点/帧）
- Niagara GPU 粒子
- `TranslucencyLightingVolume`：30 个玻璃槽的 `TLM_SURFACE` 开销

---

### Step 21 · 还原 Step 20 的投影改动（2026-11-10 12:10:36）

用户反馈"现在的效果很差"，要求：**除 VolumetricCloud 与 12 盏局部光的 ShadowResolutionScale 外，其余全部还原**。

| 项 | 处理 |
|---|---|
| `DirectionalLight.cast_shadows` | False → **True（还原）** |
| `RectLight ×5.cast_shadows` | False → **True（还原）** |
| `r.Shadow.MaxResolution` | 2048 → **3072（还原）** |
| `r.Shadow.MaxCSMResolution` | 1024 → **2048（还原）** |
| 12 盏局部光 `ShadowResolutionScale` | **0.5（保留）** |
| `VolumetricCloud` | **保持隐藏 + 关投影（保留）** |

关卡大小 4,051,964 B。用户确认"现在没什么问题"。

#### 复盘：为什么关方向光/面光投影会让效果变差

方向光 250 lux 虽然强度不高，但它提供**整个空间的顶光基底**；关掉后只剩筒灯的局部照明，明暗关系塌陷。
面光的柔和包裹阴影同理——它不是"多余的光"，而是让物体与桌面产生接触关系的来源。

**教训：优化性能时，不能按"这盏灯看起来不亮"来判断是否该关它的投影**。投影的作用是建立空间关系，不是照明强度。

---

### Step 22 · 分区调色（2026-11-10 12:30:48）

在真实档基础上加胶片式分区响应，幅度 2–6%：

| 参数 | 值 | 意图 |
|---|---|---|
| `ColorSaturationShadows` | (1.06, 1.06, 1.06) | 暗部饱和 +6% |
| `ColorSaturationHighlights` | (0.96, 0.96, 0.96) | 高光饱和 −4% |
| `ColorContrastShadows` | (1.05, 1.05, 1.05) | 暗部对比 +5% |
| `ColorContrastHighlights` | (0.98, 0.98, 0.98) | 高光柔化 |
| `ColorGainShadows` | (0.98, 0.99, 1.02) | 暗部偏冷 |
| `ColorGainHighlights` | (1.02, 1.00, 0.98) | 高光偏暖 |

分区范围未改（`ShadowsMax=0.09` / `HighlightsMin=0.5`）。

### Step 23 · 玻璃光照模式（2026-11-10 12:31:03）

`M_Opt_Glass` 的 `TranslucencyLightingMode`：`TLM_SURFACE` → **`TLM_VOLUMETRIC_DIRECTIONAL`**。
省掉 profViz 里看到的 `TranslucencyLightingVolume` 逐像素查找。

### Step 24 · 清理未使用材质（2026-11-10 16:0x）

删除 **14 个**无引用资产：

```
M_Opt_Liquid / M_Opt_Surface / M_Opt_Surface_Tex
MI_Opt_Tex_Labset
MI_Opt_blue1 / blue2 / glass2 / gray5 / gray7 / green1 / green3
MI_Opt_jingshixian / pink / pink1
```

`_Opt` 剩余 26 个（3 个母材质 + 23 个实例）。

**重要发现**：`find_package_referencers_for_asset` 对已保存关卡的引用**有延迟**，`MI_Opt_Marble_White` 被误报为无引用（实际挂在 `shiyantai2` 上）。**删除前必须额外核对场景实际使用**。

### Step 25 · 体积雾排查（2026-11-10 16:20–17:00）★ 三个结论

#### 结论 1：旧的 ExponentialHeightFog 数据损坏

现象：所有参数读出来都正确（密度、颜色、`EnableVolumetricFog`、位置），但画面**完全无雾**。

**决定性判定法**：把 `FogDensity` 设成 **0.1**（1 米内完全遮挡的极端值）。
- 画面变化 → 组件正常，只是参数太稀
- **画面纹丝不动 → 组件没进渲染管线，已损坏，必须删除重建**

本项目就是后者。删除旧 Actor、`spawn_actor_from_class(unreal.ExponentialHeightFog, ...)` 重建后立即正常。

#### 结论 2：体积雾不适合这个场景

用户实测：**关掉体积雾反而有雾感**（普通指数雾生效），**打开体积雾反而变干净**。

技术原因：
- 普通雾的颜色来自 `FogInscatteringLuminance`（固定值）
- 体积雾改用「3D 网格 + 灯光散射」，**不再使用那个固定颜色**
- 灯光照不到的地方，体积雾几乎不显示 → 画面变干净

光柱亮度 = `灯照度 × VolumetricScatteringIntensity`。30 米大空间 + 800 cd 灯，5 米外就衰减到看不见。

**体积雾的适用条件是「小空间 + 单点强光 + 明显遮挡」**（如光束穿过百叶窗），不适用于均匀多灯的大房间。

#### 结论 3：普通指数雾是性价比最高的空气感方案

零开销、不受灯光影响、远处自然衰减。最终配置：

```
Enable Volumetric Fog = False
FogDensity            = 0.0008
FogHeightFalloff      = 0.12
FogInscatteringLuminance = (0.52, 0.58, 0.70)
FogMaxOpacity         = 0.85
13 盏灯的 VolumetricScatteringIntensity = 0.15
```

---

## 附录 A · 通过 RemoteControl API 控制编辑器（已打通，可复用）

### A.1 一次性配置

**1. `aa.uproject` 启用两个插件**

```json
{ "Name": "RemoteControl", "Enabled": true },
{ "Name": "RemoteControlWebInterface", "Enabled": true }
```

**2. 创建 `Config/DefaultRemoteControl.ini`**

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

**三个容易搞错的地方**（都踩过）：
- 类定义是 `UCLASS(config = RemoteControl)` → 文件必须是 **`DefaultRemoteControl.ini`**，不是 `DefaultEngine.ini`
- 模块名是 `RemoteControlCommon`，段名是 **`[/Script/RemoteControlCommon.RemoteControlSettings]`**
- 属性名是 **`bAllowConsoleCommandRemoteExecution`**（不是 `bAllowConsoleCommand`）

**3. 启动编辑器**

```
UnrealEditor.exe "aa.uproject" /Game/Start -RCWebControlEnable -RCWebInterfaceEnable
```

端口 30010，约 9–24 秒就绪。

### A.2 调用方式

```powershell
# 执行任意 Python（最强，能做任何事）
$b = @{
  objectPath = "/Script/PythonScriptPlugin.Default__PythonScriptLibrary"
  functionName = "ExecutePythonCommand"
  parameters = @{ PythonCommand = "import unreal; unreal.log('ok')" }
} | ConvertTo-Json -Depth 8
Invoke-RestMethod -Uri "http://127.0.0.1:30010/remote/object/call" -Method Put -Body $b -ContentType "application/json"

# 读/写任意属性
Invoke-RestMethod -Uri "http://127.0.0.1:30010/remote/object/property" -Method Put ...

# 可用端点：/remote/object/call、/property、/describe、/batch、/preset/:preset/function/:fn
```

**已知限制**：
- `get_pie_world()` / `GameplayStatics.get_game_world()` 在 5.7 Python 里**不存在**，PIE 世界拿不到
- **编辑器视口不在前台时引擎降频**，`ProfileGPU` 只记录到 `SlateWidgetRender`（0.5ms），场景 pass 为空 —— 所以 headless / 后台采集不到有效 GPU 数据
- `-run=pythonscript` 即使不加 `-nullrhi` 也是 **Null RHI**（日志 `verbatimrhiname="Null"`），无 GPU

### A.3 `.profViz` 格式（未能完整逆向）

路径：`%LOCALAPPDATA%\UnrealEngine\5.7\Saved\Logs\profileViz\`

二进制流，每个节点大致是「3 个 double + uint32 childCount + uint32 nameLen + name」，但**名称长度非 4 字节对齐导致字段偏移逐节点漂移**，无法用固定步长线性扫描。

**可用做法**：用正则 `[\x20-\x7e]{6,}` 提取全部事件名（本项目得到 195 个），事件名本身就足以定位开销来源。
**不建议再投入**：完整逆向收益低，需要数值时直接让用户在 Output Log 看 `ProfileGPU` 的表格。

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

## 5. 当前状态（截至 Step 20）

### 5.1 材质

| 项 | 状态 |
|---|---|
| 不透明材质 | **163 槽** PBR 化，父材质 `M_Opt_Surface_Var`（5 参数 + 世界坐标噪声调制粗糙度） |
| 颜色来源 | **全部取自原材质真实值**（`get_material_default_vector_parameter_value`），零猜测 |
| 玻璃 | **30 槽**（`glass` 27 + `glass3` 3），`M_Opt_Glass`，Fresnel 驱动 Opacity，`TLM_SURFACE` |
| 金属 | `MI_Opt_chrome` 镀铬（BaseColor 0.92 / R 0.12 / Metallic 1.0），水龙头 6 槽 |
| 粗糙度变化 | `RoughnessVar`：white 0.12 / white1 0.10 / 其余 0.08 |
| 未替换 | `MI_Glass_01a` 46 槽（DekoClass 体系，假反射 cubemap）、各种哈希材质、`anquanchukou_mat` |

### 5.2 灯光

| 项 | 状态 |
|---|---|
| 13 盏灯 | 物理照度（DirectionalLight 250 lux / SpotLight 1200 cd / PointLight 1600 cd / RectLight 2200 lm），**色温由用户手动微调** |
| Mobility | **全部 Movable** |
| 接触阴影 | `ContactShadowLength = 0.03` |
| 投影状态 | DirectionalLight **关**、RectLight ×5 **关**、SpotLight ×7 + PointLight **开** |
| 局部光阴影分辨率 | `ShadowResolutionScale = 0.5` |

### 5.3 渲染与后处理

| 项 | 状态 |
|---|---|
| VSM | **关闭**（`r.Shadow.Virtual.Enable=0`） |
| 传统 Shadow Map | `MaxResolution=2048` / `MaxCSMResolution=1024` / `MaxSoftKernelSize=0` |
| 静态光照 | `r.AllowStaticLighting=False` |
| 方向光阴影距离 | 4000（原 20000） |
| 后处理 | `PP_Opt`（unbound），**真实/自然档**：Bloom 0.30/阈值 1.0、暗角 0.15、颗粒 0.01、色散 0、锐化 0.20、对比 1.02、Local Exposure 关闭 |
| Lumen | GI + Reflections，`MaxRoughnessToTrace=0.4` |
| 其他 | `SSR.Quality=2`、`AOQuality=1`、`ContactShadows=1`、`Streaming.PoolSize=3000` |

### 5.4 工程配置

| 项 | 状态 |
|---|---|
| RemoteControl | **已启用**（`RemoteControl` + `RemoteControlWebInterface`），可 HTTP 远程执行 Python |
| 编辑器启动 | 需带 `-RCWebControlEnable -RCWebInterfaceEnable`，端口 30010 |

---

## 6. 后续计划

### 6.1 性能（等 `stat unit` 数据决定）

| 优先级 | 项目 | 依据 |
|---|---|---|
| 高 | Lumen 反射（`r.Lumen.Reflections.Allow=0`） | 如果 GPU 仍是瓶颈，这是最大单项 |
| 中 | GPU 蒙皮（SKM_Quinn 4.6 万顶点/帧） | profViz 有 `GPUSkinCache_UpdateSkinningBatches` |
| 中 | Niagara GPU 粒子 | profViz 有 `NiagaraGpuComputeDispatch` |
| 低 | 玻璃 `TLM_VOLUMETRIC` 替换 `TLM_SURFACE` | `TranslucencyLightingVolume` 64³ Cascades:2 |

### 6.2 画质（用户决定是否继续）

| 项目 | 说明 |
|---|---|
| 反射捕获球 | 场景当前 **0 个** `ReflectionCapture`，加 3–5 个可让金属/玻璃有正确环境反射 |
| 表面贴图 | 项目内有现成 PBR 三通道（`TX_School_Floor_01a` / `TX_Wall_Plaster_01a` 等 ALB/NRM/RMA） |
| Decal 贴花 | 地面污渍、台面划痕 |
| 局部体积雾 | 窗户附近做丁达尔光柱 |

### 6.3 已知未解决问题

| 问题 | 状态 |
|---|---|
| 第一人称玻璃不反射角色 | 材质 `MI_Glass_01a` 用的是 cubemap 假反射，且屏幕空间反射无法反射屏外像素。**已确认放弃**（PlanarReflection 收益太低） |
| 电热板外壳绿色 | 该颜色是原材质真实值（`green` = (0.018, 0.090, 0.038)），非误伤。若要改必须按 actor 单独指定 |
| 粗糙度空间变化 | 用户反馈"像湿掉"后已从 0.60 降到 0.12 |
