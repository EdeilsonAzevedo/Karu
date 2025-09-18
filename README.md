# Karu  Kangaroo Neonatal Platform

Backend Django e templates para a plataforma de acompanhamento neonatal baseada no Método Canguru.

---

## 🚀 **Guia de Instalação e Execução**

Siga os passos abaixo para configurar e rodar o ambiente de desenvolvimento.

### **1. Pré-requisitos**

-   **Python**: `3.12`
-   **Gerenciador de Pacotes**: [Poetry](https://python-poetry.org/)
-   **Instalador de Aplicações**: [pipx](https://pypa.github.io/pipx/) (opcional, mas recomendado)

### **2. Configuração do Ambiente**

```bash
# Clone o repositório e entre no diretório
git clone [https://github.com/edeilson_azevedo/karu.git](https://github.com/edeilson_azevedo/karu.git)
cd karu

# Instale as dependências do projeto com Poetry
poetry install

# Configure os hooks de pre-commit para garantir a qualidade do código
poetry run pre-commit install --hook-type pre-commit --hook-type commit-msg
```

### **3. Execução do Servidor**

```bash
# Aplique as migrações do banco de dados
poetry run python manage.py migrate

# Inicie o servidor de desenvolvimento
poetry run python manage.py runserver
```

---

## 🛠️ **Ferramentas e Padrões de Qualidade**

Este projeto utiliza ferramentas modernas para garantir um código limpo, testado e padronizado.

### **Checagens Manuais**

Você pode rodar as seguintes checagens a qualquer momento:

-   **Formatação e Lint (Ruff):**
    ```bash
    poetry run ruff check . --fix
    poetry run ruff format .
    ```

-   **Análise de Tipagem (Pyright):**
    ```bash
    poetry run pyright
    ```

-   **Execução de Testes (Pytest):**
    ```bash
    poetry run pytest
    ```

### **Padrão de Commits**

Utilizamos o padrão **Conventional Commits** para manter o histórico de versões organizado.

| Prefixo | Descrição                                  |
| :------ | :----------------------------------------- |
| `feat`  | Adiciona uma nova funcionalidade.          |
| `fix`   | Corrige um bug.                            |
| `docs`  | Altera apenas a documentação.              |
| `test`  | Adiciona ou modifica testes.               |
| `chore` | Manutenção do repositório (sem alteração de código de produção). |

*Exemplo de mensagem de commit:*
```
feat(patients): adicionar endpoint para cadastro de recém-nascido
```

---

## 🏗️ **Arquitetura do Projeto**

O backend é organizado nos seguintes apps Django:

-   **`accounts`**: Gerenciamento de usuários e papéis.
-   **`patients`**: Cadastro e dados clínicos dos pacientes.
-   **`kangaroo_method`**: Rotinas específicas do Método Canguru.
-   **`reports`**: Dashboards e relatórios.
-   **`notifications`**: Sistema de alertas e lembretes.
-   **`core`**: Componentes e utilitários compartilhados.