# TUTORIAL SISTEMA DE EMAILS - KARU
# Para Windows e Linux

## 📋 PRÉ-REQUISITOS

### 1. INSTALAÇÃO DO PYTHON E PIP

#### WINDOWS:
- Baixe Python: https://www.python.org/downloads/
- Marque "Add Python to PATH" durante instalação
- Verifique instalação: `python --version` e `pip --version`

#### LINUX (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

## Instalar todas as dependências Python necessárias
```bash
pip install celery redis django-celery-results django-celery-beat
```

LINUX:
# Ubuntu/Debian
```
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

_________________________________________________________

# CONFIGURAÇÃO DO GMAIL (OBRIGATÓRIO)

## Para enviar emails, configure o Gmail:

### Ativar Verificação em 2 Etapas:

#### Acesse: https://myaccount.google.com/security

#### Ative "Verificação em duas etapas"

#### Gerar Senha de App:

#### Acesse: https://myaccount.google.com/apppasswords

#### Selecione "Email" → "Outro (Nome personalizado)"

#### Digite "Karu Sistema" → Clique "Gerar"

#### Use a senha gerada em EMAIL_HOST_PASSWORD

#### Permitir Apps Menos Seguros (se necessário):

#### Acesse: https://myaccount.google.com/lesssecureapps

#### Ative a opção (não recomendado, use senha de app)

________________________________________________________

# EXECUÇÃO DO SISTEMA

## PASSO 1: APLICAR MIGRAÇÕES

```bash
python manage.py migrate
```

## PASSO 2: INICIAR REDIS

```bash
sudo systemctl start redis
# Ou
redis-server
```

## PASSO 3: INICIAR CELERY WORKER

### WINDOWS:
```cmd
celery -A seu_projeto worker --pool=solo --loglevel=info
```

### LINUX:
```bash
celery -A seu_projeto worker --loglevel=info
```

## PASSO 4: INICIAR CELERY BEAT (AGENDADOR)

```bash
celery -A seu_projeto beat --loglevel=info
```

## PASSO 5: INICIAR SERVIDOR DJANGO

```bash
python manage.py runserver
```
_______________________________________________________________

## NOTAS IMPORTANTES

NUNCA commitar emails e senhas reais no código
Use variáveis de ambiente para dados sensíveis
Teste sempre em ambiente de desenvolvimento primeiro
Configure backups regulares do Redis se usar em produção

