import streamlit as st
import math
from datetime import datetime

# Configuração da Interface
st.set_page_config(page_title="Pelican Pro - Calculadora", page_icon="🛸", layout="wide")

def main():
    st.title("🛸 Dose certa: Gestão de Calda")
    st.markdown("---")

    # --- SIDEBAR: CONFIGURAÇÕES DE HARDWARE E ÁREA ---
    with st.sidebar:
        st.header("⚙️ Configurações")
        area_total = st.number_input("Área do Talhão (ha)", min_value=0.1, value=50.0, step=1.0)
        vazao_plan = st.number_input("Vazão Planejada (L/ha)", min_value=1.0, value=10.0, step=0.5)
        
        st.divider()
        cap_pulv = st.number_input("Capacidade Pulverizador (L)", min_value=1, value=275)
        cap_mist = st.number_input("Capacidade Misturador (L)", min_value=1, value=1000)
        
        st.divider()
        modo_pronto_uso = st.toggle("MODO PRONTO USO (Sem Água)", value=False)
        st.info("No modo Pronto Uso, a vazão real será a soma das doses dos produtos.")

    # --- CORPO DO APP: ADIÇÃO DE PRODUTOS ---
    if 'produtos' not in st.session_state:
        st.session_state.produtos = []

    st.subheader("🧪 Composição da Mistura")
    
    # Form para adicionar produtos de uma vez
    with st.form("add_produto", clear_on_submit=True):
        col1, col2, col3 = st.columns([3, 2, 1])
        nome_p = col1.text_input("Nome do Defensivo/Adjuvante")
        dose_p = col2.number_input("Dose (L ou kg / ha)", min_value=0.0, step=0.001, format="%.3f")
        add_btn = col3.form_submit_button("Adicionar")
        
        if add_btn and nome_p:
            st.session_state.produtos.append({"nome": nome_p, "dose": dose_p})

    # Listagem de Produtos com opção de remover
    if st.session_state.produtos:
        st.write("**Lista de Produtos:**")
        for i, p in enumerate(st.session_state.produtos):
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.text(f"• {p['nome']}")
            c2.text(f"{p['dose']:.3f} L-kg/ha")
            if c3.button("Remover", key=f"del_{i}", type="secondary"):
                st.session_state.produtos.pop(i)
                st.rerun()
    else:
        st.warning("Nenhum produto adicionado à calda.")

    if st.button("Limpar Tudo", type="secondary"):
        st.session_state.produtos = []
        st.rerun()

    st.divider()

    # --- PROCESSAMENTO E RELATÓRIO ---
    if st.button("📊 GERAR RELATÓRIO DE MISTURA", type="primary", use_container_width=True):
        if not st.session_state.produtos:
            st.error("Adicione produtos para realizar o cálculo.")
            return

        # 1. Lógica de Cargas Fechadas
        cargas_por_batida = math.floor(cap_mist / cap_pulv)
        vol_util_mist = cargas_por_batida * cap_pulv
        
        # 2. Definição da Vazão
        soma_doses = sum(p['dose'] for p in st.session_state.produtos)
        vazao_final = soma_doses if modo_pronto_uso else vazao_plan
        
        if vazao_final == 0:
            st.error("Erro: Vazão não pode ser zero.")
            return

        ha_por_misturada = vol_util_mist / vazao_final

        # 3. Montagem do Relatório
        rel = []
        rel.append(f"RELATÓRIO DE MISTURA - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        rel.append("MODO: " + ("PRONTO USO (100% PRODUTO)" if modo_pronto_uso else "DILUIÇÃO (PRODUTO + ÁGUA)"))
        rel.append("="*45)
        rel.append(f"TALHÃO: {area_total:.2f} ha")
        rel.append(f"VAZÃO FINAL: {vazao_final:.2f} L/ha")
        rel.append(f"MISTURADOR: {cap_mist}L total (Usando {vol_util_mist}L)")
        rel.append(f"PULVERIZADOR: {cap_pulv}L por carga")
        rel.append(f"LOGÍSTICA: {cargas_por_batida} cargas por batida do misturador")
        rel.append("-" * 45)

        # Seção Misturador
        rel.append(f"PARA O MISTURADOR ({vol_util_mist}L TOTAL):")
        vol_prod_mist = 0
        for p in st.session_state.produtos:
            d_mist = (p['dose'] / vazao_final) * vol_util_mist
            vol_prod_mist += d_mist
            rel.append(f" > {p['nome']:<18}: {d_mist:>8.3f} L-kg")
        
        if not modo_pronto_uso:
            agua_mist = vol_util_mist - vol_prod_mist
            rel.append(f" > ÁGUA P/ COMPLETAR: {max(0.0, agua_mist):>8.2f} L")
        else:
            rel.append(" > ÁGUA ADICIONADA:      0.00 L (PRONTO USO)")

        rel.append("-" * 45)

        # Seção Tanque Individual
        rel.append(f"POR CARGA DO PULVERIZADOR ({cap_pulv}L):")
        vol_prod_pulv = 0
        for p in st.session_state.produtos:
            d_pulv = (p['dose'] / vazao_final) * cap_pulv
            vol_prod_pulv += d_pulv
            rel.append(f" > {p['nome']:<18}: {d_pulv:>8.3f} L-kg")
        
        if not modo_pronto_uso:
            agua_pulv = cap_pulv - vol_prod_pulv
            rel.append(f" > ÁGUA P/ COMPLETAR: {max(0.0, agua_pulv):>8.2f} L")

        rel.append("-" * 45)
        
        # Seção Estoque/Talhão
        rel.append("NECESSIDADE TOTAL (ESTOQUE):")
        for p in st.session_state.produtos:
            total_est = p['dose'] * area_total
            rel.append(f" > {p['nome']:<18}: {total_est:>8.2f} L-kg")
        
        rel.append("-" * 45)
        rel.append(f"Rendimento Misturador: {ha_por_misturada:.2f} ha / batida")
        rel.append(f"Misturas Totais:    {math.ceil(area_total / ha_por_misturada)}")

        # Exibição
        final_text = "\n".join(rel)
        st.code(final_text, language="text")

        # Botão de Download
        st.download_button(
            label="💾 Salvar Relatório (.txt)",
            data=final_text,
            file_name=f"calda_{datetime.now().strftime('%d_%m_%H%M')}.txt",
            mime="text/plain"
        )

if __name__ == "__main__":
    main()
