import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def reactivate_users():
    print("🔄 REATIVAR USUÁRIOS DESATIVADOS")
    print("=" * 50)
    
    inactive_users = User.objects.filter(is_active=False).order_by('username')
    
    if not inactive_users:
        print("✅ Nenhum usuário desativado para reativar.")
        return
    
    print("Usuários desativados encontrados:\n")
    
    for i, user in enumerate(inactive_users, 1):
        status = "🔴 INATIVO"
        print(f"{i}. {status} - {user.username} - {user.get_full_name()}")
    
    print("\nDigite o número do usuário para reativar (ou 0 para sair):")
    
    try:
        choice = int(input("Escolha: "))
        if choice == 0:
            return
        
        selected_user = inactive_users[choice - 1]
        
        print("\n🔍 Confirmando reativação:")
        print(f"   Usuário: {selected_user.username}")
        print(f"   Nome: {selected_user.get_full_name()}")
        print(f"   Email: {selected_user.email}")
        print(f"   Tipo: {selected_user.get_user_type_display()}")
        
        confirm = input("\n❓ Tem certeza que deseja reativar este usuário? (s/N): ")
        
        if confirm.lower() in ['s', 'sim', 'y', 'yes']:
            selected_user.is_active = True
            selected_user.save()
            print(f"✅ Usuário {selected_user.username} reativado com sucesso!")
        else:
            print("❌ Reativação cancelada.")
            
    except (ValueError, IndexError):
        print("❌ Escolha inválida!")

if __name__ == '__main__':
    reactivate_users()