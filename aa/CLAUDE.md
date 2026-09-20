# CLAUDE.md — 项目约定

本仓库有两个部分：UE5 项目本体（`Content/`、`Config/`、`Plugins/` 等）与一套
MkDocs 技术文档站（`docs/` → 构建到 `site/`）。下面只写「不看代码就猜不到」的约定。

## UI 工作前必读

**任何改动界面的任务，动手前先读 `DESIGN.md`。**

文档站使用 **Aether** 设计系统（磨砂玻璃材质语言，Apple 风格亮色）。它是一套外部
交付的设计系统，不是本项目自创的，文件分布如下：

| 路径 | 作用 | 能否修改 |
| --- | --- | --- |
| `DESIGN.md` | 设计系统规范（令牌、组件、Do/Don't、无障碍） | 只读参考 |
| `bad-dodo-83-64e996bc/` | 原始指导包：`css/system.css`、`html/preview.html`（视觉参照）、`metadata.json` | 只读，不修改 |
| `docs/stylesheets/system.css` | 设计系统本体，站点实际加载的那一份 | 只做过一处改动（见下），其余**不要就地改**，要改先改指导包再同步 |
| `docs/stylesheets/extra.css` | MkDocs Material 适配层，本项目自己的样式都写在这里 | 可以改 |
| `docs/stylesheets/icons.css` | 图标工具类，由脚本生成 | **勿手工编辑**，见下文 |
| `docs/stylesheets/fonts.css` | 自托管字体的 @font-face，由脚本生成 | **勿手工编辑**，见下文 |
| `docs/fonts/*.woff2` | 字体文件本体（6 个，250KB） | 由脚本下载，不要手工替换 |
| `docs/design-system.md` | 「设计系统」页面，所有组件的实际渲染效果 | 可以改；改样式后顺手核对这里 |

改样式的顺序：读 `DESIGN.md` → 查 `docs/stylesheets/system.css` 有哪些令牌 →
在 `docs/stylesheets/extra.css` 里映射到 Material 的类上 → 对照
`docs/design-system.md` 确认没有破坏已有组件。

### 四条硬约束

1. **不新造颜色。** 颜色只用 `--color-*` 令牌。强调色 `#0a84ff` 只用于焦点、链接、
   开关开启态；石墨 `--color-ink` 只用于主操作、选中态、文字，不做大面积背景。
   适配层自己引入的辅助量用 `--aether-` 前缀（如 `--aether-wash`），与系统令牌区分。
2. **`rem` 要换算。** Aether 的令牌按 `1rem = 16px` 设计，而 Material 把根字号设成
   `125%`（`1rem = 20px`）。`extra.css` 第 1 节已经把间距/字号令牌按 `1rem = 20px`
   重新标定过——写新样式时**直接用 `var(--space-*)` / `var(--text-*)` 即可拿到
   DESIGN.md 里写的真实像素值**，不要再自己乘系数。
3. **焦点态不能删。** 每个可交互表面都要有 `:focus-visible` 焦点环
   （`var(--focus-ring)`）。`DESIGN.md` 明确要求重塑样式时不得移除焦点态。
4. **图标只用 Lucide，不用 Material 自带的那套。** 见下节。

### 图标

图标源文件在 `overrides/.icons/lucide/*.svg`（ISC 许可，1.75 描边，**不要自己编
路径**，从 https://lucide.dev 取）。一套文件服务两个用途：

- **主题外壳**（顶栏、搜索、折叠箭头、代码复制按钮）：在 `mkdocs.yml` 的
  `theme.icon.*` 槽位里指定，走 Material 的配置机制，不改模板，升级不失效。
  代码块按钮和导航箭头是 CSS 遮罩画的，在 `extra.css` 第 9.2 节用
  `--md-code-copy-icon` 一类变量覆盖。
- **文档正文**：跑 `python tools/build_icons_css.py` 生成
  `docs/stylesheets/icons.css`，然后在 Markdown 里写
  `<span class="aa-i aa-i-check"></span>`。加了新图标就重跑一次脚本。

!!! warning "两个已经踩过的坑"

    **一、描边图标会被涂成实心。** Material 的 `.md-icon svg{fill:currentcolor}`
    对 Lucide 这种 `fill="none"` 的描边图标是致命的——`menu`、`x` 这类纯线条图标
    会整块消失。`extra.css` 第 9.1 节必须保留那段 `fill: none` 覆盖。

    **二、`theme.icon.tag` 要的是映射不是字符串。** 写成 `tag: lucide/tag` 会让
    构建直接崩（`Can only get item pairs from a mapping`），得写成
    `tag: { default: lucide/tag }`。

### 层叠顺序（决定了覆盖能否生效）

`main.css` → `palette.css` → `system.css` → `extra.css` → `icons.css`。
`extra.css` 靠「同特异度、后加载者胜」覆盖 Material，所以**顺序不能乱**。

两个已经踩过的坑：

- **`extra_css` 是 MkDocs 的顶层配置项，不能写在 `theme:` 下面**。写在 `theme:`
  下会被静默忽略，样式表链接根本不会出现在 HTML 里（这个 bug 在本项目里真实存在过，
  表现为改了 CSS 完全没反应）。
- **Material 有一批选择器带 `[dir=ltr]` / `[dir=rtl]` 前缀**，特异度是 0,2,1，
  比裸的 `.md-typeset xxx`（0,1,1）高。引用块的左边框就吃过这个亏：不写成
  `[dir] .md-typeset blockquote`，8px 的灰色竖条会一直留在那里。

### 字体必须自托管

`docs/fonts/*.woff2` + `docs/stylesheets/fonts.css`，由 `tools/fetch_fonts.py` 生成。

**不要改回 Google Fonts。** 原始 `system.css` 是用 `@import` 从 fonts.googleapis.com
拉 Inter 和 JetBrains Mono 的，这在两个方面不可接受：googleapis.com 在国内不可达，
字体加载不到；而且 CSS `@import` 是**阻塞渲染**的，拉不到时会白屏好几秒。
自托管之后站点 100% 自包含，内网、断网都能正常显示。

为此 `docs/stylesheets/system.css` 与指导包**不再是逐字节一致**——只删了那两行
`@import`，文件头有注释说明，其余内容未动。原始版本仍在
`bad-dodo-83-64e996bc/css/system.css`。这是唯一允许的偏离。

只下了 latin 子集：中文由系统字体（苹方 / 微软雅黑）兜底，不需要 CJK 字体文件。

### 图片放大

正文图片点击放大，实现在 `docs/javascripts/lightbox.js` + `extra.css` 第 12 节。
**没有用 `mkdocs-glightbox`**——那会给团队增加一个 pip 依赖，而且它的视觉和
Aether 不是一套。自制的这个用同一套玻璃材质，样式跟着设计系统走。

脚本挂在 Material 的 `window.document$` 上（Material 用的是即时导航，切页面不会
重新加载，所以每次内容替换后都要重新给图片挂行为）。这个 Observable 由
Material 的 bundle 暴露，而 bundle 是同步脚本、`extra_javascript` 排在它后面，
所以能拿到。

它在加载时给正文图片加 `tabindex` / `role="button"`，所以**图片是可聚焦的**——
改这段代码时别把焦点态弄丢。

### 暗色模式

`DESIGN.md` 只定义了亮色。暗色是本项目**对设计系统的扩展**，取值全部来自 Aether
自己的墨色家族（`#1d1d1f` / `#f5f5f7` / `#86868b`），没有引入新色相，实现在
`extra.css` 第 3 节。扩展时要保持这条纪律。

## 文档站

```bash
mkdocs serve          # 本地预览 http://127.0.0.1:8000，带热重载
mkdocs build --clean  # 构建到 site/
```

- 用 `mkdocs build --clean` 而不是 `mkdocs build`：站点是纯静态产物，增量构建容易
  留下上一次的陈旧文件。
- `docs/` 下不在 `nav:` 里的 md 文件仍会被构建成 HTML，只是不出现在导航中。
- `site/` 是构建产物，不要手工编辑——改了会在下次构建时被覆盖。
- **`mkdocs build --clean` 会清空 `site/`**。里面有 `ui.zip` 这类手工放进去的文件，
  会被一起删掉（发生过一次）。这也是建议把 `site/` 移出版本控制的原因，见 `DEPLOY.md`。
- 正文里的中文标题锚点能用（`[文字](#按钮)`），靠的是 `mkdocs.yml` 里把 `toc.slugify`
  换成了 `pymdownx.slugs.slugify`。MkDocs 默认实现会把非 ASCII 字符全部丢掉，
  中文标题的锚点会退化成 `#_1` `#_2`。

### `本地预览.cmd` — 改之前先读这段

给不装工具的同事双击用的本地预览脚本。两条约束，破坏任何一条这个脚本就废了：

1. **文件必须保持纯 ASCII。** 本机控制台代码页是 936（GBK），在这个文件里混编码
   会让 cmd.exe 把中文行拆开当成命令去执行。中文说明写在 `docs/打开网页.md` 里。
2. **保持 CRLF 换行。** cmd.exe 对纯 LF 的批处理文件支持很差。

脚本的作用是起一个本地 HTTP 服务器。**不能靠双击 `site/index.html` 看站点**——
MkDocs 生成的是目录式链接（`animation/level-sequence/`），磁盘上是
`.../index.html`，只有 HTTP 服务器会做这个映射，`file://` 只会显示文件夹列表。

## 部署

站点是纯静态文件，部署 = 构建 + 把 `site/` 传到服务器。目标环境是自有服务器的 Nginx。

具体步骤见知识库的《静态站部署实操手册》：
`D:\OBSIDIAN\知识库\wiki\项目记录\静态站部署实操手册.md`

> 原先的 `DEPLOY.md` 已整理进知识库，改成通用版本（占位符替换即可用），
> 并补充了大小写敏感、多站点共存等排错项。内容与原来一致，位置变了。
