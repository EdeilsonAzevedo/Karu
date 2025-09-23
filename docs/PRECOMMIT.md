# 🔧 Guia Pre-commit - Projeto Karu

## O que é Pre-commit?

O **pre-commit** é uma ferramenta que executa verificações automáticas no seu código **antes** de cada commit. Isso garante que todo código que vai para o repositório siga os padrões de qualidade definidos pela equipe.

### O que nosso pre-commit faz:
- ✅ **Formatação automática** do código Python (Ruff)
- ✅ **Correção de problemas** básicos de linting
- ✅ **Padronização de mensagens** de commit
- ✅ **Consistência** no estilo de código

---

## 📦 Instalação (OBRIGATÓRIA para todos)

### Opção 1: Manual
```bash
# 1. Instalar Poetry (se não tiver)
curl -sSL https://install.python-poetry.org | python3 -

# 2. Instalar dependências
poetry install

# 3. Ativar ambiente virtual
poetry env activate

# 4. CRÍTICO: Instalar hooks
poetry run pre-commit install
poetry run pre-commit install --hook-type commit-msg

# 5. Testar
poetry run pre-commit run --all-files
```

---

## 🚀 Como usar no dia a dia

```bash
# 1. Ativar ambiente (sempre que abrir novo terminal)
poetry env activate

# 2. Fazer alterações e commit normal
git add .
git commit -m "feat: nova funcionalidade"

# 3. Pre-commit roda automaticamente ✨
```

### Padrão de mensagens de commit:
- `feat:` - Nova funcionalidade
- `fix:` - Correção de bug
- `docs:` - Documentação
- `style:` - Formatação, sem mudança de lógica
- `refactor:` - Refatoração de código
- `test:` - Adição ou correção de testes
- `chore:` - Tarefas de manutenção

**Exemplos:**
```bash
git commit -m "feat: implementar alta de paciente"
git commit -m "fix: corrigir validação de formulário"
git commit -m "docs: atualizar guia de setup"
```

---

## 🐛 Problemas Comuns e Soluções

### ❌ "Poetry não encontrado"
```bash
# Linux/Mac
curl -sSL https://install.python-poetry.org | python3 -


# Reiniciar terminal e verificar
poetry --version
```

### ❌ "Pre-commit não rodou"
```bash
# Ativar ambiente e reinstalar hooks
poetry env activate

# Ou manual:
pre-commit install
pre-commit install --hook-type commit-msg
```

### ❌ "Ruff failed" - Código foi modificado
**O que aconteceu:** O Ruff corrigiu automaticamente problemas de formatação.

**Solução:**
```bash
# Adicionar correções e tentar novamente
git add .
git commit -m "sua mensagem aqui"
```

### ❌ "Commitizen failed" - Mensagem inválida
**Exemplos de mensagens inválidas:**
```bash
❌ "correção bug"
❌ "nova feature"
❌ "fix bug do formulário"
```

**Exemplos de mensagens válidas:**
```bash
✅ "fix: correção de bug no formulário"
✅ "feat: nova funcionalidade de pacientes"
✅ "docs: atualizar documentação da API"
```


### Pre-commit manual:
```bash
# Rodar em todos os arquivos
pre-commit run --all-files

# Rodar apenas formatação
pre-commit run ruff-format --all-files

# Pular pre-commit (USE COM CUIDADO)
git commit -m "feat: sua mensagem" --no-verify
```

---

## 📝 Configuração do Projeto

### Arquivos importantes:
- `.pre-commit-config.yaml` - Configuração dos hooks
- `pyproject.toml` - Configuração do Ruff e dependências

### Nossa configuração atual:
- **Ruff**: Formatação e linting Python
- **Commitizen**: Padronização de mensagens
- **Target**: Python 3.12

---

## 🎯 Por que usamos Pre-commit?

- ✅ **Código consistente** em toda a equipe
- ✅ **Menos bugs** chegando ao repositório
- ✅ **Reviews mais rápidos** (foco na lógica, não formatação)
- ✅ **Histórico limpo** de commits
- ✅ **Produtividade** maior da equipe

---

*Lembre-se: O pre-commit é nosso amigo! Ele nos ajuda a manter a qualidade e consistência do código. 🚀*