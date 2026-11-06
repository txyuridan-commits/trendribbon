import os, json, re, hashlib
from datetime import datetime
from pathlib import Path

import streamlit as st
import requests

APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
KNOWLEDGE_DIR = APP_DIR / "knowledge"
HISTORY_FILE = DATA_DIR / "history.json"
LIBRARY_FILE = DATA_DIR / "products.json"
KNOWLEDGE_INDEX = DATA_DIR / "knowledge.json"

DATA_DIR.mkdir(exist_ok=True)
KNOWLEDGE_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="TrendRibbon｜绳带辅料 AI 开发工作台", page_icon="🧵", layout="wide")

# ---------- Persistence ----------
def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except Exception:
        return default

def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def now_id():
    return datetime.now().strftime("%Y%m%d-%H%M%S")

# ---------- Knowledge base ----------
def extract_text(name, raw):
    suffix = Path(name).suffix.lower()
    if suffix in [".txt", ".md", ".csv", ".json"]:
        return raw.decode("utf-8", errors="ignore")
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
            import io
            reader = PdfReader(io.BytesIO(raw))
            return "\n".join(p.extract_text() or "" for p in reader.pages)
        except Exception as e:
            return f"[PDF 解析失败: {e}]"
    if suffix == ".docx":
        try:
            from docx import Document
            import io
            doc = Document(io.BytesIO(raw))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            return f"[DOCX 解析失败: {e}]"
    return ""

def retrieve_knowledge(query, limit=5):
    docs = load_json(KNOWLEDGE_INDEX, [])
    terms = set(re.findall(r"[\w\u4e00-\u9fff]+", query.lower()))
    scored = []
    for d in docs:
        body = (d.get("text", "") + " " + d.get("name", "")).lower()
        score = sum(1 for t in terms if len(t) > 1 and t in body)
        if score:
            scored.append((score, d))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in scored[:limit]]

# ---------- AI ----------
SYSTEM_PROMPT = """你是 TrendRibbon，一名专业的绳带、织带及服装辅料产品开发顾问。
服务对象是绳带辅料工厂开发人员、设计师和外贸业务员。
严格遵守：
1. 不得虚构工厂已有设备、认证、工艺能力、供应商、成本、交期或测试结果。
2. 将内容区分为「趋势/客户输入」「AI设计建议」「待工厂验证」。
3. 输出可执行的产品开发信息，避免空泛营销语言。
4. 需要生成三套明显不同的方案：A 商业易落地、B 时尚设计感、C 创新功能/结构。
5. 输出必须是合法 JSON，不要 Markdown 代码围栏。
JSON结构：
{
 "summary":"...",
 "concepts":[
  {"code":"TR-001","name":"中文名称","name_en":"English name","positioning":"定位",
   "design_rationale":"设计理念","product_type":"产品类型","materials":["材料"],
   "structure":"结构","processes":["建议工艺"],"colors":["颜色"],
   "accessories":["配件"],"applications":["应用场景"],
   "selling_points":["卖点"],"factory_checks":["待工厂确认项"],
   "feasibility":"高/中/待验证","visual_prompt":"英文静物产品效果图提示词",
   "pitch_zh":"中文推介文案","pitch_en":"English pitch"}
 ],
 "recommendation":"优先建议及原因",
 "missing_information":["仍需补充的信息"]
}
"""

def demo_result(mode, brief, context):
    base = [
      {
        "code":"TR-001","name":"反光机能户外抽绳","name_en":"Reflective Utility Drawcord",
        "positioning":"商业易落地｜户外与运动服装",
        "design_rationale":"以高密度绳体结合局部反光元素，在不明显增加视觉负担的前提下提升夜间识别度。",
        "product_type":"圆形抽绳","materials":["涤纶纱","反光纱（建议）"],
        "structure":"高密度圆绳，反光纱间隔嵌入或表层并股。",
        "processes":["圆绳编织","绳头包覆或热封（按材料验证）"],
        "colors":["黑/反光银","深海军蓝/反光灰","深绿/反光银"],
        "accessories":["TPU绳头（可选）","低轮廓调节扣（可选）"],
        "applications":["户外夹克","运动裤","功能背包"],
        "selling_points":["功能识别清晰","适合基础款升级","可延展多色系列"],
        "factory_checks":["确认反光纱能否稳定并入现有编织结构","测试反光效果与耐洗性","验证绳头连接强度"],
        "feasibility":"待验证","visual_prompt":"Premium studio product photography of a technical reflective drawcord, tightly braided dark navy polyester cord with subtle silver reflective tracer, clean TPU aglet, isolated on warm light grey background, macro detail, soft directional lighting, no text, no logo.",
        "pitch_zh":"以细节反光提升户外辅料的功能识别度，适合运动与轻户外系列开发。",
        "pitch_en":"A technical drawcord with subtle reflective detailing, designed to add functional visibility to outdoor and activewear collections."
      },
      {
        "code":"TR-002","name":"混色肌理装饰绳","name_en":"Melange Tactile Fashion Cord",
        "positioning":"时尚设计感｜休闲、女装与包袋",
        "design_rationale":"通过混色纱线与不规则肌理编织，强调手作感和触觉层次，让绳带成为可见的设计细节。",
        "product_type":"装饰圆绳/扁绳","materials":["棉纱或棉涤混纺纱","双色/多色纱线"],
        "structure":"多股混色编织，可延伸结饰、环圈或短流苏。",
        "processes":["混色并纱","编织","绳结整理（建议）"],
        "colors":["赤褐/米白","丁香紫/浅灰","玉米黄/深蓝"],
        "accessories":["哑光金属绳头（可选）","包覆绳头（可选）"],
        "applications":["卫衣抽绳","针织外套","手袋与鞋履装饰"],
        "selling_points":["触感和视觉辨识度高","适合胶囊系列","颜色组合易做系列化"],
        "factory_checks":["确认纱线来源与可持续供货","测试掉毛、色牢度及结饰牢度","评估批量颜色一致性"],
        "feasibility":"待验证","visual_prompt":"Editorial macro still-life of a tactile melange fashion cord, chunky braided cotton blend fibers in rust brown and natural ecru, a small handcrafted loop and neat finished tip, premium fashion trims product photography, neutral studio background, no text, no logo.",
        "pitch_zh":"以混色纱线和立体编织打造更有触感的装饰绳，让基础服装细节更具设计感。",
        "pitch_en":"A tactile melange cord with dimensional braided texture, bringing a crafted design accent to casual apparel and accessories."
      },
      {
        "code":"TR-003","name":"几何提花机能织带","name_en":"Graphic Jacquard Utility Webbing",
        "positioning":"创新结构｜运动与户外装备",
        "design_rationale":"将几何图形、对比色和功能扣具组合，形成具有品牌识别度的织带系统。",
        "product_type":"提花织带","materials":["涤纶纱","再生涤纶纱（可选）"],
        "structure":"双/多色提花结构，搭配可拆卸扣具或环形连接。",
        "processes":["提花织造","定型整理","裁切与端部处理"],
        "colors":["深绿/黑","科技蓝/银灰","黑/玉米黄"],
        "accessories":["D形环（可选）","插扣（可选）","织带拉环（可选）"],
        "applications":["机能背包","运动服装","户外装备"],
        "selling_points":["图形识别度强","可延展宽度和配色","便于形成系列化辅料"],
        "factory_checks":["确认现有织机支持的宽度与提花复杂度","验证织带厚度、拉力和耐磨","核对再生纱供应及认证要求"],
        "feasibility":"待验证","visual_prompt":"High-end technical trims product still life of a geometric jacquard webbing strap, deep forest green and black woven graphic pattern, neatly folded with one matte dark metal D-ring, crisp weave detail, neutral studio background, no text, no logo.",
        "pitch_zh":"以几何提花和功能配件构建完整机能织带方案，适合背包、运动和户外产品线。",
        "pitch_en":"A graphic jacquard webbing concept combining distinctive woven patterning with functional hardware for active and outdoor accessories."
      }
    ]
    if mode == "趋势调研":
        summary = "本次演示基于输入关键词生成趋势假设。正式趋势结论应补充可追溯来源、发布日期和市场范围。"
    elif mode == "客户需求":
        summary = "已将客户需求转化为三条不同开发路径。请补齐尺寸、测试标准、目标成本和交期后再进入打样。"
    else:
        summary = "已生成三条差异化新品开发路径，可作为内部概念评审起点。"
    return {"summary":summary, "concepts":base,
            "recommendation":"建议先评估 TR-001 的工艺兼容性与 TR-003 的织造能力，再决定打样顺序；此排序是开发建议，不代表市场销量预测。",
            "missing_information":["目标产品尺寸/直径/宽度","目标市场与价格带","现有设备及可用材料","测试标准与交期"]}

def call_ai(mode, brief, context, api_key, base_url, model):
    if not api_key:
        return demo_result(mode, brief, context), "演示模式"
    user_prompt = f"""业务模式：{mode}
用户输入：{brief}
知识库检索内容（仅作参考，不能推断未提供的工厂能力）：
{context[:12000]}
请严格按系统要求输出 JSON。"""
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {"model":model, "temperature":0.6,
               "messages":[{"role":"system","content":SYSTEM_PROMPT},
                           {"role":"user","content":user_prompt}]}
    r = requests.post(url, headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},
                      json=payload, timeout=120)
    r.raise_for_status()
    content = r.json()["choices"][0]["message"]["content"]
    content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip())
    return json.loads(content), "AI API"

# ---------- Styling ----------
st.markdown("""
<style>
.block-container{padding-top:1.4rem;padding-bottom:2rem;max-width:1500px}
.hero{padding:1.3rem 1.5rem;border-radius:18px;background:linear-gradient(120deg,#172b3a,#315c61);color:white;margin-bottom:1rem}
.hero h1{font-size:2rem;margin:0 0 .3rem 0}
.hero p{opacity:.85;margin:0}
.small-muted{color:#718096;font-size:.88rem}
div[data-testid="stMetric"]{background:#f5f7f8;padding:12px;border-radius:12px}
</style>
""", unsafe_allow_html=True)

# 修复首页快捷导航
if "nav_target" in st.session_state:
    st.session_state["page_nav"] = st.session_state.pop("nav_target")

with st.sidebar:
    st.markdown("## 🧵 TrendRibbon")
    st.caption("AI Fashion Trims Development Studio")
    page = st.radio(
        "工作台",
        ["Dashboard","新品开发","客户需求方案","趋势调研","产品库","历史记录","知识库","设置"],
        label_visibility="collapsed",
        key="page_nav"
    )
    st.divider()
    st.caption("开发原则")
    st.caption("AI 建议 ≠ 工厂已验证工艺")
    st.caption("所有打样、成本、交期需人工确认")

st.markdown('<div class="hero"><h1>TrendRibbon</h1><p>从趋势洞察到辅料产品方案，让绳带开发更快、更有方向。</p></div>', unsafe_allow_html=True)

history = load_json(HISTORY_FILE, [])
products = load_json(LIBRARY_FILE, [])
knowledge = load_json(KNOWLEDGE_INDEX, [])

if page == "Dashboard":
    st.subheader("开发工作台")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("方案生成记录", len(history))
    c2.metric("产品库项目", len(products))
    c3.metric("知识库资料", len(knowledge))
    c4.metric("本地运行状态", "正常")
    st.markdown("### 从一个需求开始")
    cols = st.columns(3)
    entries = [("新品开发","从产品方向生成三套差异化辅料概念。","新品开发"),
               ("客户需求方案","把客户 brief 转成可沟通的产品提案。","客户需求方案"),
               ("趋势调研","整理趋势信号并转化为辅料开发机会。","趋势调研")]
    for col,(title,desc,target) in zip(cols,entries):
        with col:
            st.markdown(f"#### {title}")
            st.write(desc)
            if st.button(f"开始{title}", key=f"go_{target}", use_container_width=True):
                st.session_state["nav_target"] = target
                st.rerun()
    st.markdown("### 最近方案")
    if history:
        for item in history[-5:][::-1]:
            st.write(f"**{item.get('title','未命名')}** · {item.get('created_at','')} · {item.get('mode','')}")
    else:
        st.info("还没有生成记录。进入「新品开发」创建第一份方案。")
    st.caption("提示：演示模式可直接体验；配置 API Key 后可调用真实模型。")

elif page in ["新品开发","客户需求方案","趋势调研"]:
    mode = page
    st.subheader({"新品开发":"新品开发策划","客户需求方案":"客户需求转产品方案","趋势调研":"趋势调研与辅料机会"}[mode])
    if mode == "新品开发":
        brief = st.text_area("描述你想开发的产品方向", placeholder="例如：开发适合轻户外夹克的轻量抽绳，偏机能风，主色深绿和科技蓝。", height=130)
        extra = st.text_input("目标品类/应用", placeholder="户外服装、运动裤、背包……")
    elif mode == "客户需求方案":
        brief = st.text_area("粘贴客户需求或邮件内容", placeholder="客户需要一款用于运动外套的抽绳，要求轻量、耐洗、深色系，预计下季度上市……", height=170)
        extra = st.text_input("客户/品牌/市场（可选）")
    else:
        brief = st.text_area("输入趋势主题或调研范围", placeholder="例如：SS27 户外运动、机能风、可持续材料、装饰性抽绳……", height=130)
        extra = st.text_input("季节/市场", placeholder="SS27 / 欧洲运动户外")
    with st.expander("高级约束（建议填写）"):
        materials = st.text_input("可用材料", placeholder="涤纶、棉、再生涤纶、TPU……")
        processes = st.text_input("已知可用工艺/设备", placeholder="圆绳编织、提花织带、包覆绳头……")
        limits = st.text_input("限制条件", placeholder="目标宽度、直径、颜色、测试标准、预算、交期……")
    if st.button("✨ 生成 3 套开发方案", type="primary", use_container_width=True):
        if not brief.strip():
            st.warning("请先填写需求或开发方向。")
        else:
            cfg = load_json(DATA_DIR/"settings.json", {})
            docs = retrieve_knowledge(brief + " " + extra + " " + materials + " " + processes)
            context = "\n\n".join(f"资料：{d['name']}\n{d['text'][:2500]}" for d in docs)
            full_brief = f"{brief}\n补充：{extra}\n材料：{materials}\n工艺：{processes}\n限制：{limits}"
            with st.spinner("正在整理需求、检索知识库并生成方案……"):
                try:
                    result, source = call_ai(mode, full_brief, context, cfg.get("api_key",""), cfg.get("base_url","https://api.openai.com/v1"), cfg.get("model","gpt-4o-mini"))
                    record = {"id":now_id(),"created_at":datetime.now().strftime("%Y-%m-%d %H:%M"),
                              "mode":mode,"title":brief[:48],"brief":full_brief,"result":result,"source":source}
                    history.append(record); save_json(HISTORY_FILE, history)
                    st.session_state["latest_result"] = record
                except Exception as e:
                    st.error(f"生成失败：{e}")
    record = st.session_state.get("latest_result")
    if record and record.get("mode") == mode:
        result = record["result"]
        st.success(f"生成完成 · {record.get('source','')} · {record.get('created_at','')}")
        st.write(result.get("summary",""))
        concepts = result.get("concepts",[])
        for i, concept in enumerate(concepts):
            with st.container(border=True):
                st.markdown(f"### {concept.get('code','')}｜{concept.get('name','')}")
                st.caption(f"{concept.get('name_en','')} · {concept.get('positioning','')}")
                st.write(concept.get("design_rationale",""))
                a,b,c = st.columns(3)
                a.markdown("**材料**"); a.write("、".join(concept.get("materials",[])))
                b.markdown("**结构**"); b.write(concept.get("structure",""))
                c.markdown("**可行性**"); c.write(concept.get("feasibility","待验证"))
                d,e = st.columns(2)
                with d:
                    st.markdown("**建议工艺**"); st.write("、".join(concept.get("processes",[])))
                    st.markdown("**颜色**"); st.write("、".join(concept.get("colors",[])))
                    st.markdown("**配件**"); st.write("、".join(concept.get("accessories",[])))
                with e:
                    st.markdown("**应用场景**"); st.write("、".join(concept.get("applications",[])))
                    st.markdown("**卖点**"); st.write("；".join(concept.get("selling_points",[])))
                    st.markdown("**待工厂确认**"); st.write("；".join(concept.get("factory_checks",[])))
                with st.expander("中英文推介文案与效果图 Prompt"):
                    st.markdown("**中文**"); st.write(concept.get("pitch_zh",""))
                    st.markdown("**English**"); st.write(concept.get("pitch_en",""))
                    st.markdown("**Visual prompt**"); st.code(concept.get("visual_prompt",""))
                if st.button("＋ 保存到产品库", key=f"save_{record['id']}_{i}"):
                    products.append({"saved_at":datetime.now().strftime("%Y-%m-%d %H:%M"),"source_id":record["id"],**concept})
                    save_json(LIBRARY_FILE, products)
                    st.toast("已保存到产品库")
        st.markdown("### 开发建议")
        st.write(result.get("recommendation",""))
        if result.get("missing_information"):
            st.markdown("**仍需补充的信息**")
            st.write("；".join(result["missing_information"]))
        st.warning("以上内容属于 AI 概念建议，不代表工厂已具备对应工艺、材料、认证或测试能力。")
        st.download_button("下载本次方案 JSON", json.dumps(record,ensure_ascii=False,indent=2), file_name=f"TrendRibbon_{record['id']}.json", mime="application/json")

elif page == "产品库":
    st.subheader("产品库")
    if not products:
        st.info("暂无已保存产品。在方案卡片中点击「保存到产品库」。")
    else:
        for p in products[::-1]:
            with st.container(border=True):
                st.markdown(f"**{p.get('code','')}｜{p.get('name','')}**")
                st.caption(f"{p.get('name_en','')} · {p.get('saved_at','')}")
                st.write(p.get("positioning",""))
                st.write("材料：" + "、".join(p.get("materials",[])))
                st.write("应用：" + "、".join(p.get("applications",[])))
        st.download_button("导出产品库 JSON", json.dumps(products,ensure_ascii=False,indent=2), "TrendRibbon_Product_Library.json", "application/json")

elif page == "历史记录":
    st.subheader("历史生成记录")
    if not history:
        st.info("暂无历史记录。")
    else:
        for item in history[::-1]:
            with st.expander(f"{item.get('created_at','')}｜{item.get('mode','')}｜{item.get('title','')}"):
                st.write(item.get("result",{}).get("summary",""))
                st.json(item.get("result",{}), expanded=False)
                st.download_button("下载记录", json.dumps(item,ensure_ascii=False,indent=2),
                                   file_name=f"TrendRibbon_{item.get('id','record')}.json",
                                   key=f"hist_{item.get('id')}")

elif page == "知识库":
    st.subheader("工艺知识库")
    st.write("上传工厂工艺说明、产品目录、材料资料或历史开发文档。当前版本使用本地关键词检索，适合 MVP 验证；后续可升级向量检索。")
    files = st.file_uploader("上传资料（TXT / MD / PDF / DOCX / CSV / JSON）", type=["txt","md","pdf","docx","csv","json"], accept_multiple_files=True)
    if files and st.button("导入知识库", type="primary"):
        current = load_json(KNOWLEDGE_INDEX, [])
        added = 0
        for f in files:
            raw = f.getvalue()
            text = extract_text(f.name, raw)
            if not text.strip():
                continue
            digest = hashlib.sha256(raw).hexdigest()
            if any(x.get("hash")==digest for x in current):
                continue
            safe_name = re.sub(r"[^A-Za-z0-9._\-\u4e00-\u9fff]", "_", f.name)
            (KNOWLEDGE_DIR / f"{digest[:10]}_{safe_name}").write_bytes(raw)
            current.append({"id":digest[:12],"hash":digest,"name":f.name,"text":text,"imported_at":datetime.now().isoformat(timespec="minutes")})
            added += 1
        save_json(KNOWLEDGE_INDEX, current)
        st.success(f"成功导入 {added} 份资料。")
        st.rerun()
    st.markdown(f"### 已收录资料（{len(knowledge)}）")
    for d in knowledge:
        with st.expander(f"{d.get('name')} · {d.get('imported_at','')}"):
            st.write(d.get("text","")[:1800] or "无可检索文本")
            if st.button("删除此资料", key=f"del_{d.get('id')}"):
                updated = [x for x in knowledge if x.get("id") != d.get("id")]
                save_json(KNOWLEDGE_INDEX, updated)
                st.rerun()

elif page == "设置":
    st.subheader("模型设置")
    cfg = load_json(DATA_DIR/"settings.json", {})
    with st.form("settings"):
        api_key = st.text_input("API Key", value=cfg.get("api_key",""), type="password", help="保存在本机 data/settings.json，不会上传到 TrendRibbon。")
        base_url = st.text_input("API Base URL", value=cfg.get("base_url","https://api.openai.com/v1"))
        model = st.text_input("模型名称", value=cfg.get("model","gpt-4o-mini"))
        submitted = st.form_submit_button("保存设置", type="primary")
        if submitted:
            save_json(DATA_DIR/"settings.json", {"api_key":api_key,"base_url":base_url,"model":model})
            st.success("设置已保存。")
    st.markdown("### 当前版本说明")
    st.markdown("""
- 演示模式：不配置 API Key 即可运行，使用内置示例生成逻辑。
- AI 模式：兼容 OpenAI Chat Completions 格式的 API 服务。
- 图片：当前生成英文静物效果图 Prompt；真正生成图片需另接图像生成 API。
- 知识库：本地文件保存与关键词检索；尚未启用向量数据库。
- 数据：本地 JSON 文件保存，不适合多人并发或生产环境。
""")
    st.info("正式商用前建议增加账号体系、租户隔离、云端数据库、权限控制、审计日志、向量检索与备份。")

st.divider()
st.caption("TrendRibbon MVP · Local-first prototype · AI concepts require factory validation")
