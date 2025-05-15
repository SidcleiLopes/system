import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd


st.set_page_config(
    page_title="Sistema Restaurante",
    page_icon="🍽️",
    layout="wide"
)
# ⚠️ Pegando as credenciais do secrets.toml
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(url, key)

def verificar_login(login, senha):
    response = supabase.table("usuarios").select("*").eq("login", login).eq("senha", senha).execute()
    data = response.data
    if data:
        return data[0]["tipo"]
    return None

def tela_login():
    st.title("Login")

    login = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        tipo_usuario = verificar_login(login, senha)
        if tipo_usuario:
            st.session_state["usuario"] = login
            st.session_state["tipo"] = tipo_usuario
            st.success(f"Bem-vindo, {login}!")
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")


def tela_admin():
    st.title("Painel do Administrador")

    # Menu lateral de navegação
    menu = st.sidebar.selectbox("🔧 Selecione uma área", [
        "📊 Relatórios",
        "🍽️ Gerenciar Pratos",
        "👥 Clientes & Pedidos"
    ])

    # 📊 RELATÓRIOS
    if menu == "📊 Relatórios":
        st.subheader("📈 Relatórios de Pedidos")

        pedidos = supabase.table("pedidos").select("*").execute().data

        if not pedidos:
            st.info("Nenhum pedido registrado ainda.")
            return

        df = pd.DataFrame(pedidos)
        df["criado_em"] = pd.to_datetime(df["criado_em"])
        df["data"] = df["criado_em"].dt.date

        # 🎯 Filtro por período
        data_min = df["data"].min()
        data_max = df["data"].max()

        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("De", value=data_min, min_value=data_min, max_value=data_max)
        with col2:
            data_fim = st.date_input("Até", value=data_max, min_value=data_min, max_value=data_max)

        df_periodo = df[(df["data"] >= data_inicio) & (df["data"] <= data_fim)]

        if df_periodo.empty:
            st.warning("Nenhum pedido no período selecionado.")
            return

        # 🔷 Gift cards
        prato_mais_pedido = (
            df_periodo["descricao"].value_counts().idxmax()
            if not df_periodo.empty else "N/A"
        )
        total_vendas = df_periodo["valor"].sum()
        total_pedidos = len(df_periodo)
        
        col1, col2, col3 = st.columns(3)

        col1.markdown(f"""
        <div style="background-color: #1E1E1E; padding: 16px; border-radius: 10px; text-align: center; color: white;">
            <h4>🏆 Prato Mais Pedido</h4>
            <p style="font-size: 16px;">{prato_mais_pedido}</p>
        </div>
        """, unsafe_allow_html=True)

        col2.markdown(f"""
        <div style="background-color: #1E1E1E; padding: 16px; border-radius: 10px; text-align: center; color: white;">
            <h4>💰 Vendas Totais (R$)</h4>
            <p style="font-size: 20px;">{total_vendas:.2f}</p>
        </div>
        """, unsafe_allow_html=True)

        col3.markdown(f"""
        <div style="background-color: #1E1E1E; padding: 16px; border-radius: 10px; text-align: center; color: white;">
            <h4>🍽️ Qtde de Pedidos</h4>
            <p style="font-size: 20px;">{total_pedidos}</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # 📊 Quantidade por tipo
        qtd_por_tipo = df_periodo["tipo"].value_counts().reset_index()
        qtd_por_tipo.columns = ["Tipo", "Quantidade"]
        st.subheader("📦 Quantidade por Tipo de Prato")
        st.bar_chart(qtd_por_tipo.set_index("Tipo"))

        # 📊 Total por tipo
        total_por_tipo = df_periodo.groupby("tipo")["valor"].sum().reset_index()
        total_por_tipo.columns = ["Tipo", "Total R$"]
        st.subheader("💸 Valor Total por Tipo de Prato")
        st.bar_chart(total_por_tipo.set_index("Tipo"))

        st.divider()
        st.subheader("📋 Pedidos Detalhados")
        st.dataframe(df_periodo[["cliente", "tipo", "descricao", "valor", "status", "criado_em"]])

    # 🍽️ GERENCIAR PRATOS
    elif menu == "🍽️ Gerenciar Pratos":
        st.subheader("🍽️ Cadastro e Edição de Pratos")

        pratos = supabase.table("pratos").select("*").execute().data

        with st.expander("➕ Cadastrar novo prato"):
            with st.form("form_cadastro_prato"):
                nome_novo = st.text_input("Nome do prato")
                tipo_novo = st.selectbox("Tipo", ["Marmita", "Prato Feito", "Kilo"])
                preco_novo = st.number_input("Preço (R$)", min_value=0.0, format="%.2f", step=0.5)

                submit = st.form_submit_button("Cadastrar")
                if submit:
                    if nome_novo.strip():
                        supabase.table("pratos").insert({
                            "nome": nome_novo.strip(),
                            "tipo": tipo_novo.lower(),
                            "preco": preco_novo
                        }).execute()
                        st.success("Prato cadastrado com sucesso!")
                        st.experimental_rerun()
                    else:
                        st.warning("Informe o nome do prato.")

        st.divider()
        st.subheader("📋 Pratos cadastrados")

        for prato in pratos:
            with st.expander(f"{prato['nome']} - R$ {prato['preco']:.2f}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    novo_nome = st.text_input("Editar nome", value=prato["nome"], key=f"nome_{prato['id']}")
                with col2:
                    novo_preco = st.number_input("Editar preço", value=prato["preco"], format="%.2f", key=f"preco_{prato['id']}")
                with col3:
                    novo_tipo = st.selectbox("Editar tipo", ["marmita", "prato feito", "kilo"], 
                                             index=["marmita", "prato feito", "kilo"].index(prato["tipo"]), 
                                             key=f"tipo_{prato['id']}")

                if st.button("💾 Salvar alterações", key=f"salvar_{prato['id']}"):
                    supabase.table("pratos").update({
                        "nome": novo_nome.strip(),
                        "preco": novo_preco,
                        "tipo": novo_tipo
                    }).eq("id", prato["id"]).execute()
                    st.success("Prato atualizado!")
                    st.experimental_rerun()

                if st.button("🗑️ Excluir prato", key=f"excluir_{prato['id']}"):
                    supabase.table("pratos").delete().eq("id", prato["id"]).execute()
                    st.warning("Prato excluído.")
                    st.experimental_rerun()

    # 👥 CLIENTES E PEDIDOS
    elif menu == "👥 Clientes & Pedidos":
        st.subheader("👥 Pedidos por Cliente")

        pedidos = supabase.table("pedidos").select("*").order("criado_em", desc=True).execute().data

        if pedidos:
            df = pd.DataFrame(pedidos)
            st.dataframe(df[["cliente", "tipo", "descricao", "valor", "status", "criado_em"]])
        else:
            st.info("Nenhum pedido registrado.")


def tela_balcao():
    st.title("Área do Balcão")
    st.subheader("Novo Pedido")

    # Nome do cliente
    nome_cliente = st.text_input("Nome do Cliente")

    # Tipo de pedido
    tipo_pedido = st.selectbox("Tipo de Pedido", ["Marmita", "Kilo", "Prato Feito"])

    # Buscar pratos do banco por tipo
    pratos_db = supabase.table("pratos").select("*").eq("tipo", tipo_pedido.lower()).execute().data

    if not pratos_db:
        st.warning("Nenhum prato cadastrado para este tipo.")
        return

    # Criar lista de nomes dos pratos e dicionário com preços
    nomes_pratos = [prato["nome"] for prato in pratos_db]
    precos_pratos = {prato["nome"]: prato["preco"] for prato in pratos_db}

    # Seleção de prato e obtenção de valor
    prato_escolhido = st.selectbox("Prato", nomes_pratos)
    valor = precos_pratos.get(prato_escolhido, 0.0)
    st.info(f"💲 Valor automático: R$ {valor:.2f}")

    # Restante das opções do pedido
    tipo_feijao = st.radio("Tipo de Feijão", ["De Caldo", "Tropeiro", "Tutu"])
    exceto = st.multiselect("Excluir ingredientes", ["Tomate", "Cebola", "Feijão", "Alface", "Batata"])
    descricao = st.text_area("Observações (opcional)")

    if st.button("Enviar Pedido"):
        if not nome_cliente.strip():
            st.warning("Por favor, insira o nome do cliente.")
            return

        # Montar descrição
        texto_descricao = f"Prato: {prato_escolhido} | Feijão: {tipo_feijao}"
        if exceto:
            texto_descricao += f" | Exceto: {', '.join(exceto)}"
        if descricao:
            texto_descricao += f" | Obs: {descricao}"

        # Criar dicionário de pedido
        pedido = {
            "tipo": tipo_pedido.lower(),
            "descricao": texto_descricao,
            "status": "pendente",
            "cliente": nome_cliente.strip(),
            "valor": valor,
            "criado_por": st.session_state["usuario"],
            "criado_em": datetime.datetime.now().isoformat()
        }

        # Enviar para o Supabase
        supabase.table("pedidos").insert(pedido).execute()
        st.success(f"✅ Pedido para {nome_cliente} enviado para a cozinha!")


def tela_cozinha():
    st.title("Área da Cozinha")
    st.subheader("Pedidos em Aberto")

    # Buscar pedidos com status pendente ou em preparo
    response = supabase.table("pedidos") \
        .select("*") \
        .in_("status", ["pendente", "em preparo"]) \
        .order("criado_em", desc=False) \
        .execute()
    pedidos = response.data

    if not pedidos:
        st.info("Nenhum pedido pendente ou em preparo no momento.")
        return

    for pedido in pedidos:
        with st.container():
            st.markdown("---")
            st.markdown(f"**Cliente:** {pedido['cliente']}")
            st.markdown(f"**Tipo:** {pedido['tipo'].capitalize()}")
            st.markdown(f"**Descrição:** {pedido['descricao']}")
            st.markdown(f"**Status Atual:** `{pedido['status'].upper()}`")
            st.markdown(f"**Criado por:** {pedido['criado_por']} às {pedido['criado_em'][:16].replace('T', ' ')}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Marcar como Em Preparo", key=f"prep_{pedido['id']}"):
                    supabase.table("pedidos").update({"status": "em preparo"}).eq("id", pedido["id"]).execute()
                    st.rerun()

            with col2:
                if st.button("Marcar como Pronto", key=f"pronto_{pedido['id']}"):
                    supabase.table("pedidos").update({"status": "pronto"}).eq("id", pedido["id"]).execute()
                    st.rerun()

def main():

    if "usuario" not in st.session_state:
        tela_login()
    else:
        tipo = st.session_state["tipo"]

        if tipo == "admin":
            tela_admin()
        elif tipo == "balcao":
            tela_balcao()
        elif tipo == "cozinha":
            tela_cozinha()
        else:
            st.error("Tipo de usuário inválido.")

        st.sidebar.markdown("---")
        if st.sidebar.button("Sair"):
            st.session_state.clear()
            st.rerun()

if __name__ == "__main__":
    main()
