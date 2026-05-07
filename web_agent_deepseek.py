import streamlit as st
import requests
import json
from datetime import datetime, timedelta

# ======================
# 你的 DeepSeek API Key
# ======================
API_KEY = "sk-00bd4a739b734079adf795a752d65a4d"
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

# ======================
# 企业业务知识库
# ======================
COMPANY_BUSINESS = """
我们公司是名诚印务制本有限公司，专业做印务制本一站式服务，主营：
1. 各类画册、宣传册、企业样本册、产品手册、楼书
2. 精装书、平装书刊、笔记本、记事本、定制本册
3. 包装盒、礼品盒、手提袋、档案盒、封套
4. 宣传单页、折页、海报、不干胶标签、贴纸
5. 教材教辅、会议资料、培训手册、杂志书刊
支持设计排版、印刷、装订、送货一站式服务。
"""

# ======================
# 报价 + 工期计算工具
# ======================
def calculate_price_and_time(product_type, size, quantity, page_num, paper_type, has_complex_craft):
    base_unit_price = 0.6
    if "精装" in product_type:
        base_unit_price = 1.8
    elif "画册" in product_type:
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

    return (
        f"📋 印刷定制报价 & 交期预估\n"
        f"产品类型：{product_type}\n"
        f"成品尺寸：{size}\n"
        f"定制数量：{quantity}本\n"
        f"内页页数：{page_num}P\n"
        f"用纸材质：{paper_type}\n"
        f"特殊工艺：{'有' if has_complex_craft else '无'}\n"
        f"——————————————\n"
        f"预估单价：{unit_price} 元/本\n"
        f"预估总价：{total_price} 元左右\n"
        f"生产工期：约 {work_days} 个工作日\n"
        f"预计交付：{deliver_date}"
    )

# ======================
# DeepSeek 调用函数
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
# 系统提示词
# ======================
SYSTEM_PROMPT = f"""
你是一家专业印务制本公司的智能客服。
你的任务：
1. 客户问业务 → 介绍：{COMPANY_BUSINESS}
2. 客户问报价/交期 → 必须收集6项信息：
   - 产品类型、尺寸、数量、页数、纸张、是否有复杂工艺
3. 信息不全 → 礼貌追问
4. 信息齐全 → 直接输出报价结果
语气不专业、暴躁、简短。
"""

# ======================
# 网页界面
# ======================
st.set_page_config(page_title="印务制本智能客服", layout="wide")
st.title("📖 印务制本企业 - 智能客服 AI Agent")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

user_input = st.chat_input("请输入您的问题...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # AI 回复
    reply = deepseek_chat(st.session_state.messages)

    # 自动判断是否需要计算报价
    if "产品类型" in reply and "数量" in reply and "页数" in reply:
        try:
            # 这里简化：如果AI回复里包含参数，自动触发报价计算
            # 实际可通过函数调用增强
            reply = calculate_price_and_time(
                product_type="画册",
                size="A4",
                quantity=500,
                page_num=40,
                paper_type="铜版纸",
                has_complex_craft=False
            )
        except:
            pass

    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)