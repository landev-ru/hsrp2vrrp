#!/usr/bin/env python3
# hsrp2vrrp — обёртка-лаунчер для migrate_to_vrrp2.py / migrate_to_vrrp3.py

import os
import sys
import shutil
import subprocess
BANNER = r"""
 █████                                   ████████                                           
░░███                                   ███░░░░███                                          
 ░███████    █████  ████████  ████████ ░░░    ░███ █████ █████ ████████  ████████  ████████ 
 ░███░░███  ███░░  ░░███░░███░░███░░███   ███████ ░░███ ░░███ ░░███░░███░░███░░███░░███░░███
 ░███ ░███ ░░█████  ░███ ░░░  ░███ ░███  ███░░░░   ░███  ░███  ░███ ░░░  ░███ ░░░  ░███ ░███
 ░███ ░███  ░░░░███ ░███      ░███ ░███ ███      █ ░░███ ███   ░███      ░███      ░███ ░███
 ████ █████ ██████  █████     ░███████ ░██████████  ░░█████    █████     █████     ░███████ 
░░░░ ░░░░░ ░░░░░░  ░░░░░      ░███░░░  ░░░░░░░░░░    ░░░░░    ░░░░░     ░░░░░      ░███░░░  
                              ░███                                                 ░███     
                              █████                                                █████    
                             ░░░░░                                                ░░░░░  
Created by LanDev
https://github.com/landev-ru/hsrp2vrrp
Contacts - fraso1989@gmail.com / Fraso@mail.ru
"""
def check_configs(file1, file2):
    """Проверяет наличие и доступность конфигов ядер."""
    print("  Проверка конфигурационных файлов ядер:")
    ok = True
    for path in (file1, file2):
        if not os.path.isfile(path):
            print(f"    [!] Не найден:          {path}")
            ok = False
        elif not os.access(path, os.R_OK):
            print(f"    [!] Нет прав на чтение: {path}")
            ok = False
        else:
            size = os.path.getsize(path)
            if size == 0:
                print(f"    [!] Файл пустой:        {path}")
                ok = False
            else:
                print(f"    [+] {path}  ({size} байт)")
    return ok


def find_script(name):
    """Ищет скрипт рядом с обёрткой, затем в PATH."""
    base = os.path.dirname(os.path.abspath(__file__))
    candidates = [name, name + ".py", name.replace(".py", "")]
    for c in candidates:
        p = os.path.join(base, c)
        if os.path.isfile(p):
            return p
    return shutil.which(name) or shutil.which(name.replace(".py", ""))


def check_scripts():
    """Проверяет наличие дочерних скриптов миграции."""
    print("\n  Проверка наличия скриптов миграции:")
    s2 = find_script("migrate_to_vrrp2.py")
    s3 = find_script("migrate_to_vrrp3.py")
    print(f"    [+] VRRPv2:  {s2 or 'НЕ НАЙДЕН'}")
    print(f"    [+] VRRPv3:  {s3 or 'НЕ НАЙДЕН'}")
    return s2, s3


def run_script(script_path, file1, file2):
    """Запускает дочерний скрипт, наследуя stdin/stdout/stderr."""
    cmd = [sys.executable, script_path, file1, file2]
    print(f"\n  [*] Запуск: {' '.join(cmd)}\n")
    print("  " + "─" * 66)
    try:
        proc = subprocess.run(cmd)
        return proc.returncode
    except FileNotFoundError:
        print("  [!] Не удалось запустить скрипт (нет интерпретатора?)")
        return 1
    except KeyboardInterrupt:
        print("\n  [!] Запуск прерван пользователем.")
        return 130


def show_menu(s2, s3):
    """Показывает меню и возвращает выбор."""
    print()
    print("  " + "=" * 62)
    print("  ГЛАВНОЕ МЕНЮ")
    print("  " + "=" * 62)
    mark2 = "" if s2 else "  (недоступно)"
    mark3 = "" if s3 else "  (недоступно)"
    print(f"  1 — Перейти на VRRPv2  (migrate_to_vrrp2.py){mark2}")
    print(f"  2 — Перейти на VRRPv3  (migrate_to_vrrp3.py){mark3}")
    print("  0 — Выход")
    print("  " + "=" * 62)
    while True:
        choice = input("  Ваш выбор (0/1/2): ").strip()
        if choice in ("0", "1", "2"):
            return choice
        print("  [!] Неверный выбор, попробуйте снова.")


def main():
    print(BANNER)

    # ---- пути к конфигам ----
    file1 = sys.argv[1] if len(sys.argv) > 1 else "core1.txt"
    file2 = sys.argv[2] if len(sys.argv) > 2 else "core2.txt"

    # ---- проверка конфигов ----
    configs_ok = check_configs(file1, file2)
    if not configs_ok:
        print("\n  [!] Не все конфигурационные файлы доступны.")
        print("      Экспортируйте конфиги ядер:")
        print('        ssh admin@core1 "show run" > core1.txt')
        print('        ssh admin@core2 "show run" > core2.txt')
        print("      Либо передайте пути аргументами:")
        print("        python3 hsrp2vrrp.py path/core1.txt path/core2.txt")
        ans = input("\n  Продолжить всё равно? (y/N): ").strip().lower()
        if ans != "y":
            print("  Выход.")
            sys.exit(1)

    # ---- проверка скриптов ----
    s2, s3 = check_scripts()

    if not s2 and not s3:
        print("\n  [!] Ни один из скриптов миграции не найден рядом с hsrp2vrrp.py.")
        print("      Положите migrate_to_vrrp2.py и migrate_to_vrrp3.py в ту же папку.")
        sys.exit(1)

    # ---- основной цикл ----
    while True:
        choice = show_menu(s2, s3)

        if choice == "0":
            print("\n  Выход.")
            sys.exit(0)

        if choice == "1":
            if not s2:
                print("  [!] migrate_to_vrrp2.py не найден.")
                continue
            rc = run_script(s2, file1, file2)
            print(f"\n  [i] migrate_to_vrrp2.py завершён (код {rc})")

        elif choice == "2":
            if not s3:
                print("  [!] migrate_to_vrrp3.py не найден.")
                continue
            rc = run_script(s3, file1, file2)
            print(f"\n  [i] migrate_to_vrrp3.py завершён (код {rc})")

        print()
        again = input("  Вернуться в меню? (Y/n): ").strip().lower()
        if again == "n":
            print("  Выход.")
            sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  [!] Прервано пользователем.")
        sys.exit(130)
