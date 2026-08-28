import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  HelpCircle,
  Home,
  BookOpen,
  FileText,
  Settings,
  Lightbulb,
  MessageSquare,
  Sparkles,
  ChevronRight,
} from 'lucide-react'

interface Section {
  id: string
  title: string
  icon: React.ReactNode
}

const SECTIONS: Section[] = [
  { id: 'quickstart', title: '快速开始', icon: <Home size={16} /> },
  { id: 'workspace', title: '创作工作区', icon: <BookOpen size={16} /> },
  { id: 'config', title: '配置页', icon: <FileText size={16} /> },
  { id: 'reader', title: '阅读页', icon: <BookOpen size={16} /> },
  { id: 'assist', title: '辅助工具', icon: <Lightbulb size={16} /> },
  { id: 'community', title: '社区', icon: <MessageSquare size={16} /> },
  { id: 'llm', title: 'LLM 配置', icon: <Settings size={16} /> },
]

export default function Help() {
  const [active, setActive] = useState('quickstart')

  const go = (id: string) => {
    setActive(id)
    const el = document.getElementById(id)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 flex gap-6">
      {/* 左侧导航 */}
      <aside className="w-56 shrink-0 hidden md:block">
        <div className="sticky top-6">
          <div className="text-sm font-bold flex items-center gap-2 mb-3 text-gray-700">
            <HelpCircle size={18} /> 使用文档
          </div>
          <nav className="space-y-0.5">
            {SECTIONS.map((s) => (
              <button
                key={s.id}
                onClick={() => go(s.id)}
                className={`w-full text-left px-3 py-1.5 rounded text-sm flex items-center gap-2 transition ${
                  active === s.id
                    ? 'bg-primary/10 text-primary font-medium'
                    : 'text-muted-foreground hover:bg-muted'
                }`}
              >
                {s.icon}
                {s.title}
                {active === s.id && <ChevronRight size={12} className="ml-auto" />}
              </button>
            ))}
          </nav>
          <div className="mt-6 pt-4 border-t text-xs text-gray-400">
            <Link to="/" className="hover:text-blue-600">← 返回首页</Link>
          </div>
        </div>
      </aside>

      {/* 移动端章节选择 */}
      <div className="md:hidden -mt-2 mb-4">
        <select
          value={active}
          onChange={(e) => go(e.target.value)}
          className="w-full border rounded-lg px-3 py-2 text-sm bg-white"
        >
          {SECTIONS.map((s) => (
            <option key={s.id} value={s.id}>
              {s.title}
            </option>
          ))}
        </select>
      </div>

      {/* 右侧内容 */}
      <article className="flex-1 min-w-0 prose prose-sm max-w-none text-gray-700">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">StoryClaw 使用文档</h1>
        <p className="text-gray-500 mb-8">AI 辅助小说创作平台 · 从入门到精通</p>

        {/* 1. 快速开始 */}
        <Section id="quickstart" title="1. 快速开始" icon={<Home size={20} />}>
          <p>
            StoryClaw 是一个面向网络小说创作者的 AI 辅助写作平台，支持本地版（自带 LLM 配置）与商业版（按积分计费）两种模式。
          </p>
          <H>注册与登录</H>
          <p>
            访问首页后，点击「去注册」创建账户（用户名 + 密码），或直接「去登录」使用已有账户。
            登录后会跳转回来源页面或个人主页。
          </p>
          <H>创建书籍</H>
          <p>
            在个人主页（<Link to="/" className="text-blue-600">/</Link>）点击右上角「新建书籍」，
            填写书名、简介、类型（都市/玄幻/仙侠…）、目标平台、预计章数与总字数。
            系统会自动计算每章字数建议。主角名与主角介绍可帮助 AI 在后续生成时保持人设一致。
            提交后会自动在新标签页打开工作区。
          </p>
          <H>开始创作</H>
          <p>
            进入工作区（<code className="bg-gray-100 px-1 rounded">/workspace/:bookId</code>）后，
            默认展示「创作」标签页。左侧为目录树，可新建分卷与章节；
            右侧为富文本编辑器（基于 Tiptap），支持加粗、标题、高亮、列表等格式。
            在编辑器中输入文字，系统会自动保存（带「已保存」状态提示）。
          </p>
        </Section>

        {/* 2. 创作工作区 */}
        <Section id="workspace" title="2. 创作工作区" icon={<BookOpen size={20} />}>
          <p>
            工作区是创作的核心页面，提供编辑、AI 写作、阅读、配置、数据库等多标签页能力。
          </p>
          <H>编辑器</H>
          <p>
            富文本编辑器支持基础排版：加粗（<strong>B</strong>）、斜体（<em>I</em>）、
            H1/H2 标题、高亮、有序/无序列表。内容变更会自动节流保存到后端，
            顶部会显示「保存中…/已保存/保存失败」状态。
          </p>
          <H>AI 辅助写作</H>
          <p>编辑器下方工具栏提供四类核心 AI 能力：</p>
          <ul className="list-disc pl-6 space-y-1">
            <li>
              <strong>润色（Polish）</strong>：选中一段文字，点击「润色」，AI 会按目标（流畅/紧凑/生动…）改写选中片段，结果会替换原文。
            </li>
            <li>
              <strong>续写（Continue）</strong>：基于当前章节已有内容，AI 续写后续段落，可设置最大字数。
            </li>
            <li>
              <strong>多章生成（Multi-Write）</strong>：指定起始章号与生成数量，AI 批量生成多个章节，可勾选「跳过已存在章节」。
            </li>
            <li>
              <strong>分析（Analyze）</strong>：提供情节规划、人物发展、一致性检查、全书摘要、大纲规划五种 skill，输出结构化报告。
            </li>
          </ul>
          <p>
            所有 AI 调用均通过 SSE 流式输出，可在对话区看到实时进度（节点切换、状态更新、最终结果）。
            商业版会扣减积分，本地版消耗自有 LLM 配额。
          </p>
        </Section>

        {/* 3. 配置页 */}
        <Section id="config" title="3. 配置页" icon={<FileText size={20} />}>
          <p>
            工作区顶部提供五类配置实体标签页，用于沉淀设定、辅助 AI 生成与保持一致性：
          </p>
          <ul className="list-disc pl-6 space-y-2">
            <li>
              <strong>角色（character）</strong>：人物名称、性格、外貌、关系。AI 在续写/分析时会参考。
            </li>
            <li>
              <strong>场景（scene）</strong>：地点、环境、氛围。用于场景增强与一致性。
            </li>
            <li>
              <strong>物品（item）</strong>：道具、武器、法宝等关键物品。
            </li>
            <li>
              <strong>情节（plot）</strong>：主线/支线节点、伏笔、转折。
            </li>
            <li>
              <strong>大纲（outline）</strong>：分卷与章节大纲，可由 AI 生成或手动编辑，多章生成会以此为蓝本。
            </li>
          </ul>
          <p>
            每个实体支持名称、分类、描述、图片、扩展 JSON 与键值对（KV）。
            点击实体可加载其 RAG 关联（相似片段、相关实体与关系），方便梳理脉络。
          </p>
        </Section>

        {/* 4. 阅读页 */}
        <Section id="reader" title="4. 阅读页" icon={<BookOpen size={20} />}>
          <p>
            工作区「阅读」标签页提供沉浸式阅读体验，左侧目录、右侧正文，
            顶部工具栏可调节字号、字体、行距、页边距、亮度，并提供五种预设场景：
            日间 / 夜间 / 护眼 / 沉浸 / 户外。
          </p>
          <H>阅读配置</H>
          <p>
            点击齿轮图标可展开完整配置面板，包含字号（14-24）、字体（衬线/无衬线）、
            行距（1.4-2.2）、页边距（窄/中/宽）、背景色、文字颜色、亮度（0.3-1.0）等参数。
            配置会自动持久化到 localStorage（key 形如
            <code className="bg-gray-100 px-1 rounded mx-1">reader-config-{`{bid}`}</code>）。
          </p>
          <H>模板导入导出</H>
          <p>
            点击「保存」按钮可将当前配置存为模板（命名），方便跨书籍复用；
            已存模板可一键应用、导出为 JSON 文件，或从粘贴的 JSON 导入。
          </p>
          <H>公开阅读页</H>
          <p>
            社区帖子中引用的书籍会跳转到只读阅读页（<code className="bg-gray-100 px-1 rounded">/read/:bookId</code>），
            无需登录即可阅读，复用同一套阅读配置系统。
          </p>
        </Section>

        {/* 5. 辅助工具 */}
        <Section id="assist" title="5. 辅助工具" icon={<Lightbulb size={20} />}>
          <p>辅助工具是一组独立的创意生成 skill，适合在动笔前或卡壳时使用：</p>
          <ul className="list-disc pl-6 space-y-2">
            <li>
              <strong>头脑风暴（brainstorm）</strong>：给定主题/类型/方向，生成多个创意点子。
            </li>
            <li>
              <strong>标题生成（title-generation）</strong>：基于内容或关键词，生成多个候选书名/章节名。
            </li>
            <li>
              <strong>场景增强（scene-enhance）</strong>：扩写场景描写，可指定感官维度、氛围、视角，并保持长度。
            </li>
            <li>
              <strong>对话润色（dialogue-polish）</strong>：按角色性格与说话风格改写对白，可保留关键信息。
            </li>
          </ul>
          <p>
            此外还有「阅读配置生成（reading-config-gen）」可基于场景与偏好自动生成阅读配置 JSON。
          </p>
        </Section>

        {/* 6. 社区 */}
        <Section id="community" title="6. 社区" icon={<MessageSquare size={20} />}>
          <p>
            社区页（<Link to="/community" className="text-blue-600">/community</Link>）是公开的交流空间，
            无需登录即可浏览帖子与搜索。
          </p>
          <H>发帖</H>
          <p>
            登录后点击右上角「发帖」，填写标题与内容即可发布。
            编辑器支持纯文本，按空行自动分段。
          </p>
          <H>书籍引用 <code className="bg-gray-100 px-1 rounded">[[book:id]]</code></H>
          <p>
            在帖子内容中使用
            <code className="bg-gray-100 px-1 rounded mx-1">[[book:12]]</code>
            语法引用书籍（数字为书籍 ID）。
            后端会自动将其渲染为指向
            <code className="bg-gray-100 px-1 rounded mx-1">/read/12</code>
            的可点击链接，并在帖子下方聚合展示关联书籍卡片。
          </p>
          <H>搜索</H>
          <p>
            顶部搜索栏可同时检索帖子与书籍，结果分区显示。
            点击书籍结果会跳转到对应的只读阅读页。
          </p>
          <H>帖子详情</H>
          <p>
            帖子详情页（<code className="bg-gray-100 px-1 rounded">/post/:id</code>）渲染正文 HTML，
            其中的书籍链接会被拦截为客户端路由跳转（避免整页刷新）。
            作者可见编辑与删除按钮。
          </p>
        </Section>

        {/* 7. LLM 配置 */}
        <Section id="llm" title="7. LLM 配置" icon={<Settings size={20} />}>
          <p>根据账户版本不同，模型配置方式有差异：</p>
          <H>本地版（local）</H>
          <p>
            本地版用户可在「配置」页（<Link to="/llm-configs" className="text-blue-600">/llm-configs</Link>）
            自行管理 LLM 配置：
          </p>
          <ul className="list-disc pl-6 space-y-1">
            <li>名称、格式（openai_chat / anthropic / openai_responses）、base_url、model、temperature、max_tokens</li>
            <li>API Key 仅在创建/更新时提交，后端不回显</li>
            <li>可标记一个默认配置，对话与 AI 写作默认使用它</li>
          </ul>
          <H>商业版（business）</H>
          <p>
            商业版用户无需自配模型，平台提供预设模型与定价，按 token 计费扣减积分。
            顶部导航栏会显示当前剩余积分。每次 AI 调用结束后会展示本次消耗的输入/输出 token 与积分成本。
          </p>
          <H>选择模型</H>
          <p>
            在对话页或工作区的 AI 工具栏中，可下拉切换使用的 LLM 配置/模型；
            不选择时使用默认配置。所有调用均会记录到对话线程，便于回溯与分享。
          </p>
        </Section>

        <div className="mt-12 pt-6 border-t text-xs text-gray-400 flex items-center gap-1">
          <Sparkles size={12} /> StoryClaw · AI 辅助小说创作平台
        </div>
      </article>
    </div>
  )
}

function Section({ id, title, icon, children }: { id: string; title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <section id={id} className="mt-10 pt-6 border-t first-of-type:border-t-0 first-of-type:mt-0 first-of-type:pt-0 scroll-mt-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-3 flex items-center gap-2">
        {icon} {title}
      </h2>
      <div className="space-y-3 leading-relaxed">{children}</div>
    </section>
  )
}

function H({ children }: { children: React.ReactNode }) {
  return <h3 className="text-base font-semibold text-gray-800 mt-4 mb-1">{children}</h3>
}
