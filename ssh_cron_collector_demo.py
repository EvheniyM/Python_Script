# ============================================
# Script: ssh_cron_collector_demo.py
# Description: ДЕМОНСТРАЦИОННЫЙ скрипт для подключения к SSH и сбора cron информации
# ВНИМАНИЕ: Использовать ТОЛЬКО на своих серверах с разрешения!
# Совместимость: Windows / Linux / MacOS
# ============================================

import concurrent.futures
import paramiko
import os
from pathlib import Path

def next_ip_address(ip):
    parts = ip.split('.')
    parts[-1] = str(int(parts[-1]) + 1)
    return '.'.join(parts)

def connect_ssh(ip, username, password):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, username=username, password=password, timeout=1)
        return client
    except (paramiko.ssh_exception.AuthenticationException, 
            paramiko.ssh_exception.SSHException, 
            paramiko.ssh_exception.NoValidConnectionsError) as e:
        print(f"Failed to connect to {ip} with {username}: {e}")
        return None
    except Exception as e:
        print(f"Error connecting to {ip}: {e}")
        return None

def execute_command(ssh_client, command):
    stdin, stdout, stderr = ssh_client.exec_command(command)
    output = stdout.read().decode('utf-8')
    return output

def process_host(ip, cred):
    ssh_client = connect_ssh(ip, cred["username"], cred["password"])
    if ssh_client:
        try:
            vm_name = execute_command(ssh_client, "hostname").strip()
            cron_info = execute_command(ssh_client, "crontab -l")
            ssh_client.close()
            return f"{vm_name}: {cron_info}"
        except Exception as e:
            print(f"Error processing {ip}: {e}")
            return None
    else:
        return None

def main():
    # ========== КОНФИГУРАЦИЯ - ЗАМЕНИТЕ НА ВАШИ ДАННЫЕ ==========
    # Диапазон IP для сканирования
    start_ip = "192.168.1.1"      # Пример начального IP
    end_ip = "192.168.1.254"      # Пример конечного IP
    
    # Используем относительный путь (работает на любой ОС)
    # Создаем папку logs в текущей директории
    log_dir = Path("logs") / "ssh_cron"
    log_dir.mkdir(parents=True, exist_ok=True)
    output_file = log_dir / f"scan_results_{start_ip}.log"
    
    # ========== УЧЕТНЫЕ ДАННЫЕ - НИКОГДА НЕ ХРАНИТЕ В КОДЕ! ==========
    # Используйте переменные окружения или внешний конфиг файл
    credentials = [
        {"username": "demo_user", "password": "demo_password"},
        {"username": "test_account", "password": "test_password"}
    ]
    
    # ========== ПРОВЕРКА БЕЗОПАСНОСТИ ==========
    print("=" * 60)
    print("⚠️  ВНИМАНИЕ: Этот скрипт предназначен ТОЛЬКО для образовательных целей!")
    print("Использовать разрешено ТОЛЬКО на серверах, которыми вы владеете")
    print("или имеете письменное разрешение на тестирование.")
    print("=" * 60)
    
    confirm = input("У вас есть разрешение на сканирование этой сети? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Сканирование отменено.")
        return
    
    all_vm_cron_info = []
    
    # Генерация списка IP для сканирования
    base_ip = '.'.join(start_ip.split('.')[:-1])
    start_octet = int(start_ip.split('.')[-1])
    end_octet = int(end_ip.split('.')[-1])
    
    if start_octet > end_octet:
        print(f"Ошибка: начальный IP {start_octet} больше конечного {end_octet}")
        return
    
    total_ips = end_octet - start_octet + 1
    print(f"\n📊 Диапазон сканирования: {base_ip}.{start_octet} - {base_ip}.{end_octet}")
    print(f"📊 Всего IP для проверки: {total_ips}")
    print(f"📊 Учетных записей: {len(credentials)}")
    print(f"📊 Всего попыток: {total_ips * len(credentials)}")
    
    # Сканирование с прогрессом
    from datetime import datetime
    start_time = datetime.now()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for octet in range(start_octet, end_octet + 1):
            ip_address = f"{base_ip}.{octet}"
            for cred in credentials:
                futures.append(executor.submit(process_host, ip_address, cred))
        
        # Сбор результатов с отображением прогресса
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            result = future.result()
            if result:
                all_vm_cron_info.append(result)
                print(f"[{completed}/{len(futures)}] ✓ Найден доступ: {result.split(':')[0]}")
            elif completed % 50 == 0:  # Показываем прогресс каждые 50 попыток
                print(f"[{completed}/{len(futures)}] Прогресс...")
    
    # Сохранение результатов
    elapsed_time = datetime.now() - start_time
    
    if all_vm_cron_info:
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(f"# SSH Scan Results\n")
            file.write(f"# Scan range: {start_ip} - {end_ip}\n")
            file.write(f"# Scan time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            file.write(f"# Duration: {elapsed_time}\n")
            file.write(f"# Successful connections: {len(all_vm_cron_info)}\n")
            file.write("=" * 60 + "\n\n")
            file.write("\n\n".join(all_vm_cron_info))
        
        print(f"\n✅ Результаты сохранены в: {output_file.absolute()}")
        print(f"✅ Успешных подключений: {len(all_vm_cron_info)}")
        print(f"✅ Время выполнения: {elapsed_time}")
    else:
        print("\n❌ Не удалось подключиться ни к одному серверу")
        print("❌ Проверьте IP диапазон и учетные данные")

if __name__ == "__main__":
    main()
