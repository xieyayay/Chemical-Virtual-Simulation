# UE 5.7 化学虚拟仿真项目 · PBR 写实材质参数规范

> 版本：2026-11 · 依据 2024–2026 公开文档与实测帖撰写
> 数值标注：★ = 官方/权威来源可查；☆ = 权威区间内的工程推荐值（非逐材质权威常数）

---

## 0. 读数口径（先统一单位，否则后面全部对不上）

三套口径同时在用，混用是"看起来假"的第一大来源：

| 口径 | 用途 | 换算 |
|---|---|---|
| sRGB 8bit (0–255) | 贴图、Substance 校验器、albedo 上下限 | 与线性值互为 gamma 2.2 近似 |
| 线性 0–1 | UE BaseColor 引脚内部、F0 | — |
| F0 / Specular | 电介质反射率 | `F0 = ((n-1)/(n+1))²`；`UE Specular = F0 / 0.08` |

**核心恒等式（Epic 官方 shader 源码，GCC2026 讲稿给出）**

```
DielectricSpecularToF0(Specular) = 0.08 * Specular      // 0.08 = 电介质垂直入射最大反射率
ComputeF0           = lerp(0.08*Specular, BaseColor, Metallic)
ComputeDiffuseAlbedo = BaseColor - BaseColor*Metallic    // = BaseColor*(1-Metallic)
```

所以 **Specular = 0.5 就是 F0 = 0.04（4%），即 n≈1.5 的塑料/玻璃**。这是 UE 电介质默认值，不是"中间值蒙一个"。

**权威区间（校验器可直接用）**

- 非金属 albedo：**50–243 sRGB**（Unity PBR Validator）；Substance PBR Guide 更严：暗部 **30 sRGB 宽容 / 50 sRGB 严格**，亮部 **≤240 sRGB**，且**逐通道**判定而非平均值 ★
- 金属 albedo：**186–255 sRGB** ★
- 非金属 specular：**40–75 sRGB**；金属 specular **155–255 sRGB**；>155 sRGB 判为金属 ★
- 电介质 F0 全局规则（Lagarde）：**任何电介质不低于 0.02**；宝石 0.05–0.17；**常见液体 0.02–0.04**；找不到参考值时用 0.04 ★
- roughness 有效工作区：**0.05–0.95**（低于 0.05 只在绝对镜面用，高于 0.95 无意义）☆

**IOR → F0 → UE Specular 换算表（本规范全部数值的推导依据）**

| 介质 | n (589nm) | F0 线性 | UE Specular | 校验 |
|---|---|---|---|---|
| 空气 | 1.00 | 0.0000 | 0.00 | — |
| 冰 | 1.31 | 0.0180 | 0.225 | Epic 官方 0.224 ✓ |
| 水 | 1.333 | 0.0204 | 0.255 | Epic 官方 0.255 ✓ |
| 牛奶 | 1.35 | 0.0222 | 0.277 | Epic 官方 0.277 ✓ |
| 乙醇 | 1.361 | 0.0234 | 0.292 | 无官方 Specular，由 IOR 换算 |
| 稀硫酸铜溶液 | ~1.34 | 0.0211 | 0.264 | 浓溶液随浓度上移 |
| 皮肤 | 1.40 | 0.0278 | 0.347 | Epic 官方 0.35 ✓ |
| 硼硅玻璃 (Pyrex) | 1.474 | 0.0367 | 0.459 | — |
| 钠钙玻璃 | 1.52 | 0.0426 | 0.532 | Epic 官方 Glass 0.5 ✓ |
| 石英玻璃 | 1.4585 | 0.0348 | 0.435 | Epic Quartz 0.570 对应 n≈1.54，属另一种口径 |
| 重铅玻璃 | ~1.79 | 0.0800 | 1.00 | Epic Glass(High)/Ruby 0.08 ✓ |
| 金刚石 | 2.42 | 0.1724 | 2.155 | Epic 0.17 ✓（Specular>1 合法） |

---

## 1. 物理正确参数表

### 1.1 电介质 / 液体（Metallic = 0）

| 材质 | BaseColor sRGB（线性） | Metallic | Roughness | Specular / IOR | 备注 |
|---|---|---|---|---|---|
| 钠钙玻璃（烧杯/试管/量筒） | 不适用（透明，BaseColor 置黑或 0.02 线性） | 0 | 0.02–0.06 ★区间/☆取值 | IOR **1.52** / Specular 0.532 | 折射靠根节点 Refraction，不靠 BaseColor |
| 硼硅玻璃（实验器皿常用） | 同上 | 0 | 0.02–0.05 ☆ | IOR **1.474** / Specular 0.459 | 热膨胀低，光学更"干净"，n 比钠钙略低 |
| 磨砂玻璃（试剂瓶磨口） | 同上 | 0 | 0.35–0.50 ☆ | IOR 1.50 | 用 Haziness 或 roughness 抖动，别用噪波法线 |
| 纯水 | 不适用 | 0 | 0.00–0.02 ☆ | IOR **1.333** / Specular 0.255 | 大面积水面走 Single Layer Water |
| 乙醇 | 不适用 | 0 | 0.00–0.02 ☆ | IOR **1.361** / Specular 0.292 | 表面张力低，弯月面更贴壁 |
| 硫酸铜溶液（稀，~0.5M） | 透射色 ≈ (0.55,0.78,0.92) sRGB ☆ | 0 | 0.00–0.02 ☆ | IOR ≈ **1.34**（无权威逐浓度表）/ Specular 0.264 | 蓝色来自吸收而非 albedo，见 §2.3 |
| 硫酸铜溶液（饱和） | 透射色 ≈ (0.25,0.55,0.85) sRGB ☆ | 0 | 0.00–0.02 ☆ | IOR ≈ 1.38–1.40（无公开权威值） | 浓度↑→吸收↑→更暗更蓝 |
| 白瓷（陶瓷台面釉面） | 235 / (0.82) ☆ | 0 | 0.05–0.15 ☆ | Specular 0.5（n≈1.5 釉） | 加 clear coat 更像釉 |
| 陶瓷（未上釉素坯） | 200 / (0.58) ☆ | 0 | 0.55–0.75 ☆ | Specular 0.4 | 高粗糙 + 微法线 |
| 黑色丁腈橡胶管 | 45 / (0.026) ☆ | 0 | 0.60–0.75 ☆ | Specular 0.4 | 低于 30 sRGB 下限属"深色橡胶例外"，靠高光读形 |
| 硅胶塞（半透） | 210 / (0.66) ☆ | 0 | 0.40–0.55 ☆ | Specular 0.45 | 用 SSS Wrap，MFP 极小 |
| PP/PE 塑料试剂瓶 | 225 / (0.76) ☆ | 0 | 0.25–0.40 ☆ | Specular 0.5 | 半透感用 Two-Sided Wrap 伪一下 |
| 亚克力（有机玻璃挡板） | 不适用 | 0 | 0.03–0.08 ☆ | IOR **1.49** | 与玻璃差异极小，靠厚度/边缘读出来 |
| 浅色橡木（清漆台面） | 130 / (0.23) ☆ | 0 | 0.28–0.40 ☆ | Specular 0.5 | 清漆层用 Vertical Layer/Clear Coat |
| 原木（未处理） | 120 / (0.19) ☆ | 0 | 0.55–0.70 ☆ | Specular 0.4 | 纹理方向性走 anisotropy 或法线 |
| 混凝土（实验台基座） | 165 / (0.37) ☆ | 0 | 0.65–0.85 ☆ | Specular 0.4 | AO 必须来自几何+贴图，别烘进 albedo |
| 环氧树脂台面（黑） | 40 / (0.021) ☆ | 0 | 0.15–0.25 ☆ | Specular 0.5 | 深色 + 中低粗糙 = 最容易"油腻"的组合 |
| 皮肤（实验员手部） | 190 / (0.53) ☆ | 0 | 0.35–0.45 ☆ | Specular **0.35** ★ | 必须 Subsurface Profile，见 §5 |
| 牛奶/乳浊液 | 不适用 | 0 | 0.10–0.20 ☆ | Specular 0.277 ★ | 高 scattering，走 SSS Diffusion |
| 叶片 | — | 0 | 0.45–0.60 ☆ | Specular 0.3 | Two-Sided Foliage |

### 1.2 金属（Metallic = 1，BaseColor 即 F0，无漫反射）

| 材质 | BaseColor 线性 (R,G,B) | BaseColor sRGB | Metallic | Roughness | 备注 |
|---|---|---|---|---|---|
| 铁/碳钢 | (0.560, 0.570, 0.580) ★ | (0.77,0.78,0.78) | 1 | 0.30–0.45 ☆ | Epic 官方表，最常用的"铁支架"基色 |
| 不锈钢（304，抛光） | (0.560, 0.570, 0.580) ★(以铁近似) | 同上 | 1 | 0.08–0.15 ☆ | 严格来说 304 的 F0≈0.58–0.62，官方表未单列 → 用铁值并注明 |
| 不锈钢（拉丝/喷砂） | 同上 | 同上 | 1 | 0.25–0.40 ☆ | roughness 沿 UV 方向做各向异性更真 |
| 铝 | (0.910, 0.920, 0.920) ★ | (0.96,0.96,0.97) | 1 | 0.10–0.20 ☆ | 铝易氧化，实际做 0.3–0.5 更常见 |
| 铜 | (0.950, 0.640, 0.540) ★ | (0.98,0.82,0.76) | 1 | 0.10–0.25 ☆ | 铜电极/导线 |
| 金 | (1.000, 0.710, 0.290) ★ | (1.00,0.86,0.57) | 1 | 0.05–0.15 ☆ | 电极镀层 |
| 银 | (0.950, 0.930, 0.880) ★ | (0.98,0.97,0.95) | 1 | 0.03–0.10 ☆ | 银镜反应/镀银件 |
| 镀铬 | 无公开权威逐值（建议 0.55,0.556,0.554 线性，标注为估算） | ≈0.77 | 1 | 0.02–0.06 ☆ | 镜面级，必须有清晰环境反射 |
| 铸铁（带氧化皮） | 0.05–0.09 线性 ☆ | 65–85 | 1 | 0.50–0.65 ☆ | 铸铁 BlackBody 透黑，别用 0.5 灰 |

> 金属的 Specular 输入在 UE 中被忽略（金属 F0 直接取 BaseColor），所以金属行不列 Specular。

---

## 2. 化学实验器皿专项（8 套实现方案）

### 2.1 玻璃器皿（烧杯 / 试管 / 量筒 / 容量瓶）★核心难点

| 参数 | 值 |
|---|---|
| Shading Model | 默认 Lit（Legacy）或 Substrate Slab |
| Blend Mode | Translucent（薄壁单面壳） |
| BaseColor | 黑（0,0,0），玻璃没有漫反射 |
| Metallic | 0 |
| Roughness | 0.02–0.06（干净）/ 0.35–0.5（磨口、磨砂） |
| Specular | 0.53（= IOR 1.52） |
| Refraction | **1.0 = 无折射，1.52 = 物理正确**；实际教学场景取 **1.05–1.15** 更稳 |
| Refraction Mode | **Index of Refraction**（Epic 官方：适合罐子、玻璃杯等曲面小物体）；平面窗口类大平面用 **Pixel Normal Offset** |
| Opacity | 0.05–0.2（薄壁），配合 Fresnel 提边缘 |

**实现要点（可直接照做）**

1. **绝对不要给玻璃开 Nanite。** Nanite 不支持半透明材质；开了会出现模型破碎/部件消失、三角形炸开（社区大量复现，解法就是关 Nanite）。玻璃网格必须走普通 StaticMesh。
2. **几何优先单层壳**：真实烧杯壁厚 1–2mm，在 1080p 下壁厚只有 1–3 像素。做**单面薄壳 + 双面渲染（Two Sided）**比做内外双壁更稳，排序问题少一个数量级；厚壁只在特写镜头（<30cm）才值得做。
3. **折射只做一层**：玻璃层给 1.05–1.15，内部液体层给 1.33 的真实 IOR 会双重偏移，容易"水下错位"。把真实 IOR 交给液体，玻璃层压到 1.02–1.05。
4. **Fresnel 是玻璃的灵魂**：`Fresnel(F0=0.04, Exponent=5)` 驱动 Opacity，正对视线 0.03、边缘 0.9，才能有"边缘发亮、中心通透"的真玻璃读感。常数 Opacity = 玻璃感全丢。
5. **排序**：材质 Details → **Translucent Sort Policy = Sort by Distance to Camera**，物体级用 **Translucent Sort Priority** 手工分层（液体 < 玻璃 < 气泡 < 标签贴纸）。器皿自重叠（杯壁背面 vs 正面）无法靠 actor 排序解决 → 打开 **Sort Triangles**（per-polygon 排序，代价是每帧 CPU 排序），或改用 Masked + Dither（TSR 下抖动几乎不可见，且能进 Nanite 之外的正常管线）。
6. **Substrate 下**：Slab BSDF + **Coverage Weight**（替代 Opacity）驱动透明度；Blend Mode 选 **Translucent-Grey Transmittance**；Lighting Mode 必须显式设 **Surface ForwardShading**（支持局部光高光，最贵但玻璃必须有）；F0 填 0.04（线性），Diffuse Albedo 填 0。折射仍走根节点 Refraction 引脚。

### 2.2 水（器皿内 + 场景水体，两种做法分开）

**A. 器皿内的水（小体积、要看见刻度浸没）→ Translucent + Beer-Lambert 近似**

```
Transmittance = exp(-σ_abs * thickness)
σ_abs = -ln(T_desired) / thickness
```
- 纯净水：T = (0.98, 0.99, 1.00)，几乎无衰减，靠表面反射和弯月面读形
- 弯月面（弯液面）：这是"教具感"的关键。用一个薄环 mesh 或顶点位移做出凹面（玻璃壁处上升 1–2mm），配合高光；缺了弯月面，液体永远像果冻
- Fresnel 同玻璃；Roughness 0.0–0.02（静止）/ 0.05–0.12（晃动，用 panner 法线）

**B. 场景大水体（水槽、浴槽）→ Single Layer Water** ★

| 输入 | 含义 | 官方示例值 |
|---|---|---|
| Scattering Coefficients | 散射率，低=清澈（玻璃/水瓶），高=浑浊（橙汁/牛奶） | 0.5 / 1 / 2 / 4 / 8 / 16 / 32 递增序列 |
| Absorption Coefficients | 按波长吸收，单位 m⁻¹（= 1/吸收距离） | R 0.0033、G 0.0016、B 0.0011（红先消失→绿→蓝） |
| PhaseG | 正=前向散射（朝太阳），负=后向，0=各向同性 | -0.75 / 0.5 |
| Color Scale Behind Water | 乘水下表面亮度，做假焦散/明暗 | 1.0 起调 |
| 根节点 Opacity | BSDF 与 BRDF 的配比：1 全不透且发暗，0 则四项体积参数全生效 | 0–0.3 |

- Blend Mode 必须 **Opaque 或 Masked**（不是 Translucent），Shading Model = **SingleLayerWater**，图里必须加 **Single Layer Water Material** 输出节点
- 低端/移动端会回退成普通半透明（无体积积分、无 SSR）——教学平板端要提前验证
- 已知坑：水面块状阴影 → `r.Water.SingleLayer.DepthPrepass=1` 写进项目 DefaultEngine.ini（只读 cvar，会触发全量 shader 重编译）；UE-102259：SingleLayerWater + PixelDepthOffset 折射错误

### 2.3 有色溶液（硫酸铜 / 高锰酸钾 / 碘酒）

颜色**绝对不能**塞进 BaseColor。透明介质的颜色 = 吸收谱 × 光程。

1. 用 2.2A 的 Beer-Lambert 公式，把目标颜色当 T 反解 σ
2. 硫酸铜（蓝）：吸收红黄 → σ_R > σ_G > σ_B。稀溶液 T≈(0.55,0.78,0.92)，饱和 T≈(0.25,0.55,0.85)
3. **厚度必须真实**：液体厚度用顶点色或 depth 差驱动。同一材质在 φ50 烧杯和 φ10 试管里颜色必须不同，否则一眼假
4. 液面以上的玻璃壁不能带液体色 → 用 mask（液体 mesh 独立）而非整杯染色
5. 高锰酸钾（紫红）、碘酒（棕黄）同理，只改吸收谱
6. 浑浊/悬浊（氢氧化铜沉淀、牛奶）：改走 **SSS Diffusion 或 Simple Volume**，不要再走纯吸收

### 2.4 金属支架 / 铁架台 / 坩埚钳

- Metallic = 1，BaseColor 用铁 (0.56,0.57,0.58) 线性
- Roughness 分区：焊点/螺纹 0.5–0.65，杆身喷漆 0.35–0.5，接触面磨亮 0.15
- **必须加粗糙度微变化**：纯 0.3 常数的金属杆会像塑料；用 0.25–0.35 的噪波（大尺度，1–3cm 波长）
- 铁架台的黑色烤漆是**电介质**（Metallic=0，BaseColor 0.03–0.05），只有磨损露铁处 Metallic=1 —— 用 mask 混合，别整根 Metallic=1

### 2.5 橡胶管 / 硅胶塞

- 橡胶：Metallic 0，BaseColor 0.026 线性（≈45 sRGB），Roughness 0.60–0.75，Specular 0.4
- 橡胶的高光很弱但有：全靠 Roughness 0.6 附近的宽高光读出圆柱体积，去掉就变黑面条
- 硅胶塞是**半透**的：Two-Sided Wrap + 小 MFP（0.05–0.15cm），能透出手指轮廓影子，这是最强的真实感信号
- 表面加 micro-normal（0.3–0.5 强度，高频），橡胶的哑光颗粒感来自微法线而非粗糙度

### 2.6 陶瓷台面 / 瓷砖

- 釉面白瓷：BaseColor 0.82 线性（235 sRGB），Roughness 0.05–0.15，Specular 0.5
- **釉面要用 Clear Coat / Substrate Simple Clear Coat**（一层独立高光），否则高光和漫反射糊在一起
- 砖缝/磨损：Roughness 提到 0.5–0.7，BaseColor 降到 0.4–0.5；AO 从几何取，不烘进 albedo
- 台面反射是化学场景"干净度"的主要信息源，Roughness 别超过 0.2

### 2.7 木质台面 / 实验凳

- 清漆木：BaseColor 0.23 线性，Roughness 0.28–0.40，**清漆层用 Vertical Layer（Substrate）或 Clear Coat（Legacy）**，厚度 0.05–0.2mm
- 木纹方向性：法线贴图沿纹理拉长（anisotropy 用不上就靠贴图），木纹必须有**大尺度色差**（同一块板 0.18–0.28 波动），纯色木板必假
- 原木未处理：Roughness 0.55–0.70，Specular 0.4，加 Fuzz（绒毛感，Substrate Fuzz 或 legacy 无对应则靠微法线）

### 2.8 玻璃器皿上的"教学内容"层

- 刻度线/标签：**Decal**，Material Domain = Deferred Decal，Blend Mode = Translucent，Decal Blend Mode = **DBuffer Translucent Color Normal Roughness**（这样才能不透明地覆盖玻璃而不用管排序）
- 注意：**Substrate + DBuffer 材质表达式要求 DBuffer Decals 已启用**（UE5 默认开启，Adaptive GBuffer 强制开启）
- 刻度需要贴附曲面 → 用 Decal Actor 的 projection，或直接建模贴花 mesh

---

## 3. Substrate 与 Legacy 对应关系（5.7 迁移用）

> UE 5.7 起 Substrate 达 Production Ready；5.7+ 升级的旧工程默认仍走非 Substrate 路径，需 Project Settings > Rendering 勾 **Substrate materials** 并重启。转换不可逆。建议**新材质直接 Substrate，旧材质分批迁移**。

| Legacy | Substrate | 备注 |
|---|---|---|
| BaseColor + Metallic + Specular | **Substrate Metalness To Diffuse Albedo F0** 辅助节点 | 一行接完，沿用原值 |
| 单一 Lit（默认） | **Slab BSDF**（Simple 复杂度） | 保持 60fps 的默认选择 |
| Clear Coat | **Simple Clear Coat** | 官方优化版，别用老 Clear Coat 节点 |
| Subsurface | Slab Sub-Surface Type = **Wrap** | — |
| Two-Sided Foliage | **Two-Sided Wrap** | 叶片必用 |
| SubSurface Profile | **Diffusion** + 指定 SSS Profile | Diffusion 只在 deferred/pathtracing 与 SM6 平台可用；设了 Profile 后 MFP 被忽略 |
| Thin Translucent | **Translucent-Colored Transmittance**（最贵，需单独 buffer） | 教学项目慎用 |
| Translucent | **Translucent-Grey Transmittance**（≈旧 Translucent） | 不支持硬件彩色半透明的平台会回退 |
| Multiply 混合 | **Colored Transmittance Only** | 最轻 |
| （无） | **Fuzz**（布/绒毛/木纤维）| FuzzRoughness 控扩散 |
| （无） | **Haziness**（磨砂） | 可用 Haziness-to-Secondary-Roughness 只做磨砂 |
| （无） | **Second Roughness / Dual Specular** | 保持镜面"面积"同时混合两个粗糙度 |
| （无） | Glints | 一开即 Complex Special，GBuffer 输出量剧增，教学项目不用 |

**Blend Mode 必配 Lighting Mode**：绝大多数半透明用 **Surface Translucency Volume**；玻璃/液体需要局部光高光时用 **Surface ForwardShading**（最贵）。

**性能开关**

| CVar | 默认 | 说明 |
|---|---|---|
| `r.Substrate.BytesPerPixel` | 80 | 超预算自动简化 |
| `r.Substrate.MaxClosureCount` | — | 限制 closure 数 |
| `r.Substrate.ShadingQuality` | 0 | 0=近似照明（60fps 默认），1=精确 |
| `r.Substrate.ProjectGBufferFormat` | 0=Blendable, 1=Adaptive | Adaptive：cook +15%、强制 DBuffer、仅 XSX/PS5/Win SM6 等 |

复杂度分级（照明成本）：Simple（默认 lit）→ Single（F90/Fuzz/SSS/ClearCoat）→ Complex（Anisotropy/Specular profile/Eye/Hair）→ Complex Special（Glints）。**简化优先级：Fuzz > SSS > Haziness。**

---

## 4. 贴图与资产规范（导入 checklist）

| 贴图 | Compression Settings | sRGB | 其他 |
|---|---|---|---|
| BaseColor / Albedo | Default (BC1/BC3) 或 BC7 | **✓ on** | 只含 diffuse，无光照、无 AO |
| Normal | **Normalmap (BC5)** | **✗ off** | 需 **Flip Green Channel** 判定（OpenGL 法线=YES，DirectX 法线=NO）；**Normalize Normals = ON**（"Normalize colors in Normal Maps after mip generation for better and sharper quality; recommended"） |
| Roughness / Metallic / AO | Masks 或 BC7 | **✗ off**（线性数据） | 灰度贴图必须通道打包 |
| ORM 打包 | Default/Masks | ✗ off | 通用 **R=AO, G=Roughness, B=Metallic**；**Quixel Megascans surface 是 ORD：R=AO, G=Roughness, B=Displacement** —— 两者别混用 |
| Displacement | — | ✗ off | 喂 Nanite Tessellation（需 Enable Tessellation） |
| Emissive | Default | ✓ on（颜色） | 强度 >1 用 HDR |

**Mip 相关属性（官方 API 命名，可直接在贴图 Details 找）**

- `Mip Gen Settings`：`SimpleAverage`（2×2 kernel）/ `Sharpen0`–`Sharpen5`（更大 kernel，锐化小细节）。锐化能保住远处细节，但会引入 **摩尔纹与闪烁**——教学场景里有刻度的器皿慎用
- `LOD Bias`：整体偏置 mip（2k → 1k），不是"远处才降"，会永久降分辨率
- `Never Stream` / `Virtual Texture Streaming` / `LOD Group` / `Max Texture Size` / `Lossy Compression Amount`
- 大场景（整个实验室）用 **Streaming Virtual Texture (SVT)** 或 UDIM；动态混合用 **Runtime Virtual Texture (RVT)**

**Runtime Virtual Texture（RVT）分工** ★

- RVT：texel 由 **GPU 运行时生成**，适合程序化/多层混合材质（地形、墙面脏污、贴花合成）
- SVT：texel **从磁盘 cook 后按需加载**，适合超大、耗时生成的贴图（lightmap、UDIM）
- RVT 用法：Project Settings 开 Virtual Texture → 建 RVT 资产（Content = BaseColor/Normal/Roughness…）→ 放 **RuntimeVirtualTextureVolume** 并对齐 → Landscape/StaticMesh 的 Virtual Texture 段挂上 → 材质里用 **Runtime Virtual Texture Output** 写入，物体材质用 **Runtime Virtual Texture Sample** 读回并 Lerp
- 同一 RVT 可同时做"贴花投影"和"物体与地面融合"，教学场景里做**地面积液/腐蚀污渍**最省

**Material Parameter Collection（MPC）** ★

- 资产类型：`UMaterialParameterCollection`，存标量/矢量默认值，**任意数量材质共享**，改一次全场景生效
- 用作全局调色总线：`GlobalTint`（Vector）、`WetnessAmount`（Scalar）、`LabLightIntensity`、`SolutionConcentration`
- 材质里用 **CollectionParameter** 节点读；也可用 **Material Parameter Collection Track** 在 Sequencer 里 K 帧
- 注意：改 collection 的**参数列表/类型**会让引用它的材质重编译；只改默认值不重编译
- 纪律：**一个项目最多 2–3 个 MPC**（全局调色 + 环境状态 + 调试）。MPC 里塞每个物体自己的参数会把可调试性毁掉

**Decal 与顶点色混合**

- Decal 两条渲染路径：**DBuffer**（BasePass 前累积 basecolor/normal/roughness，UE5 默认开启，Substrate 必需）与 **GBuffer**（BasePass 后直接混合）
- 污渍/积垢/刻度 → DBuffer Decal；大面积改材质属性 → RVT
- 顶点色：一个材质内做多区域变化最便宜的手段（用 VertexColor 的 R/G/B 当 mask 做 Lerp/Tint），比多套贴图省 3–4 个 sampler

---

## 5. 次表面散射（SSS）

| 用途 | Shading Model / Substrate | 参数要点 |
|---|---|---|
| 皮肤（手部特写） | Legacy: Subsurface Profile；Substrate: **Diffusion** + Profile | Specular **0.35** ★（= IOR 1.4）；F0 0.028；Profile 里散射半径按 cm 设（红>绿>蓝） |
| 蜡 / 石蜡封口 | Subsurface / Wrap | MFP 比皮肤大，颜色偏黄白 |
| 牛奶 / 乳浊液 | Subsurface / **Diffusion** | 高 scattering、低吸收；表面仍要给 Fresnel 0.277 |
| 叶片 | **Two-Sided Foliage** / Two-Sided Wrap | 背面透光用叶子颜色；双面法线要独立 |
| 硅胶塞 | Wrap | 小 MFP，弱透 |

**Substrate MFP 单位是 cm**，RGB 三通道 = 各波长平均自由行程；用 **Transmittance To Mean Free Path** 节点由"颜色 + 厚度"反算，比手填 MFP 更直观。设了 Subsurface Profile 时材质上的 MFP 被忽略（Profile 优先）。

> 公开权威的逐材质 MFP 数值表**不存在**（Epic 只给工作流，不给数值）。上面皮肤/蜡的 MFP 属工程推荐值，需按项目尺度实测（用 1cm 立方体做标定块，肉眼对齐 0.5cm 处的透光衰减）。

---

## 6. 材质真实感 12 条硬规则（可执行）

1. **albedo 里不许有光照信息**。烘焙阴影、AO、高光、脏污对比全部滚出去。判据：把 albedo 贴图单看，应该"平得有点无聊"。
2. **albedo 逐通道夹在 50–240 sRGB**（金属 186–255）。低于 30 的只有木炭/黑橡胶级特例，且必须有来源。用 Substance 的 PBR Validate 滤镜 / Unity Validator 过一遍。
3. **F0 不许靠猜**：电介质一律从 IOR 反算 `F0=((n-1)/(n+1))²`，再 `Specular=F0/0.08`。任何电介质 F0 < 0.02 都是错的。
4. **Metallic 只准 0 或 1**。中间值只允许出现在"腐蚀/积尘/生锈/磨损过渡"mask 上，且必须是被贴图驱动的，不是手拉的 0.35。
5. **roughness 必须有空间变化**。全场 0.5 = 塑料感病根。每块材质的 roughness 至少要覆盖 0.15 的动态范围（大尺度 1–3cm 波长 + 小尺度 micro-roughness）。
6. **roughness 不进 0.95 以上**，也不轻易低于 0.05。低于 0.05 只在镜面（镀铬、静止水面）用，且必须配环境反射。
7. **法线强度默认 1.0，超过 1.5 就是在造假**。法线是"微表面斜率"，不是"凹凸贴图"。深沟槽用 displacement/几何，不用法线硬堆。
8. **必须有 micro-normal**。真实表面在 1mm 尺度上有颗粒/划痕/橘皮；缺这一层，材质在近距离永远"像塑料膜"。强度 0.15–0.4，高频，与主法线叠加前先做归一化。
9. **AO 从几何和贴图来，不烘进 albedo**。AO 该乘在 BaseColor 上做遮蔽暗示，但绝不能"画死在颜色里"（否则打光就死）。
10. **玻璃/液体不许开 Nanite**。Nanite 不支持半透明；强行开会炸模型。液体与玻璃分层建 mesh、分层排序。
11. **透明材质必须有 Fresnel 驱动的 Opacity**，常数 Opacity 的玻璃不存在于现实。玻璃 F0=0.04、边缘趋 1、正面趋 0.03。
12. **贴图链路一次定死**：Normal=BC5 + sRGB off + Flip Green 判定 + Normalize Normals ON；ORM=R/G/B 线性不勾 sRGB；灰度图全部通道打包。错一条，整个材质库的"高级感"就没了，且极难事后归因。

**附加：常见"假"的排查顺序（从高发到低发）**
albedo 过暗/过饱和 → roughness 常数 → 法线过强 → 缺 micro-detail → AO 烘进 albedo → Fresnel 缺失（透明物）→ 环境反射缺失（金属发黑）→ Lumen 反射质量不足。

---

## 7. 参考来源

**Epic 官方**
- Substrate 材质总览：https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-substrate-materials-in-unreal-engine
- 物理基础材质（Specular 0.5 = 4%、Specular 实测值表、Metallic 二值规则）：https://dev.epicgames.com/documentation/en-us/unreal-engine/physically-based-materials-in-unreal-engine
- Single Layer Water 着色模型：https://dev.epicgames.com/documentation/en-us/unreal-engine/single-layer-water-shading-model-in-unreal-engine
- Refraction / Pixel Normal Offset：https://dev.epicgames.com/documentation/en-us/unreal-engine/refraction-using-pixel-normal-offset-in-unreal-engine
- Refraction 节点示例 + 常见 IOR 表（Air 1.00 / Water 1.33 / Ice 1.31 / Glass 1.52 / Diamond 2.42）：https://dev.epicgames.com/documentation/en-us/unreal-engine/1.14---refraction-in-unreal-engine
- Decal Materials（DBuffer / GBuffer、Substrate 需 DBuffer）：https://dev.epicgames.com/documentation/en-us/unreal-engine/decal-materials-in-unreal-engine
- Virtual Texturing（RVT vs SVT）：https://dev.epicgames.com/documentation/en-us/unreal-engine/virtual-texturing-in-unreal-engine
- Material Parameter Collection Track：https://dev.epicgames.com/documentation/en-us/unreal-engine/material-parameter-collection-track
- UMaterialParameterCollection API：https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Engine/Materials/UMaterialParameterCollection
- Texture 属性（mip_gen_settings / srgb / flip_green_channel / normalize_normals 官方定义）：https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/ARTextureCameraDepth
- Subsurface Profile 使用：https://dev.epicgames.com/documentation/en-us/unreal-engine/using-subsurface-profiles-in-materials
- Nanite 虚拟化几何（WPO 为 Beta、Morph Target 不支持）：https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine

**Epic 讲稿（UE5.7 语境）**
- Epic Games Japan GCC2026「Substrate 5.7 Production Ready + 转换公式 + CitySample PS5 实测」：https://www.docswell.com/s/EpicGamesJapan/K8N2G7-2026-04-03-230956

**PBR 数值规范**
- Unity PBR Material Validator（50–243 / 186–255 / specular 40–75 / 155–255）：https://docs.unity3d.com/Manual/MaterialValidator.html
- Adobe Substance PBR Guide（albedo 30–50 / 240 sRGB，逐通道）：https://substance3d.adobe.com/tutorials/courses/the-pbr-guide-part-2
- Lagarde 电介质 specular 区间（≥0.02、液体 0.02–0.04、宝石 0.05–0.17、默认 0.04）：https://seblagarde.wordpress.com/2011/08/17/feeding-a-physical-based-lighting-mode/ （经 3dpoder 实测文转引：https://www.3dpoder.com/guia-para-capturar-texturas-pbr/）
- TurboSquid StemCell PBR 规范（电介质 IOR 1–3、金属 8–30、metallic 0.02–0.30 / 0.70–0.98）：https://www.turbosquid.com/Checker/StemCell
- 80.lv UE4 实践（albedo 区间、roughness 0.05–0.95）：https://80.lv/articles/the-substance-of-pbr/

**Nanite / 渲染限制（社区实测）**
- Nanite 不支持半透明（玻璃网格不开 Nanite）：https://forums.unrealengine.com/t/glass-material-messing-up-static-mesh/1941837
- Nanite masked 材质性能代价（Fortnite 放弃 masked）：https://forums.unrealengine.com/t/nanite-material-level-of-detail-performance-masked-materials/1237654
- Nanite masked 支持始于 5.1：https://forums.unrealengine.com/t/will-nanite-ever-support-translucent-and-masked-materials/239729
- WPO + Nanite cluster 剔除（需 clamp WPO）：https://forums.unrealengine.com/t/enabling-nanite-messes-up-uvs-nanite-not-working-with-world-position-offset/1222905
- SingleLayerWater 块状阴影修复 cvar：https://forums.unrealengine.com/t/blocky-shadows-on-single-layer-water/1234567
- UE-102259（SLW + PixelDepthOffset 折射错误）：https://issues.unrealengine.com/issue/UE-102259

**贴图 / 通道打包**
- Quixel ORD 打包（R=AO, G=Roughness, B=Displacement）：https://help.quixel.com/hc/en-us/articles/115000589729-Channel-Packing
- Kodeco UE5 Megascans 教程（ORD 三通道用法）：https://www.kodeco.com/30290630-unreal-engine-5-megascans
- polycount：除 albedo 外一律 sRGB off、Mip Gen 锐化与 LOD Bias 社区共识：https://polycount.com/discussion/184005/normal-map-compression-and-channel-packing
- UE 论坛 Mip Gen Settings / LOD Bias 行为：https://forums.unrealengine.com/t/texture-settings-help-mip-gen-settings-lod-bias-power-of-two-mode/110137

**液体 IOR**
- 乙醇 n≈1.361（多源一致）：https://www.orchidsinternationalschool.com/chemistry-formula/ethanol-formula
- 硫酸铜溶液 IOR 实测文献（按浓度查表，本规范不编数值）：J. Chem. Eng. Data 18(3) 289 — https://pubs.acs.org/jceaax/article/18/3/289/1015916/

> 明确标注为**无公开权威值**的项：硫酸铜/硫酸溶液逐浓度 IOR、镀铬 F0、各材质逐项 roughness 常数、SSS 逐材质 MFP 表。这些数值本规范给出的是区间内工程取值，需在项目标定场景里实测确认。
