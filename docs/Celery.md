  # Executar sistema(linux):

  `Passo`: Abra 4 terminais e execute em cada um deles os comandos abaixo,
  cada um deles deve ser executado no ambiente virtual ao qual o projeto se localiza. 
  EX: Ativar ambiente virtual
  source karu_env/bin/activate 
  
  ### Terminal 1 - Servidor Django
  python manage.py runserver

  ### Terminal 2 - Celery Worker
  celery -A config worker --loglevel=info

  ### Terminal 3 - Celery Beat (para tarefas agendadas)
  celery -A config beat --loglevel=info

  ### Terminal 4 - Redis server
  sudo systemctl start redis
__________________________________________________________________________
  ## Script para ativaçao linux(start_karu.sh)
  #!/bin/bash
  echo "🚀 Iniciando Sistema Karu..."

  source karu_env/bin/activate

  sudo systemctl start redis

  echo "📧 Iniciando Celery Worker..."
  
  celery -A config worker --loglevel=info --logfile=logs/celery.log &

  echo "⏰ Iniciando Celery Beat..." 
  
  celery -A config beat --loglevel=info --logfile=logs/beat.log &

  echo "🌐 Iniciando Servidor Django..."
  
  python manage.py runserver 0.0.0.0:8000

  echo "✅ Sistema Karu em execução!"
  __________________________________________________________________________

  # Executar sistema(Windows):

  `Passo`: Abra 4 terminais e execute em cada um deles os comandos abaixo,
  cada um deles deve ser executado no ambiente virtual ao qual o projeto se localiza. 
  EX:Ativar ambiente virtual
  karu_env\Scripts\activate

  ### Terminal 1 - Servidor Django
  python manage.py runserver

  ### Terminal 2 - Redis
  redis-server

  ### Terminal 3 - Celery Worker
  celery -A config worker --loglevel=info --pool=solo

  ### Terminal 4 - Celery Beat
  celery -A config beat --loglevel=info

  __________________________________________________________________________
  ## Script para ativaçao Windows(start_karu.bat)

  @echo off
  echo 🚀 Iniciando Sistema Karu...

  REM Ativar ambiente virtual
  
  call karu_env\Scripts\activate

  REM Iniciar Redis
  
  start redis-server

  REM Iniciar Celery Worker
  
  start cmd /k "karu_env\Scripts\activate && celery -A config worker --loglevel=info --pool=solo"

  REM Iniciar Celery Beat 
  
  start cmd /k "karu_env\Scripts\activate && celery -A config beat --loglevel=info"

  REM Iniciar Servidor Django
  
  echo 🌐 Iniciando Servidor Django...
  
  python manage.py runserver

  pause
  __________________________________________________________________________
  ## Configurar Senha de App para Email (Gmail)
  
  `Passo 2`: 
  
  1. Acessar Configurações da Conta Google.
      
  [https://myaccount.google.com/]

  2. Ativar Verificação em 2 Etapas
     
     Clique em `Segurança` no menu lateral
     
     Em `Como fazer login no Google` → `Verificação em 2 etapas`
     
     Clique em `Começar` e siga as instruções
     
     Configure com: SMS, Authenticator app ou backup codes
     
  ## Criar Senha de App
  
  `Passo 3`:
  
  Volte para "Segurança"
  
  Em `Como fazer login no Google` → `Senhas de app`
  
  Clique em `Selecionar app` → Escolha `Outro (Nome personalizado)`
  
  Digite: `Karu Alertas` → Escolha o nome adequado para a aplicaçao
  
  Clique em `Gerar`
  
  COPIE A SENHA (16 caracteres) - ela só aparece uma vez!
  __________________________________________________________________________
  ## Configurar no Django
  No `settings.py`:
  ```
  Configurações de Email
  EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
  EMAIL_HOST = 'smtp.gmail.com'
  EMAIL_PORT = 587
  EMAIL_USE_TLS = True
  EMAIL_HOST_USER = 'seuemail@gmail.com'  # Seu email Gmail
  EMAIL_HOST_PASSWORD = 'sua-senha-de-app-aqui'  # Cole a senha de 16 caracteres aqui
  DEFAULT_FROM_EMAIL = 'seuemail@gmail.com'

  # Lista de destinatários para alertas
  ALERT_EMAIL_RECIPIENTS = ['seuemail@gmail.com', 'outroemail@hospital.com']
  ```
  Importante!
  NÃO use sua senha normal do Gmail
  A senha de app é específica para aplicações
  Se perder, gere uma nova e atualize o settings.py
  Funciona apenas com contas Gmail pessoais
