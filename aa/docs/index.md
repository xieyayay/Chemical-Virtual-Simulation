<div class="aa-hero" markdown>

<span class="badge">UE 5.4.4 · 全蓝图实现</span>

# 虚拟仿真化学实验教学软件

一份写给「后来接手这个项目的人」的技术文档 —— 顺带也是给自己的一份回顾总结。

[开始阅读](getting-started/project-overview.md){ .md-button .md-button--primary }
[设计系统](design-system.md){ .md-button }

</div>

## 文档导航

| 章节 | 说明 |
|------|------|
| [复盘路线图](复盘/路线图.md) | 22 个任务卡 + 状态表：怎么系统地回顾这个项目 |
| [知识地图](kb/index.md) | 70 张知识卡索引，每张写清「该能回答什么问题」 |
| [架构图](复盘/架构图.md) | 可交互：分层总览 / 启动链路 / 交互链路 |
| [快速入门](getting-started/project-overview.md) | 怎么打开项目、目录结构、环境配置 |
| [关卡序列动画](animation/level-sequence.md) | Sequencer 制作、蓝图交互、步骤跳转 |
| [Widget UI](ui/widget-overview.md) | UMG 控件、数据绑定、事件处理 |
| [UI 动画](ui/widget-animation.md) | Widget 动效、入场退场、缓动 |
| [蓝图笔记](blueprints/blueprint-notes.md) | 蓝图通信、命名规范 |
| [AI 对话](systems/ai-dialog.md) | API 接入、对话面板、TTS |
| [任务系统](systems/task-system.md) | DataTable 驱动、步骤推进 |
| [交互系统](systems/interaction-system.md) | 接口 + 50 个交互点，最大技术债在哪 |
| [关卡加载](systems/level-streaming.md) | 流式加载、加载界面 |
| [模型](assets/models.md) | 命名规范、碰撞、常见问题 |
| [插件](plugins/third-party.md) | 第三方插件清单与用法 |

## 如何编写

1. **每个 .md 文件只负责一个主题**，不要太长（200-500 行为宜）
2. **多用代码块**展示蓝图逻辑、配置段落——比纯文字直观
3. **截图放在 `docs/images/`** 目录下，用相对路径引用 —— 正文里的图片**点击就能放大**，
   不用做任何额外设置
4. **中文文档**，变量名/函数名保留英文

!!! tip "想加一个按钮？"

    正文里可以直接写：

    ```
    [按钮文字](链接){ .md-button }
    [主要按钮](链接){ .md-button .md-button--primary }
    ```

    这是 MkDocs 的标准写法，不需要懂 HTML。可用的样式和组件见
    [设计系统](design-system.md)。
