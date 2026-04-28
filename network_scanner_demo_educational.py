# ⚠️ LEGAL WARNING - EDUCATIONAL PURPOSE ONLY

This network scanner is for **educational purposes only**.

## Legal Requirements:
- ✅ You MUST have WRITTEN PERMISSION from the network owner
- ✅ Use ONLY on networks you own or are authorized to test
- ❌ DO NOT scan networks without authorization (illegal in many countries)
- ❌ DO NOT use for malicious purposes

## Potential Violations:
- Computer Fraud and Abuse Act (CFAA) in the US
- General Data Protection Regulation (GDPR) in the EU
- Similar laws in other jurisdictions

## Responsible Use:
1. Get explicit permission before scanning
2. Document your authorization
3. Limit scanning to necessary targets
4. Handle results responsibly
5. Follow your organization's security policies

**The author assumes no responsibility for misuse.**


# ============================================
# Script: network_scanner_demo.py
# Description: Демонстрационный скрипт для сканирования сети (nmap + ARP)
# ВНИМАНИЕ: Использовать ТОЛЬКО в разрешенных сетях и с согласия владельца
# ============================================

import nmap
import socket
import os
import time
from concurrent.futures import ThreadPoolExecutor
from scapy.all import ARP, Ether, srp

# Функция для получения MAC-адреса с использованием ARP
def get_mac_address(ip_address):
    arp_request = ARP(pdst=ip_address)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast/arp_request
    answered_list = srp(arp_request_broadcast, timeout=1, verbose=False)[0]

    if answered_list:
        return answered_list[0][1].hwsrc
    else:
        return "No MAC address"

# Функция для сканирования хоста
def scan_host(ip_address, output_file_path):
    nm = nmap.PortScanner()

    with open(output_file_path, "a") as output_file:
        try:
            nm.scan(hosts=ip_address, arguments='-sn')
            
            if nm[ip_address].state() == "up":
                mac_address = get_mac_address(ip_address)

                try:
                    dns_name = socket.gethostbyaddr(ip_address)[0]
                except socket.herror:
                    dns_name = "No DNS name"

                nm.scan(hosts=ip_address, arguments='-sV')
                open_ports = []

                for proto in nm[ip_address].all_protocols():
                    ports = nm[ip_address][proto]
                    for port, port_info in ports.items():
                        if port_info['state'] == 'open':
                            service = port_info.get('name', 'unknown')
                            version = port_info.get('version', 'unknown')
                            product = port_info.get('product', 'unknown')
                            open_ports.append(f"{proto.upper()}/{port}: {service} ({product} {version})")

                # Отладочные выводы
                print(f"Host: {ip_address}")
                print(f"  MAC Address: {mac_address}")
                print(f"  DNS Name: {dns_name}")
                if open_ports:
                    print(f"  Open Ports: {', '.join(open_ports)}")

                # Запись в файл
                output_file.write(f"IP Address: {ip_address}\n")
                output_file.write(f"DNS Name: {dns_name}\n")
                output_file.write(f"MAC Address: {mac_address}\n")
                if open_ports:
                    output_file.write("Open Ports and Services:\n")
                    for port in open_ports:
                        output_file.write(f"  - {port}\n")
                else:
                    output_file.write("No open ports found.\n")
                output_file.write('-' * 50 + '\n')
            else:
                print(f"Host {ip_address} is down.")
        except Exception as e:
            with open(output_file_path, "a") as output_file:
                output_file.write(f"Error scanning host {ip_address}: {e}\n")
                print(f"Error scanning host {ip_address}: {e}")

# Функция для сканирования подсети
def scan_subnet(subnet, output_file_path):
    nm = nmap.PortScanner()

    with open(output_file_path, "a") as output_file:
        output_file.write(f"\nScanning subnet: {subnet}\n")
        output_file.write("=" * 50 + "\n")

        try:
            nm.scan(hosts=subnet, arguments='-sn')
        except Exception as e:
            output_file.write(f"Error scanning subnet {subnet}: {e}\n")
            print(f"Error scanning subnet {subnet}: {e}")
            return

        active_hosts = [host for host in nm.all_hosts() if nm[host].state() == "up"]
        print(f"Active hosts in {subnet}: {', '.join(active_hosts)}")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(scan_host, host, output_file_path) for host in active_hosts]
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    print(f"Error during scanning: {e}")

# Основная функция
def main():
    # Используем уникальный файл для каждого запуска
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    output_file_path = os.path.join(os.getcwd(), f"network_scan_results_{timestamp}.txt")

    # ЗАМЕНИТЕ на ваши сети или используйте параметры командной строки
    # Примеры частных IP диапазонов (замените на свои)
    private_ip_ranges = [
        "192.168.1.0/24",      # Пример: домашняя сеть
        "10.0.0.0/24",         # Пример: офисная сеть
        "172.16.0.0/24"        # Пример: корпоративная сеть
    ]

    print("=" * 60)
    print("ВНИМАНИЕ: Сканирование сети без разрешения может быть НЕЗАКОННЫМ!")
    print("Убедитесь, что у вас есть право сканировать указанные сети.")
    print("=" * 60)
    
    response = input("Продолжить? (yes/no): ")
    if response.lower() != 'yes':
        print("Сканирование отменено.")
        return

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(scan_subnet, ip_range, output_file_path) for ip_range in private_ip_ranges]

        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"Error during scanning: {e}")

    print(f"\nScan results saved to {output_file_path}")

if __name__ == "__main__":
    main()
