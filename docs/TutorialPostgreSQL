# Tutorial: Instalando PostgreSQL e Criando um Banco de Dados

Este é um guia passo a passo para baixar, instalar e criar seu primeiro banco de dados com PostgreSQL no Windows.

---

## Parte 1: Baixando e Instalando o PostgreSQL

### Passo 1: Acesse o Site Oficial
Vá para a página de downloads oficial do PostgreSQL: [https://www.postgresql.org/download/](https://www.postgresql.org/download/)

### Passo 2: Escolha seu Sistema Operacional
Na página, você verá ícones para vários sistemas operacionais. Clique em **Windows**.

### Passo 3: Baixe o Instalador
1. A página irá te direcionar para um link para baixar o instalador da empresa EDB. Clique no link: **"Download the installer"**.
2. Escolha a versão mais recente do PostgreSQL para **Windows x86-64** e clique em **Download**.

### Passo 4: Execute o Instalador
Após o download, execute o arquivo `.exe`. Você verá um assistente de instalação. Siga os passos:

1.  **Setup**: Clique em "Next".
2.  **Installation Directory**: Pode deixar o diretório padrão. Clique em "Next".
3.  **Select Components**: Mantenha todos os componentes selecionados, especialmente `pgAdmin 4`, que é uma ferramenta gráfica muito útil. Clique em "Next".
    * `PostgreSQL Server`: O servidor do banco de dados.
    * `pgAdmin 4`: A interface gráfica para gerenciar seus bancos.
    * `Stack Builder`: Para instalar ferramentas adicionais (pode ignorar por agora).
    * `Command Line Tools`: Ferramentas de linha de comando como o `psql`.
4.  **Data Directory**: Pode deixar o padrão. Clique em "Next".
5.  **Password**: **ESTE É O PASSO MAIS IMPORTANTE!** Você precisa definir uma senha para o superusuário do banco de dados (o usuário padrão é `postgres`). **Escolha uma senha, anote-a e não a esqueça!** Você precisará dela sempre. Digite a senha duas vezes e clique em "Next".
6.  **Port**: Deixe a porta padrão `5432`. Clique em "Next".
7.  **Advanced Options**: Deixe o `Locale` como "Default locale". Clique em "Next".
8.  **Pre Installation Summary**: Revise as configurações e clique em "Next" para iniciar a instalação.
9.  **Finish**: Ao final, desmarque a opção "Stack Builder" e clique em "Finish".

**Pronto! O PostgreSQL está instalado.**

---

## Parte 2: Criando o Banco de Dados "karu"

Agora que o PostgreSQL está instalado, vamos criar o banco de dados.

### Método 1: Usando o pgAdmin 4 (Interface Gráfica) - Recomendado

#### Passo 1: Abra o pgAdmin 4
Vá ao Menu Iniciar do Windows, procure por **"pgAdmin 4"** e abra o aplicativo.

#### Passo 2: Conecte-se ao Servidor
1. No lado esquerdo, você verá "Servers". Dê um duplo clique nele.
2. Ele vai pedir a senha. Digite a **senha que você definiu durante a instalação** e marque "Save password" para não ter que digitá-la toda vez. Clique em "OK".

#### Passo 3: Crie o Banco de Dados
1. Com o servidor conectado, você verá uma lista de itens. Clique com o botão direito em **"Databases"**.
2. No menu que aparecer, vá para **Create > Database...**.

#### Passo 4: Dê o Nome ao Banco de Dados
1. Uma janela vai se abrir. No campo **"Database name"**, digite `karu`.
2. Você pode deixar todas as outras opções como estão.
3. Clique no botão **"Save"**.

**Sucesso!** Você verá agora o banco de dados `karu` listado sob "Databases" na barra lateral.
