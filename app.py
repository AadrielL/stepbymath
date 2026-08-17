import streamlit as st
from google import genai
from google.genai import errors
import plotly.graph_objects as go
import numpy as np
from prompt import SYSTEM_INSTRUCTION

# Configuração da página do Streamlit
st.set_page_config(page_title="StepByMath", page_icon="🧮", layout="centered")

st.title("🧮 StepByMath")
st.markdown("Seu tutor interativo de Cálculo 1. Resolva problemas passo a passo!")

# ==========================================
# 1. INICIALIZAÇÃO DE ESTADOS NA SESSÃO
# ==========================================
if "user_api_key" not in st.session_state:
    st.session_state.user_api_key = ""

if "exercicio_concluido" not in st.session_state:
    st.session_state.exercicio_concluido = False

if "mostrar_grafico" not in st.session_state:
    st.session_state.mostrar_grafico = False

# ==========================================
# 2. BARRA LATERAL (Chave API)
# ==========================================
with st.sidebar:
    st.header("⚙️ Configuração")
    st.markdown("Para usar o StepByMath, você precisa de uma chave gratuita da API do Gemini.")
    st.markdown("[👉 Pegue sua chave aqui](https://aistudio.google.com/app/apikey)")
    
    if st.session_state.user_api_key == "":
        chave_input = st.text_input("Cole sua Chave API aqui:", type="password")
        
        if st.button("💾 Salvar Chave"):
            if chave_input:
                st.session_state.user_api_key = chave_input
                for key in ["gemini_client", "chat_session", "exercicio_concluido", "mostrar_grafico"]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
            else:
                st.error("Por favor, cole a chave antes de salvar.")
    else:
        st.success("✅ Chave configurada com sucesso!")
        
        if st.button("🗑️ Limpar Chave / Sair"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.markdown("---")
    st.markdown("💡 **Privacidade:** Sua chave fica apenas na memória do seu navegador.")

if not st.session_state.user_api_key:
    st.warning("👈 Por favor, insira e salve sua chave da API do Gemini na barra lateral para começar.")
    st.stop()

# ==========================================
# 3. INICIALIZAÇÃO DO CLIENTE E CHAT
# ==========================================
if "gemini_client" not in st.session_state or "chat_session" not in st.session_state:
    try:
        client = genai.Client(api_key=st.session_state.user_api_key)
        st.session_state.gemini_client = client
        st.session_state.chat_session = client.chats.create(
            model="gemini-3.6-flash",
            config={"system_instruction": SYSTEM_INSTRUCTION}
        )
    except Exception as e:
        st.error(f"❌ Falha ao conectar com o Gemini: {e}")
        st.stop()

# ==========================================
# 4. RENDERIZAÇÃO DO HISTÓRICO
# ==========================================
try:
    history = st.session_state.chat_session.get_history()
    for message in history:
        role = "assistant" if message.role == "model" else "user"
        with st.chat_message(role):
            if message.parts and len(message.parts) > 0:
                st.markdown(message.parts[0].text)
except Exception as e:
    st.error(f"Erro ao carregar histórico: {e}")

# ==========================================
# 5. ENTRADA DE MENSAGEM E INTERATIVIDADE
# ==========================================
user_input = st.chat_input("Digite sua função ou o que deseja treinar...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
        
    with st.chat_message("assistant"):
        with st.spinner("Analisando o problema..."):
            try:
                response = st.session_state.chat_session.send_message(user_input)
                resposta_texto = response.text
                st.markdown(resposta_texto)
                
                # Detecta se o exercício terminou (contém + C ou termos de conclusão)
                if "+ C" in resposta_texto or "constante" in resposta_texto.lower() or "perfeito" in resposta_texto.lower():
                    st.session_state.exercicio_concluido = True
                    st.rerun()
                            
            except errors.APIError as e:
                st.error(f"⚠️ Erro da API: {e}")
            except Exception as e:
                st.error(f"⚠️ Erro técnico: {e}")

# ==========================================
# 6. PAINEL DE CONCLUSÃO E GRÁFICO DINÂMICO
# ==========================================
if st.session_state.exercicio_concluido:
    st.markdown("---")
    st.success("🎉 Exercício concluído com sucesso!")
    
    # Bloco de Resumo Organizado
    with st.expander("📌 Ver Resumo Completo da Solução"):
        st.markdown("Aqui está a consolidação de todos os passos resolvidos nesta sessão:")
        for msg in st.session_state.chat_session.get_history():
            if msg.role == "model" and msg.parts:
                st.markdown(f"- {msg.parts[0].text[:140]}...")

    # Botões de Ação Dinâmica
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Gerar Gráfico da Função", use_container_width=True):
            st.session_state.mostrar_grafico = True
            st.rerun()
            
    with col2:
        if st.button("🔄 Próximo Exercício", use_container_width=True):
            st.session_state.chat_session = st.session_state.gemini_client.chats.create(
                model="gemini-3.6-flash",
                config={"system_instruction": SYSTEM_INSTRUCTION}
            )
            st.session_state.exercicio_concluido = False
            st.session_state.mostrar_grafico = False
            st.rerun()

# ==========================================
# 7. RENDERIZAÇÃO DO GRÁFICO DINÂMICO (Plotly)
# ==========================================
if st.session_state.get("mostrar_grafico", False):
    st.markdown("---")
    st.subheader("📈 Visualização Gráfica Interativa")
    st.markdown("Gráfico gerado com base na função resolvida no exercício:")
    
    x = np.linspace(-3, 3, 400)
    
    expressao_escolhida = st.selectbox(
        "Selecione a função correspondente ao exercício atual:",
        [
            "x³ (Exercício atual: ∫x³ dx)", 
            "3x² + 4x - 5 (Exemplo anterior)", 
            "x² - 4x + 3", 
            "2x + 3"
        ]
    )
    
    if "x³" in expressao_escolhida:
        y_func = x**3
        y_prim = (x**4) / 4
        nome_func = "f(x) = x³"
        nome_prim = "F(x) = (x⁴/4)"
    elif "3x² + 4x - 5" in expressao_escolhida:
        y_func = 3*(x**2) + 4*x - 5
        y_prim = (x**3) + 2*(x**2) - 5*x
        nome_func = "f(x) = 3x² + 4x - 5"
        nome_prim = "F(x) = x³ + 2x² - 5x"
    elif "x² - 4x + 3" in expressao_escolhida:
        y_func = (x**2) - 4*x + 3
        y_prim = (x**3)/3 - 2*(x**2) + 3*x
        nome_func = "f(x) = x² - 4x + 3"
        nome_prim = "F(x) = (1/3)x³ - 2x² + 3x"
    else:
        y_func = 2*x + 3
        y_prim = (x**2) + 3*x
        nome_func = "f(x) = 2x + 3"
        nome_prim = "F(x) = x² + 3x"

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y_func, name=nome_func, line=dict(color="blue", width=2)))
    fig.add_trace(go.Scatter(x=x, y=y_prim, name=f"{nome_prim} (Primitiva)", line=dict(color="orange", width=2, dash="dash")))
    
    fig.update_layout(
        xaxis_title="Eixo X",
        yaxis_title="Eixo Y",
        template="plotly_dark",
        margin=dict(l=20, r=20, t=20, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)