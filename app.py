import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import uuid

from dados import FISCAIS_CONTRATOS

# ------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# ------------------------------------------------------------------
st.set_page_config(page_title="Atualização Semanal - Contratos", page_icon="🛣️", layout="centered")

NOME_DA_PLANILHA = "Atualização Semanal - Contratos"  # nome exato da planilha no Google Drive
NOME_DA_ABA = "Respostas"  # nome da aba dentro da planilha onde as linhas serão gravadas

CABECALHO = [
    "Data/Hora",
    "Fiscal",
    "Aba de Origem",
    "Contrato",
    "Valor investido",
    "Extensão Executada (Km)",
    "Quantidade de Ruas Executadas",
    "Observações",
]

SEM_ATUALIZACAO = "Não há atualização"


# ------------------------------------------------------------------
# CONEXÃO COM O GOOGLE SHEETS
# ------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def conectar_planilha():
    escopos = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credenciais = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=escopos
    )
    cliente = gspread.authorize(credenciais)
    planilha = cliente.open(NOME_DA_PLANILHA)

    try:
        aba = planilha.worksheet(NOME_DA_ABA)
    except gspread.WorksheetNotFound:
        aba = planilha.add_worksheet(title=NOME_DA_ABA, rows=1000, cols=len(CABECALHO))

    if aba.row_values(1) != CABECALHO:
        aba.update("A1", [CABECALHO])

    return aba


def enviar_linhas(linhas):
    aba = conectar_planilha()
    aba.append_rows(linhas, value_input_option="USER_ENTERED")


# ------------------------------------------------------------------
# ESTADO DA SESSÃO
# ------------------------------------------------------------------
if "blocos" not in st.session_state:
    # cada bloco = um contrato preenchido nesta sessão
    st.session_state.blocos = [str(uuid.uuid4())]

if "enviado" not in st.session_state:
    st.session_state.enviado = False


def adicionar_bloco():
    st.session_state.blocos.append(str(uuid.uuid4()))


def remover_bloco(bloco_id):
    st.session_state.blocos.remove(bloco_id)
    # limpa as chaves salvas desse bloco no session_state
    for chave in list(st.session_state.keys()):
        if chave.endswith(f"__{bloco_id}"):
            del st.session_state[chave]


# ------------------------------------------------------------------
# TELA DE SUCESSO
# ------------------------------------------------------------------
if st.session_state.enviado:
    st.success("✅ Atualização enviada com sucesso! Obrigado.")
    if st.button("Preencher nova atualização"):
        st.session_state.enviado = False
        st.session_state.blocos = [str(uuid.uuid4())]
        st.rerun()
    st.stop()


# ------------------------------------------------------------------
# FORMULÁRIO
# ------------------------------------------------------------------
st.title("🛣️ Atualização Semanal de Contratos")
st.caption("Preencha os dados de um ou mais contratos e envie tudo de uma vez.")

fiscal = st.selectbox(
    "Fiscal *",
    options=["Selecione..."] + sorted(FISCAIS_CONTRATOS.keys()),
)

if fiscal == "Selecione...":
    st.info("Selecione o seu nome para ver os contratos disponíveis.")
    st.stop()

contratos_do_fiscal = FISCAIS_CONTRATOS[fiscal]
opcoes_contrato = [c["contrato"] for c in contratos_do_fiscal] + [SEM_ATUALIZACAO]

st.divider()

respostas = []

for i, bloco_id in enumerate(st.session_state.blocos):
    with st.container(border=True):
        col_titulo, col_remover = st.columns([5, 1])
        with col_titulo:
            st.markdown(f"**Contrato #{i + 1}**")
        with col_remover:
            if len(st.session_state.blocos) > 1:
                st.button(
                    "🗑️",
                    key=f"remover__{bloco_id}",
                    on_click=remover_bloco,
                    args=(bloco_id,),
                    help="Remover este contrato",
                )

        contrato_selecionado = st.selectbox(
            "Contrato",
            options=opcoes_contrato,
            key=f"contrato__{bloco_id}",
        )

        sem_atualizacao = contrato_selecionado == SEM_ATUALIZACAO

        if sem_atualizacao:
            valor_executar = ""
            extensao_executada = ""
            qtd_ruas = ""
            observacoes = st.text_area(
                "Observações (opcional)",
                key=f"obs__{bloco_id}",
                placeholder="Informações sobre contratos ou pedidos para acrescentar contratos.",
            )
        else:
            col1, col2 = st.columns(2)
            with col1:
                valor_executar = st.number_input(
                    "Valor Investido (R$)",
                    min_value=0.0,
                    step=1000.0,
                    format="%.2f",
                    key=f"valor__{bloco_id}",
                )
            with col2:
                extensao_executada = st.number_input(
                    "Extensão Executada (Km)",
                    min_value=0.0,
                    step=0.1,
                    format="%.2f",
                    key=f"extensao__{bloco_id}",
                )

            qtd_ruas = st.number_input(
                "Quantidade de Ruas Executadas",
                min_value=0,
                step=1,
                key=f"ruas__{bloco_id}",
            )
            qtd_ruas = int(qtd_ruas)

            observacoes = st.text_area(
                "Observações",
                key=f"obs__{bloco_id}",
                placeholder="Alguma observação sobre o andamento do contrato...",
            )

        aba_origem = next(
            (c["aba"] for c in contratos_do_fiscal if c["contrato"] == contrato_selecionado),
            "",
        )

        respostas.append(
            [
                datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                fiscal,
                aba_origem,
                contrato_selecionado,
                valor_executar,
                extensao_executada,
                qtd_ruas,
                observacoes,
            ]
        )

st.button("➕ Adicionar outro contrato", on_click=adicionar_bloco)

st.divider()

if st.button("✅ Enviar tudo", type="primary", use_container_width=True):
    try:
        with st.spinner("Enviando..."):
            enviar_linhas(respostas)
        st.session_state.enviado = True
        st.rerun()
    except Exception as e:
        st.error(f"Ocorreu um erro ao enviar os dados: {e}")
        st.caption(
            "Confira se a planilha foi compartilhada com CTCPPT SETRAND "
            "Credenciais incorretas."
            "Entre em contato com David Alves"
        )
