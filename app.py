import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
from zoneinfo import ZoneInfo
import uuid

from dados import FISCAIS_CONTRATOS

FUSO_BR = ZoneInfo("America/Maceio")  

# CONFIGURAÇÃO DA PÁGINA
# ------------------------------------------------------------------
st.set_page_config(page_title="Atualização Semanal - Contratos", page_icon="🛣️", layout="centered")

NOME_DA_PLANILHA = "Atualização Semanal - Contratos"  
NOME_DA_ABA = "Respostas" 
NOME_DA_ABA_PRO_ESTRADA = "Pró-Estrada"  

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

CABECALHO_PRO_ESTRADA = [
    "Data/Hora",
    "Fiscal",
    "Lote",
    "Cidade",
    "Recapeamento - Investimento",
    "Recapeamento - Extensão Executada (Km)",
    "Recapeamento - Quantidade de Ruas",
    "Recapeamento - Conclusão da Obra",
    "Recapeamento - Data de Conclusão",
    "Sinalização - Investimento",
    "Sinalização - Extensão Executada (Km)",
    "Sinalização - Quantidade de Ruas",
    "Sinalização - Conclusão da Obra",
    "Sinalização - Data de Conclusão",
]

SEM_ATUALIZACAO = "Não há atualização"
PRO_ESTRADA = "Pró-Estrada"
FISCAL_PRO_ESTRADA = "Marcelo de Carvalho Santos"  
SITUACOES_OBRA = ["Selecione...", "Em Execução", "Não Iniciada", "Concluída", "Paralisada"]
LOTES = ["Selecione...", "Lote 1", "Lote 2"]


def formatar_valor_brl(valor):
    """Converte um float em texto no formato XX.xxx.xxx,XX."""
    texto = f"{valor:,.2f}"  
    texto = texto.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
    return texto



# CONEXÃO COM O GOOGLE SHEETS
# ------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def conectar_cliente():
    escopos = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credenciais = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=escopos
    )
    return gspread.authorize(credenciais)


def obter_aba(nome_aba, cabecalho):
    cliente = conectar_cliente()
    planilha = cliente.open(NOME_DA_PLANILHA)

    try:
        aba = planilha.worksheet(nome_aba)
    except gspread.WorksheetNotFound:
        aba = planilha.add_worksheet(title=nome_aba, rows=1000, cols=len(cabecalho))

    if aba.row_values(1) != cabecalho:
        aba.update("A1", [cabecalho])

    return aba


def enviar_linhas(nome_aba, cabecalho, linhas):
    if not linhas:
        return
    aba = obter_aba(nome_aba, cabecalho)
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


# TELA DE SENHA
# ------------------------------------------------------------------

def senha_correta():
    if st.session_state.get("autenticado"):
        return True

    st.markdown(
        "<h2 style='text-align: center;'>🔒 Acesso restrito</h2>",
        unsafe_allow_html=True,
    )
    with st.form("form_senha"):
        senha_digitada = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

    if entrar:
        if senha_digitada == st.secrets.get("app_password", ""):
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Senha incorreta.")#

    return False


if not senha_correta():
    st.stop()


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
opcoes_contrato = [c["contrato"] for c in contratos_do_fiscal]
if fiscal == FISCAL_PRO_ESTRADA:
    opcoes_contrato = opcoes_contrato + [PRO_ESTRADA]
opcoes_contrato = opcoes_contrato + [SEM_ATUALIZACAO]

st.divider()

respostas_normais = []
respostas_pro_estrada = []

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
        eh_pro_estrada = contrato_selecionado == PRO_ESTRADA

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
            situacao_obra = st.selectbox(
                "Situação da Obra",
                options=SITUACOES_OBRA,
                key=f"situacao__{bloco_id}",
            )
            observacoes = st.text_area(
                "Observações (opcional)",
                key=f"obs__{bloco_id}",
                placeholder="Pode explicar o motivo, se quiser (ex: obra parada, sem medição na semana) ou pedido para incluir contratos...",
            )

            respostas_normais.append(
                [
                    datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M:%S"),
                    fiscal,
                    aba_origem,
                    contrato_selecionado,
                    cidade.strip(),
                    situacao_obra if situacao_obra != "Selecione..." else "",
                    "",
                    "",
                    "",
                    observacoes,
                ]
            )
        elif eh_pro_estrada:
            lote = st.selectbox(
                "Lote",
                options=LOTES,
                key=f"lote__{bloco_id}",
            )

            def bloco_recape_ou_sinalizacao(rotulo, prefixo):
                st.markdown(f"**{rotulo}**")
                col1, col2 = st.columns(2)
                with col1:
                    investimento_num = st.number_input(
                        "Investimento (R$)",
                        min_value=0.0,
                        step=1000.0,
                        format="%.2f",
                        key=f"{prefixo}_investimento__{bloco_id}",
                    )
                    investimento = formatar_valor_brl(investimento_num)
                    st.caption(f"R$ {investimento}")
                with col2:
                    extensao = st.number_input(
                        "Extensão Executada (Km)",
                        min_value=0.0,
                        step=0.1,
                        format="%.2f",
                        key=f"{prefixo}_extensao__{bloco_id}",
                    )

                qtd_ruas = st.number_input(
                    "Quantidade de Ruas",
                    min_value=0,
                    step=1,
                    key=f"{prefixo}_ruas__{bloco_id}",
                )
                qtd_ruas = int(qtd_ruas)

                conclusao_texto = st.text_input(
                    "Conclusão da Obra",
                    key=f"{prefixo}_conclusao__{bloco_id}",
                    placeholder="Ex: Concluído, Em execução, etc.",
                )

                data_conclusao = st.date_input(
                    "Data de Conclusão",
                    key=f"{prefixo}_data__{bloco_id}",
                    value=None,
                    format="DD/MM/YYYY",
                )
                data_conclusao_txt = (
                    data_conclusao.strftime("%d/%m/%Y") if isinstance(data_conclusao, date) else ""
                )

                return [investimento, extensao, qtd_ruas, conclusao_texto, data_conclusao_txt]

            dados_recapeamento = bloco_recape_ou_sinalizacao("Recapeamento", "recape")
            st.divider()
            dados_sinalizacao = bloco_recape_ou_sinalizacao("Sinalização", "sinal")

            respostas_pro_estrada.append(
                [
                    datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M:%S"),
                    fiscal,
                    lote if lote != "Selecione..." else "",
                    cidade.strip(),
                    *dados_recapeamento,
                    *dados_sinalizacao,
                ]
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

            respostas_normais.append(
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
            enviar_linhas(NOME_DA_ABA, CABECALHO, respostas_normais)
            enviar_linhas(NOME_DA_ABA_PRO_ESTRADA, CABECALHO_PRO_ESTRADA, respostas_pro_estrada)
        st.session_state.enviado = True
        st.rerun()
    except Exception as e:
        st.error(f"Ocorreu um erro ao enviar os dados: {e}")
        st.caption(
            "Confira se a planilha foi compartilhada"
            "e se as credenciais em estão corretas."
        )
