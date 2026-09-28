#Atualização Semanal dos contratos - App em streamlit

App web simples. 
O fiscal abre um link, coloca a senha comum entre eles, escolhe o seu nome, aparece os seus contratos, 
preenche um ou mais contrato (botão adcionar/remover incluído) e enviando tudo para a planilha do gestor. 

#O que o fiscal ve?
1. Escolha o **nome dele** numa lista -**todos os fiscais aparecem**, 
inclusive os que nao tem nenhum contrato em execução no momento. 
2. Aparecem os **contratos dele** (pre carregado a partir do código dados.py) mais a opção **"Não há atualização"**. 
    Fiscais sem contratos tem somente essa opção disponível.
3. Há dois blocos diferentes para preencher dependendo do contrato escolhido. Os campos para preencher são: 
Bloco 1: 
"Cidade", "Situação da Obra", "extensão Executada (km)", "Valor Executada (R$)", "Quantidade de Ruas Executadas", "observações" 
Bloco 2: 
"Cidade", "Lote", "Situação da Obra", "extensão Executada (km)", "Valor Executada (R$)", "Quantidade de Ruas Executadas","Data de Conclução" e "observações"

4. No final pode clicar em **"+ Adcionar outro contrato"** quantas vezes precisar, ou remover um bloco com o simbolo de lixeira.
5. Apos preencher por completo clica em **"Enviar Tudo"** - Todas as informações vão para uma planilha do google drive de uma vez.
  informações do Bloco 1 e dois vão para abas destintas. 
  
  
  
  ## Arquivos do projeto
   - "app.py" - o app em si
   - "dados.py" - Dicionário fiscal -> listas de contratos (Gerado a partir de um arquivo interno) [esse arquivo futuramente ficará no drive para nao escapar informações internas]
   
   -  "requeriments.txt" - dependências.
   - screts.toml - arquivos de credenciais (não disponivel no Github)
   

   
Planilha Criado no Drive com o nome: 

ATUALIZAÇÃO SEMANAL - CONTRATOS

(para mandar para outra planilha ou trocar o nome mudar no arquivo "app.py" na constante "NOME_DA_PLANILHA")


#

Criação do service accont no google cloud
 (A explicação para criar e explicada no próprio Google)
 
 Cpmpartilhar a planilha com a service account 
 
 baixe o arquivo ,json 
 . 
 Na planilha do Google Drive clique em compartilhar e adcione e-mail do arquivo .json como **editor**
 
Publicação no streamlit community cloud (de forma grátis)
Conectar a conta Github no streamlit e crie um novo app
Selecione o repositório, o branch e o arquivo "app.py". 
Adcione as crendenciais indicadas nas configurações - secrets (dados do arquivo .json)

Apois a criação é recebido um link (do tipo: https://nomeapp.streamlit.app) - 
link para ser distribuído entre os fiscais junto com a senha única




Há script interno para retirar os dados da planilha e jogar no banco de dados interno.
Somando os dados numéricos e substituindo os dados de situação observação. 
Para adcionar um novo contrato o fiscal entra em contato e pede a adição 
ou na aba observação pede para mudar a situação de algum contrato para "Em execução"



