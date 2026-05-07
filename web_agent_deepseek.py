import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta
import pandas as pd
import PyPDF2
from PIL import Image
import pytesseract

# ======================
# 配置
# ======================
API_KEY = "sk-00bd4a739b734079adf795a752d65a4d"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
# 知识库文件夹路径
KNOWLEDGE_DIR = os.path.join(os.getcwd(), "knowledge")

# ======================
# 企业完整信息
# ======================
COMPANY_INFO = """
公司名称：绍兴市名诚印务制本有限公司
地址：浙江省绍兴市越城区镜湖路
成立时间：2003年08月18日
注册资本：150.00万人民币
经营范围：
1. 包装装潢、其他印刷品印刷
2. 本册加工
3. 批发、零售：纸制品、塑料制品、工艺礼品（除金饰品）、邮品（除普通邮票）、布

主营产品：
1. 各类画册、宣传册、企业样本册、产品手册、楼书
2. 精装书、平装书刊、笔记本、记事本、定制本册
3. 包装盒、礼品盒、手提袋、档案盒、封套
4. 宣传单页、折页、海报、不干胶标签、贴纸
5. 教材教辅、会议资料、培训手册、杂志书刊

服务：设计排版、印刷、装订、送货一站式服务。
订购联系电话：13605755944（吴先生）
"""

# ======================
# 报价 + 工期计算
# ======================
def calculate_price_and_time(product_type, size, quantity, page_num, paper_type, has_complex_craft):
    base_unit_price = 0.6
    if "精装" in product_type:
        base_unit_price = 1.8
    elif "画册" in product_type or "宣传册" in product_type:
        base_unit_price = 0.8
    elif "笔记本" in product_type:
        base_unit_price = 0.7

    if paper_type == "特种纸":
        base_unit_price *= 1.5
    if has_complex_craft:
        base_unit_price *= 1.3

    unit_price = round(base_unit_price * (page_num / 20), 2)
    total_price = round(unit_price * quantity, 2)

    if quantity <= 100:
        work_days = 3
    elif quantity <= 1000:
        work_days = 6
    else:
        work_days = 10
    if has_complex_craft:
        work_days += 3

    deliver_date = (datetime.now() + timedelta(days=work_days)).strftime("%Y-%m-%d")

    return f"""
📋 印刷定制报价 & 交期预估
产品类型：{product_type}
成品尺寸：{size}
定制数量：{quantity}本
内页页数：{page_num}P
用纸材质：{paper_type}
特殊工艺：{'有' if has_complex_craft else '无'}
——————————————
预估单价：{unit_price} 元/本
预估总价：{total_price} 元左右
生产工期：约 {work_days} 个工作日
预计交付：{deliver_date}
"""

# ======================
# 单文件文本提取
# ======================
def extract_text_from_file(file_path):
    text = ""
    try:
        if file_path.lower().endswith(".pdf"):
            reader = PyPDF2.PdfReader(file_path)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        elif file_path.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_path)
            text = df.to_string()
        elif file_path.lower().endswith((".png", ".jpg", ".jpeg")):
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img, lang="chi_sim")
        elif file_path.lower().endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
    except Exception as e:
        text = f"文件解析失败：{str(e)}"
    return text.strip()

# ======================
# 批量加载整个知识库文件夹
# ======================
def load_all_knowledge():
    all_text = "【公司内部知识库资料】\n"
    if not os.path.exists(KNOWLEDGE_DIR):
        os.makedirs(KNOWLEDGE_DIR)
        return all_text
    for fname in os.listdir(KNOWLEDGE_DIR):
        fpath = os.path.join(KNOWLEDGE_DIR, fname)
        if os.path.isfile(fpath):
            all_text += f"\n===== 文件：{fname} =====\n"
            all_text += extract_text_from_file(fpath)
    return all_text

# ======================
# DeepSeek 对话
# ======================
def deepseek_chat(messages):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.2
    }
    response = requests.post(DEEPSEEK_URL, headers=headers, json=data)
    res = response.json()
    return res["choices"][0]["message"]["content"]

# ======================
# 加载全局知识库
# ======================
knowledge_content = load_all_knowledge()

# ======================
# 系统提示词（内置知识库+公司信息）
# ======================
SYSTEM_PROMPT = f"""
你是绍兴市名诚印务制本有限公司的专业智能客服。
联系电话：13605755944（对外只称呼吴先生，不透露全名）

【公司基础信息】
{COMPANY_INFO}

【内部知识库资料】
{knowledge_content}

严格遵守规则：
1. 回答客户问题优先参考公司信息 + 内部知识库
2. 客户问报价、价格、工期：必须收集6项信息：产品类型、成品尺寸、定制数量、内页页数、纸张类型、是否有复杂工艺
3. 信息不全礼貌追问，信息齐全自动给出标准报价单
4. 禁止编造不存在的价格、业务信息
5. 语气专业、简洁、接地气，适合印刷行业客服口吻
"""

# ======================
# 前台聊天界面（无任何文件上传）
# ======================
st.set_page_config(page_title="名诚印务智能客服", layout="wide")
st.title("📖 绍兴市名诚印务制本有限公司 - AI智能客服")

# 初始化对话
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# 展示历史对话
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# 用户聊天输入
user_input = st.chat_input("请输入您的咨询问题...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    ai_reply = deepseek_chat(st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
    with st.chat_message("assistant"):
        st.markdown(ai_reply)
