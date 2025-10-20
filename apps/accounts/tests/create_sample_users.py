import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from apps.accounts.models import GestorProfile, ProfissionalSaudeProfile, PaisProfile

User = get_user_model()

def create_sample_users():
    print("👥 CRIANDO USUÁRIOS DE EXEMPLO (VERSÃO CORRIGIDA)")
    print("=" * 60)
    
    # Garante que os grupos existem
    groups_map = {
        'gestores': Group.objects.get_or_create(name='gestores')[0],
        'profissionais_saude': Group.objects.get_or_create(name='profissionais_saude')[0],
        'pais': Group.objects.get_or_create(name='pais')[0]
    }
    
    print("✅ Grupos verificados/criados")
    
    # 1. Gestor
    if not User.objects.filter(username='12345678901').exists():
        gestor_user = User.objects.create_user(
            username='12345678901',
            email='maria.silva@ubs.com',
            password='senha123',
            first_name='Maria',
            last_name='Silva',
            user_type='gestor',
            is_active=True
        )
        # ⚡ CORREÇÃO: Adiciona ao grupo correto
        gestor_user.groups.add(groups_map['gestores'])
        
        GestorProfile.objects.create(
            user=gestor_user,
            cpf='12345678901',
            telefone='(11) 99999-9999',
            unidade='UBS Centro',
            cargo='Coordenadora de Saúde'
        )
        print("✅ Gestor criado: maria.silva@ubs.com / senha123")

    # 2. Profissional de Saúde - Médico
    if not User.objects.filter(username='23456789012').exists():
        medico_user = User.objects.create_user(
            username='23456789012',
            email='dr.carlos@ubs.com',
            password='senha123',
            first_name='Carlos',
            last_name='Santos',
            user_type='profissional_saude',
            is_active=True
        )
        # ⚡ CORREÇÃO: Adiciona ao grupo correto
        medico_user.groups.add(groups_map['profissionais_saude'])
        
        ProfissionalSaudeProfile.objects.create(
            user=medico_user,
            cpf='23456789012',
            categoria='Médico',
            especialidade='Pediatria',
            conselho='CRM',
            numero_registro='123456',
            unidade='UBS Centro',
            telefone='(11) 98888-8888'
        )
        print("✅ Médico criado: dr.carlos@ubs.com / senha123")

    # 3. Profissional de Saúde - Enfermeiro
    if not User.objects.filter(username='34567890123').exists():
        enfermeiro_user = User.objects.create_user(
            username='34567890123',
            email='ana.enfermeira@ubs.com',
            password='senha123',
            first_name='Ana',
            last_name='Oliveira',
            user_type='profissional_saude',
            is_active=True
        )
        #Adiciona ao grupo correto
        enfermeiro_user.groups.add(groups_map['profissionais_saude'])
        
        ProfissionalSaudeProfile.objects.create(
            user=enfermeiro_user,
            cpf='34567890123',
            categoria='Enfermeiro',
            especialidade='Neonatologia',
            conselho='COREN',
            numero_registro='654321',
            unidade='UBS Centro',
            telefone='(11) 97777-7777'
        )
        print("✅ Enfermeiro criado: ana.enfermeira@ubs.com / senha123")

    # 4. Pais/Responsável 1
    if not User.objects.filter(username='45678901234').exists():
        pais1_user = User.objects.create_user(
            username='45678901234',
            email='joao.silva@email.com',
            password='senha123',
            first_name='João',
            last_name='Silva',
            user_type='pais',
            is_active=True
        )
        # ⚡ CORREÇÃO: Adiciona ao grupo correto
        pais1_user.groups.add(groups_map['pais'])
        
        PaisProfile.objects.create(
            user=pais1_user,
            cpf='45678901234',
            telefone='(11) 96666-6666'
        )
        print("✅ Responsável criado: joao.silva@email.com / senha123")

    # 5. Pais/Responsável 2
    if not User.objects.filter(username='56789012345').exists():
        pais2_user = User.objects.create_user(
            username='56789012345',
            email='maria.oliveira@email.com',
            password='senha123',
            first_name='Maria',
            last_name='Oliveira',
            user_type='pais',
            is_active=True
        )
        # ⚡ CORREÇÃO: Adiciona ao grupo correto
        pais2_user.groups.add(groups_map['pais'])
        
        PaisProfile.objects.create(
            user=pais2_user,
            cpf='56789012345',
            telefone='(11) 95555-5555'
        )
        print("✅ Responsável criado: maria.oliveira@email.com / senha123")

    print("\n🎯 VERIFICAÇÃO FINAL:")
    verify_user_groups()

def verify_user_groups():
    """Verifica se todos os usuários estão nos grupos corretos"""
    print("\n🔍 VERIFICANDO GRUPOS DOS USUÁRIOS:")
    print("-" * 50)
    
    sample_usernames = ['12345678901', '23456789012', '34567890123', '45678901234', '56789012345']
    
    type_to_group = {
        'gestor': 'gestores',
        'profissional_saude': 'profissionais_saude',
        'pais': 'pais'
    }
    
    all_correct = True
    
    for username in sample_usernames:
        try:
            user = User.objects.get(username=username)
            expected_group = type_to_group.get(user.user_type)
            current_groups = list(user.groups.values_list('name', flat=True))
            
            status = "✅" if expected_group in current_groups else "❌"
            print(f"{status} {username}: {user.user_type} -> {current_groups}")
            
            if expected_group not in current_groups:
                all_correct = False
                
        except User.DoesNotExist:
            print(f"❌ {username}: NÃO ENCONTRADO")
            all_correct = False
    
    if all_correct:
        print("\n🎉 TODOS OS USUÁRIOS ESTÃO NOS GRUPOS CORRETOS!")
    else:
        print("\n⚠️  ALGUNS USUÁRIOS PRECISAM DE CORREÇÃO!")

if __name__ == '__main__':
    create_sample_users()