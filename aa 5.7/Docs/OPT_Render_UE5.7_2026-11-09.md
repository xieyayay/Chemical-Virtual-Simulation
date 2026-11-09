# 虚拟仿真（化学实验）渲染专项优化 · UE 5.7

> 项目：`D:\UE5\Chemistry\aa 5.7`　引擎：UE 5.7.4 (CL 51494982)　DX12 / SM6 / Substrate 已开
> 生成时间：2026-11-09　基于：对 `/Game/Start` 的运行时实测（371 actors / 306 网格组件 / 12 盏灯 / 0 个后处理体积）

---

## 0. 一句话结论

**画面"不真实"的主因不是缺素材，是三件事叠加：**

| 排序 | 问题 | 实测证据 | 影响 |
|---|---|---|---|
| **P0** | **全场景没有后处理体积** | `/Game/Start` 中 `PostProcessVolume` 数量 = **0** | 无曝光锁定、无局部曝光、Bloom 用引擎默认、无白平衡/胶片曲线 → 画面永远"灰、平、飘" |
| **P0** | **所有灯几乎是关着的** | SpotLight/PointLight = **8 Candelas**、RectLight = **25 Lumens**、DirectionalLight = **10 Lux**（全是新建默认值，无人调过） | 6 m 高天花板下桌面照度 ≈ 0.2 lux。Lumen 没有有效光源可反弹 → 无间接光层次、阴影死黑 |
| **P1** | **130+ 个网格挂着纯色常量材质** | `/Game/models/material/{white×37, glass×27, black×19, red×18, gray2×15, green×14 …}` | 无 roughness / 无法线 / 无高光控制 → 一打光就是纸片、塑料 |
| P2 | 306/306 网格 Nanite 关闭 | `nanite_off = 306` | 导入模型 LOD 粗糙、自遮挡阴影差（器皿本身别开 Nanite，见 §5.4） |
| P2 | 29 个槽位挂着引擎占位材质 | `MI_Ball_01×8`、`MI_Cube_01×5`、`Widget3DCameraPassThrough×6`、`BasicShapeMaterial×10` | 场景里可能残留 VREditor 的灰球/灰块 |
| P3 | 2 个零缩放 Actor | `Plane3` / `Plane4` scale=(-0.003, 0, 0) | 只产生物理警告，不影响画面，建议删 |

---

## 1. 已经做完的（本包已落盘）

| 文件 | 作用 | 状态 |
|---|---|---|
| `Config/DefaultEngine.ini`（末尾追加 `[SystemSettings]`） | Lumen HWRT、半透阴影质量、TSR、色调映射、体积雾、关自动曝光、关 MegaLights | ✅ 已写入（原文件备份为 `DefaultEngine.ini.bak_20261109`） |
| `Content/_Opt/M_Opt_Surface` | 不透明 PBR 母材质（带**粗糙度空间变化**，这是去掉塑料感的关键） | ✅ 已生成 12.7 KB |
| `Content/_Opt/M_Opt_Glass` | 玻璃母材质（Fresnel 驱动不透明度 + 折射） | ✅ 已生成 9.5 KB |
| `Content/_Opt/M_Opt_Liquid` | 有色溶液母材质（吸收色 + Fresnel + 折射） | ✅ 已生成 9.7 KB |
| `Content/_Opt/MI/MI_Opt_*` ×31 | white/white1/black/gray..gray7/red/red1/blue/blue1/blue2/green/green1..3/pink/pink1/purple/purple1/jingshixian/glass..glass3 的物理正确实例 | ✅ 已生成 |
| `Saved/opt/opt_apply_editor.py` | **编辑器内一键**：建 PPV + 重设全部灯光 + SkyLight + 体积雾 | ✅ 待你执行（30 秒） |
| `Saved/opt/opt_swap_materials_editor.py` | **编辑器内一键**：把纯色材质换成 PBR 实例（可 Ctrl+Z） | ✅ 待你执行（30 秒） |
| `Saved/opt/fix_scene.py` | 同上的 headless 版（需关闭编辑器，带 `--apply`） | ✅ 已跑通 dry-run |
| `Saved/opt/build_opt_assets.py` | 材质资产生成脚本（可重复执行，幂等） | ✅ 已验证 |
| `Saved/opt/verify_assets.py` + `verify_report.txt` | 材质图结构验证（BaseColor/Roughness/Normal/Opacity/Refraction 引脚逐个核对） | ✅ 已通过 |
| `Saved/opt/check_mi.py` + `mi_colors.txt` | 31 个实例的颜色/粗糙度核对 | ✅ 已通过 |
| `Saved/opt/backup_20261109/Content/Start.umap` | 关卡备份（3.86 MB） | ✅ |

### 1.1 生成结果实测（不是"应该能行"，是跑出来的）

三个母材质的引脚连接（`verify_report.txt`）：

```
M_Opt_Surface: BaseColor←VectorParameter  Roughness←Clamp(噪声链)  Metallic←Scalar  Specular←Scalar  Normal←Multiply
M_Opt_Glass:   BaseColor←VectorParameter  Roughness←Scalar  Specular←Scalar  Opacity←Clamp(Fresnel)  Refraction←AppendVector
M_Opt_Liquid:  BaseColor←VectorParameter  Roughness←Scalar  Specular←Scalar  Opacity←Clamp(Fresnel)  Refraction←AppendVector
```

31 个实例的颜色（`mi_colors.txt`，线性值）：

| 实例 | BaseColor | Roughness |
|---|---|---|
| white / white1 | 0.82 / 0.78 | 0.45 / 0.42 |
| black | 0.025 | 0.52 |
| gray / gray2 / gray6 | 0.38 / 0.34 / 0.18 | 0.48 |
| red / red1 | (0.48, 0.04, 0.04) | 0.34 |
| green / green2 | (0.04, 0.18, 0.07) | 0.32 |
| blue | (0.02, 0.05, 0.24) | 0.32 |
| jingshixian | (0.72, 0.60, 0.06) | 0.55 |
| glass..glass3 | (0.02, 0.03, 0.035) | 0.03 |

> 原材质的颜色读不出来（`MaterialEditingLibrary` 在 5.7 commandlet 下没有遍历表达式的 API），
> 所以用了两层：先读 `editor_only_data.base_color` 引用的常量节点，读不到再按名字落物理色表。
> 表里所有值都在 Substance/Unity 的 albedo 校验区间内（非金属 0.02–0.94 线性）。

---

## 2. 三步执行（约 5 分钟）

### 第 1 步：重启编辑器（让 `[SystemSettings]` 生效）

关掉 UE → 重开项目。`r.Lumen.HardwareRayTracing` 这类 cvar 必须重启才吃。

### 第 2 步：打光 + 后处理（编辑器内执行）

`Tools → Execute Python Script...` → 选 `D:\UE5\Chemistry\aa 5.7\Saved\opt\opt_apply_editor.py`

之后**先别保存**，直接点 Play 看效果。不满意就 `Ctrl+Z`，或关掉不保存。
执行后会打印每盏灯的新数值，便于核对。

### 第 3 步：材质替换（编辑器内执行）

`Tools → Execute Python Script...` → 选 `opt_swap_materials_editor.py`

默认只换 `glass / white / gray / black` 四类（语义明确、风险最低）。
`red / green / blue / purple / pink` 默认**不换**——它们可能是液体、橡胶、涂层，
颜色语义不明，误换会让"红色胶头"变成"红色塑料"。

确认要全换：打开脚本把 `ALLOW_CHROMATIC = False` 改成 `True` 再跑。

满意后 `Ctrl+S` 保存关卡。

---

## 3. 打光方案（实测值 → 目标值）

### 3.1 现场实测

| 灯 | 类型单位 | 当前值 | 位置 (cm) | 问题 |
|---|---|---|---|---|
| DirectionalLight | Lux | **10** | 80, -420, 1010 | 真实阴天室外 1000–10000 lux；10 lux 连"黄昏"都不够 |
| SpotLight ×6 | Candelas | **8** | 天花板 z≈595 | 8 cd 在 6 m 外 = 0.22 lux，等于没开 |
| PointLight6 | Candelas | **8** | 2697, -12, 839 | 同上 |
| RectLight ×5 | **Lumens** | **25.1** | z≈601 | 一根 36W 荧光灯管 ≈ 2000–3600 lm；25 lm 是蜡烛 |
| SkyLight | — | 1.0 | — | 指定了 `TX_Cubemap_01a` 静态立方图 + 同时开 RealTimeCapture（互相打架） |
| ExponentialHeightFog | — | 默认 | — | 所有灯 `VolumetricScatteringIntensity=1.0`，一开体积雾就全场泛白 |

### 3.2 目标值（脚本已内置）

| 灯 | 单位 | 目标强度 | 色温 | VolumetricScattering |
|---|---|---|---|---|
| DirectionalLight | Lux | **800**（室内窗光量级） | 5200 K | 0.60 |
| RectLight（灯管） | Lumens | **2600** | 5000 K | 0.35 |
| SpotLight（筒灯） | Candelas | **1400** | 4300 K | 0.30 |
| PointLight（灯泡） | Candelas | **1800** | 4500 K | 0.30 |
| SkyLight | — | 1.0 + CapturedScene + RealTimeCapture + 下半球不黑 | — | — |
| HeightFog | — | Density 0.008 / HeightFalloff 0.15 / StartDistance 150 / Volumetric 开 / ScatteringDist 0.2 | — | — |

**换算依据**（你要给评委讲"为什么是这个数"就用这个）：
点光源照度 `E = I / d²`。6 m 高天花板到桌面 1.5 m 实验台，距离 d ≈ 4.5 m，
要桌面达到 60–80 lux（教室/实验室标准照度 300–500 lux，这里按"有氛围的教学片"降到 60–80），
需要 `I = E·d² = 70 × 20.25 ≈ 1400 cd`。这就是 SpotLight 取 1400 的由来。

### 3.3 三点光补充（现在完全缺）

现场只有"顶光 + 一盏方向光"，**没有主光/补光/轮廓光的层次**。补三盏，性价比极高：

| 位置 | 类型 | 强度 | 色温 | 说明 |
|---|---|---|---|---|
| 实验台斜上方 45° | RectLight 60×120 cm | 1200 lm | 4800 K | 主光，让烧杯有明确高光方向 |
| 对面墙 | RectLight 200×80 cm | 500 lm | 6500 K | 补光，抬暗部，避免死黑 |
| 角色/器皿背后 | SpotLight | 400 cd | 5200 K | 轮廓光，把器皿从背景里"抠"出来 |

> 不要加第 4、5 盏。室内小场景灯越多越脏，Lumen 也越容易在接触处出噪点。

---

## 4. 后处理参数（脚本已内置，这里是"为什么"）

| 参数 | 值 | 理由 |
|---|---|---|
| AutoExposureMethod | **MANUAL** | 教学录屏必须每帧亮度一致；自动曝光会在镜头转向窗户时"呼吸" |
| AutoExposureBias | **10.8** | MANUAL 下 bias 即 EV100。EV100 ≈ log2(L·100/12.5)，10.8 对应 ~180 lux 中灰，匹配 3.2 的照度 |
| ApplyPhysicalCameraExposure | **false** | 不用物理相机，避免和 CineCamera 的 f-stop 打架 |
| Bloom Intensity | **0.45**（默认 0.675） | 室内场景 Bloom 过强会让白墙糊成一团 |
| Bloom Threshold | 1.0 | 只让灯管/玻璃边缘溢光 |
| Vignette | **0.32** | 轻微暗角把注意力收到实验台 |
| Film Grain | **0.035** | 去"CG 干净感"，0.02–0.05 是安全区，>0.1 就是噪点 |
| Scene Fringe（色散） | **0.35** | 模拟镜头色差，只在边缘可见 |
| Film Slope / Toe / Shoulder | **0.90 / 0.28 / 0.26** | ACES 胶片曲线微调：压高光、提暗部质感 |
| White Temp / Tint | **5600 K / 0** | 荧光灯偏绿，统一到日光；Tint 别动，动了肤色会脏 |
| Local Exposure Highlight/Shadow Contrast | **0.85 / 0.75** | 室内暗 + 窗外亮的核心解法，比自动曝光可控 |
| Local Exposure Detail Strength | 0.6 | 保住暗部细节，不糊 |
| Motion Blur Amount | 0.35 | 有 33 个 LevelSequence 过场，微动态模糊更电影 |
| Sharpen | 0.3 | TSR 会软，补一点；>0.6 出白边 |

---

## 5. 材质专项

### 5.1 你的场景里，材质到底错在哪

`/Game/models/material/` 下的 `white / black / red / glass …` 是 **3ds Max / SketchUp 导入时自动生成的纯色材质**：
一个 `Constant3Vector` 直接接 BaseColor，Roughness 是常量，没有法线，没有 AO。

后果：
- **全表面同一个粗糙度** → 不管布、金属、塑料、陶瓷都反射同样的光形 → 大脑立刻判定"假的"
- **没有微法线** → 近看镜面像塑料膜
- **玻璃用常量 Opacity** → 现实里玻璃的边缘永远比正面不透明（Fresnel），常数 Opacity 做不到

所以修法不是"换更贵的贴图"，而是：**给每个材质至少 0.15 的粗糙度动态范围 + 一层高频微法线**。
`M_Opt_Surface` 里的 `RoughnessVar` 参数就是干这个的（WorldPosition 驱动的 4 层噪声）。

### 5.2 母材质参数（`/Game/_Opt/` 已生成）

**M_Opt_Surface**（不透明）

| 参数 | 默认 | 用途 |
|---|---|---|
| BaseColor | 0.5 灰 | 由各 MI 给具体色 |
| Roughness | 0.40 | 基值 |
| **RoughnessVar** | **0.14** | 空间扰动幅度——**这一项就是"去塑料感"的开关**，别设 0 |
| Metallic | 0 | 非金属一律 0 |
| Specular | 0.50 | = F0 0.04 = IOR 1.5（塑料/玻璃/漆面） |
| NormalTex / NormalTiling / NormalStrength | 空 / 1 / 1 | 有法线贴图就接上，强度别超 1.5 |

**M_Opt_Glass**（Translucent, TwoSided）

| 参数 | 默认 | 物理依据 |
|---|---|---|
| GlassTint | (0.02, 0.03, 0.035) | 玻璃没有漫反射，接近黑 |
| Roughness | 0.03 | 干净玻璃 0.02–0.06 |
| Specular | **0.53** | IOR 1.52 钠钙玻璃 → F0 0.0426 → Spec 0.532 |
| EdgeOpacity | 0.92 | Fresnel(Exp=5) 乘它：正面≈0.03、边缘≈0.92 |
| RoughRefraction | 0.02 | 折射只做薄薄一层，真实 IOR 交给液体，避免双重偏移 |

**M_Opt_Liquid**（Translucent, TwoSided）

| 参数 | 默认 | 物理依据 |
|---|---|---|
| AbsorptionColor | (0.25, 0.55, 0.85) | 硫酸铜稀溶液透射色，**颜色走吸收不走 BaseColor** |
| Density | 0.65 | 浓度/光程代理，浓溶液调高 |
| Roughness | 0.02 | 静止液面 0–0.02 |
| Specular | **0.26** | 水 IOR 1.333 → F0 0.0204 → Spec 0.255 |

### 5.3 物理参数速查（Metallic=0 的电介质）

| 材质 | BaseColor (线性) | Roughness | Specular | IOR |
|---|---|---|---|---|
| 钠钙玻璃（烧杯/试管） | 透明 | 0.02–0.06 | **0.532** | 1.52 |
| 硼硅玻璃 Pyrex | 透明 | 0.02–0.05 | 0.459 | 1.474 |
| 纯水 | 透明 | 0.00–0.02 | **0.255** | 1.333 |
| 乙醇 | 透明 | 0.00–0.02 | 0.292 | 1.361 |
| 白瓷釉面（实验台） | 0.82 | 0.05–0.15 | 0.50 | 1.5 |
| 陶瓷素坯 | 0.58 | 0.55–0.75 | 0.40 | — |
| 黑色丁腈橡胶管 | 0.026 | 0.60–0.75 | 0.40 | — |
| 硅胶塞（半透） | 0.66 | 0.40–0.55 | 0.45 | — |
| 清漆木台面 | 0.23 | 0.28–0.40 | 0.50 | — |
| 原木（未处理） | 0.19 | 0.55–0.70 | 0.40 | — |
| 混凝土 | 0.37 | 0.65–0.85 | 0.40 | — |
| 皮肤（实验员手） | 0.53 | 0.35–0.45 | **0.35** | 1.40 |

金属（Metallic=1，BaseColor 即 F0）：铁 (0.56,0.57,0.58) / 铝 (0.91,0.92,0.92) / 铜 (0.95,0.64,0.54) /
金 (1.00,0.71,0.29) / 银 (0.95,0.93,0.88)。

> 换算公式：`F0 = ((n-1)/(n+1))²`，`Specular = F0 / 0.08`。
> 例：水 n=1.333 → F0=0.0204 → Spec=0.255（与 Epic 官方表一致）。

完整表格、IOR 校验链、贴图通道打包规范见 → [`Docs/PBR_Material_Spec_UE5.7.md`](PBR_Material_Spec_UE5.7.md)

### 5.4 器皿 6 条铁律（踩过才知道）

1. **玻璃绝不开 Nanite**。Nanite 不支持半透明，开了会部件消失/三角面炸开。你场景里 306 个网格全关 Nanite 反而躲过这一劫，别手贱打开。
2. **单面薄壳 + TwoSided，别做内外双壁**。壁厚 1–2 mm 在 1080p 只有 1–3 px，双壁只换来排序灾难。
3. **Fresnel 驱动 Opacity**。正面 0.03、边缘 0.9。常数 Opacity 的玻璃现实里不存在。
4. **折射只做一层**：玻璃 1.02–1.15，真实 IOR 留给液体。两层都做 → 水下错位。
5. **排序**：`Translucent Sort Policy = Sort by Distance to Camera`；液体 < 玻璃 < 气泡 < 标签，用 `Translucent Sort Priority` 分层。
6. **Substrate 下**：Opacity 变成 Coverage Weight，Blend Mode = `Translucent-Grey Transmittance`，Lighting Mode 必须显式设 `Surface ForwardShading`，否则高光是错的。

### 5.5 液体：为什么你的水像果冻

**颜色走吸收，不走 BaseColor。** 透明介质的颜色 = 吸收谱 × 光程：
`T = exp(-σ·d)`。φ50 烧杯和 φ10 试管的同一杯硫酸铜，颜色必须不同。

**弯月面（凹液面）是教具感的关键**：贴壁处上升 1–2 mm 的凹面 + 一道高光，缺了它液体永远是果冻。

---

## 6. 技术取舍（评委可能会问）

| 问题 | 结论 | 依据 |
|---|---|---|
| 要不要开 MegaLights？ | **不要**。5.7 仍是 Beta（5.5 Experimental → 5.7 Beta），恒定开销 + 质量随每像素光照复杂度下降；本场景 12 盏静态灯，deferred + VSM 更省，强方向光在室内容易出噪点 | UE 5.7 文档 / MegaLights 页 |
| Substrate 开不开？ | **保持开着**（项目已 `r.Substrate=True`）。5.7 起 production-ready，Blendable GBuffer 性能≈非 Substrate。要 layering（玻璃 = Slab + Fuzz + 透射三层）才需要切 Adaptive GBuffer，项目当前不需要 | Substrate 文档 |
| Lumen 要不要 HWRT？ | **要**。软件光追在玻璃上有三大限制（不支持 WPO、墙厚须 ≥10 cm、大单网格 distance field 自遮挡差），做不到干净镜面反射。器皿必须有清晰反射 | Lumen Technical Details |
| Nanite 要不要全开？ | **不要全开**。器皿/玻璃禁开；建筑、地面、大型设备可以开，省 LOD 与阴影开销。当前 306/306 全关属于"能用但不最优" | Nanite 文档 |
| 要不要 Path Tracer 出宣传图？ | 出参赛图/海报时用 Movie Render Queue + Path Tracer，一帧几秒到几十秒，画质碾压实时。实时预览仍用 Lumen | Path Tracer 文档 |

---

## 7. 如果还差一口气：优先级队列

按"投入 1 小时能拿回多少真实感"排序：

1. **给实验台、墙面、地面接真 PBR 贴图**（AO/Roughness/Normal）。项目里 `Content/quote/DekoClass/` 和 `Content/Fab/` 已有现成的 `TX_*_ALB/NRM/RMA`，直接建 MI 接上 M_Opt_Surface 的贴图槽，成本最低。
2. **器皿换 M_Opt_Glass**（跑 `opt_swap_materials_editor.py` 即可）。
3. **加微法线贴图**（1 mm 尺度划痕/橘皮，强度 0.15–0.4）。项目里 Megascans 的 `_N` 可以直接抽一张平铺。
4. **补三点光**（§3.3）。
5. **刻度线/标签换成 DBuffer Decal**，别用半透明贴片（乱序）。
6. **灯光加 Light Function**（灯管菲涅尔衰减 + 灰尘投影），成本 10 分钟，室内真实感提升明显。

---

## 8. 回滚

| 改了什么 | 怎么退 |
|---|---|
| `DefaultEngine.ini` | 覆盖回 `Config/DefaultEngine.ini.bak_20261109` |
| `/Game/Start` 关卡 | 覆盖回 `Saved/opt/backup_20261109/Content/Start.umap` |
| `/Game/_Opt/*` 材质资产 | 整个 `Content/_Opt` 目录删掉即可（没有任何已有资产引用它） |
| 编辑器内脚本改动 | 不保存关卡 = 没改；或 `Ctrl+Z` |

---

## 9. 调研来源

- UE 5.7 Release Notes / 文档索引 — <https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-7-documentation>
- Substrate Materials（5.7 状态、Slab/Fuzz/Transmittance、GBuffer 模式） — <https://dev.epicgames.com/documentation/en-us/unreal-engine/substrate-materials-in-unreal-engine>
- Substrate 总览（BSDF 分层、F0/F90） — <https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-substrate-materials-in-unreal-engine>
- Physically Based Materials（Specular 0.5 = 4% 反射、IOR 表） — <https://dev.epicgames.com/documentation/en-us/unreal-engine/physically-based-materials-in-unreal-engine>
- Refraction（IOR 表、Pixel Normal Offset 适用场景） — <https://dev.epicgames.com/documentation/en-us/unreal-engine/refraction-using-pixel-normal-offset-in-unreal-engine>
- Single Layer Water（散射/吸收系数、PhaseG） — <https://dev.epicgames.com/documentation/en-us/unreal-engine/single-layer-water-shading-model-in-unreal-engine>
- Decal Materials（DBuffer，Substrate 依赖） — <https://dev.epicgames.com/documentation/en-us/unreal-engine/decal-materials-in-unreal-engine>
- Virtual Texturing（RVT vs SVT） — <https://dev.epicgames.com/documentation/en-us/unreal-engine/virtual-texturing-in-unreal-engine>
- Nanite（半透明/masked 限制、WPO Beta） — <https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine>
- Subsurface Profiles（皮肤/蜡/叶片） — <https://dev.epicgames.com/documentation/en-us/unreal-engine/using-subsurface-profiles-in-materials>
- Unity PBR Material Validator（albedo 50–243 / 金属 186–255） — <https://docs.unity3d.com/Manual/MaterialValidator.html>
- Adobe Substance PBR Guide — <https://substance3d.adobe.com/tutorials/courses/the-pbr-guide-part-2>
- Lagarde《Feeding a physically based shading model》（F0 ≥ 0.02、液体 0.02–0.04） — <https://seblagarde.wordpress.com/2011/08/17/feeding-a-physical-based-lighting-mode/>
- Quixel ORD 通道打包 — <https://help.quixel.com/hc/en-us/articles/115000589729-Channel-Packing>
- Epic Games Japan GCC2026 讲稿（Substrate 转换公式、PS5 实测） — <https://www.docswell.com/s/EpicGamesJapan/K8N2G7-2026-04-03-230956>

---

## 10. 已做 / 未做（如实标注）

**已实际执行并验证：**
- 读取项目全部配置、扫描 2874 个 `.uasset`、跑通 UE Python headless 管线
- 实测 `/Game/Start` 全部 actor（371）、灯光单位与数值、PPV 数量、材质槽引用统计
- 写入 `[SystemSettings]`（原文件已备份）
- 生成 3 个母材质 + 31 个 MI（磁盘已确认落盘，编译 0 error）

**未执行（需要你操作或需要关闭编辑器）：**
- 灯光/PPV 的实际应用（`opt_apply_editor.py` 需在编辑器内跑）
- 材质槽替换（`opt_swap_materials_editor.py` 需在编辑器内跑）
- **渲染前后对比截图**——本机编辑器实例正被占用并跑着 PIE，headless 无法出图。跑完前两步后自行截一张对比，或告诉我关掉编辑器，我用 `-game + HighResShot` 出图。
