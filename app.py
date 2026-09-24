import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from zoneinfo import ZoneInfo
import uuid

from dados import FISCAIS_CONTRATOS

FUSO_BR = ZoneInfo("America/Maceio")  

# CONFIGURAÇÃO DA PÁGINA
# ------------------------------------------------------------------
st.set_page_config(page_title="Atualização Semanal - Contratos", page_icon="🛣️", layout="centered")

NOME_DA_PLANILHA = "Atualização Semanal - Contratos"  
NOME_DA_ABA = "Respostas"  

CABECALHO = [
    "Data/Hora",
    "Fiscal",
    "Aba de Origem",
    "Contrato",
    "Cidade",
    "Situação da Obra",
    "Valor Executado",
    "Extensão Executada (Km)",
    "Quantidade de Ruas Executadas",
    "Observações",
]

SEM_ATUALIZACAO = "Não há atualização"
SITUACOES_OBRA = ["Selecione...", "Em Execução", "Não Iniciada", "Concluída", "Paralisada"]


def formatar_valor_brl(valor):
    """Converte um float em texto no formato XX.xxx.xxx,XX."""
    texto = f"{valor:,.2f}"  # ex: 150,000.00
    texto = texto.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    return texto



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


# ESTADO DA SESSÃO
# ------------------------------------------------------------------
if "blocos" not in st.session_state:
    st.session_state.blocos = [str(uuid.uuid4())]

if "enviado" not in st.session_state:
    st.session_state.enviado = False


def adicionar_bloco():
    st.session_state.blocos.append(str(uuid.uuid4()))


def remover_bloco(bloco_id):
    st.session_state.blocos.remove(bloco_id)
    for chave in list(st.session_state.keys()):
        if chave.endswith(f"__{bloco_id}"):
            del st.session_state[chave]


# TELA DE SUCESSO
# ------------------------------------------------------------------
if st.session_state.enviado:
    st.success("✅ Atualização enviada com sucesso! Obrigado.")
    if st.button("Preencher nova atualização"):
        st.session_state.enviado = False
        st.session_state.blocos = [str(uuid.uuid4())]
        st.rerun()
    st.stop()


 
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

        aba_origem = next(
            (c["aba"] for c in contratos_do_fiscal if c["contrato"] == contrato_selecionado),
            "",
        )

        cidade = st.text_input(
            "Cidade",
            key=f"cidade__{bloco_id}",
            placeholder="Ex: Maceió",
        )
        if aba_origem in ("MCL 03", "IMPLANTAÇÃO EM PARALELEPÍPEDO"):
            st.caption("⚠️ Informe a cidade")

        if sem_atualizacao:
            valor_executar = ""
            extensao_executada = ""
            qtd_ruas = ""
            situacao_obra = st.selectbox(
                "Situação da Obra",
                options=SITUACOES_OBRA,
                key=f"situacao__{bloco_id}",
            )
            observacoes = st.text_area(
                "Observações (opcional)",
                key=f"obs__{bloco_id}",
                placeholder="Pode explicar o motivo, se quiser. E caso queira informar sobre outros contratos" ,
            )
        else:
            col1, col2 = st.columns(2)
            with col1:
                valor_num = st.number_input(
                    "Valor Executado (R$)",
                    min_value=0.0,
                    step=1000.0,
                    format="%.2f",
                    key=f"valor__{bloco_id}",
                )
                st.caption("Valor executado na semana")
                valor_executar = formatar_valor_brl(valor_num)
                st.caption(f"R$ {valor_executar}")
            with col2:
                extensao_executada = st.number_input(
                    "Extensão Executada (Km)",
                    min_value=0.0,
                    step=0.1,
                    format="%.2f",
                    key=f"extensao__{bloco_id}",
                )

            situacao_obra = st.selectbox(
                "Situação da Obra",
                options=SITUACOES_OBRA,
                key=f"situacao__{bloco_id}",
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

        respostas.append(
            [
                datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M:%S"),
                fiscal,
                aba_origem,
                contrato_selecionado,
                cidade.strip(),
                situacao_obra if situacao_obra != "Selecione..." else "",
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
            "Confira se a planilha foi compartilhada com CTCPPT SETRAND"
            "confirme se as credenciais estão corretas."
        )
