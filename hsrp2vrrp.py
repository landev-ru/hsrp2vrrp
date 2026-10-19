#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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


# ─── Проверки окружения ─────────────────────────────────────────────────────
def check_configs(file1, file2):
    """Возвращает (ok, {path: (exists, error)})."""
    results = {}
    ok = True
    for path in (file1, file2):
        if not os.path.isfile(path):
            results[path] = (False, 'not found')
            ok = False
        elif not os.access(path, os.R_OK):
            results[path] = (False, 'no read permission')
            ok = False
        elif os.path.getsize(path) == 0:
            results[path] = (False, 'empty file')
            ok = False
        else:
            results[path] = (True, None)
    return ok, results


def find_script(name):
    base = os.path.dirname(os.path.abspath(__file__))
    for candidate in (name, name + '.py', name.replace('.py', '')):
        path = os.path.join(base, candidate)
        if os.path.isfile(path):
            return path
    return shutil.which(name) or shutil.which(name.replace('.py', ''))


def check_scripts():
    return find_script('migrate_to_vrrp2.py'), find_script('migrate_to_vrrp3.py')


# ─── Запуск дочернего скрипта ───────────────────────────────────────────────
def run_script(script_path, file1, file2):
    cmd = [sys.executable, script_path, file1, file2]
    print()
    print(f"  run: {' '.join(cmd)}")
    print(f"  {'-' * 62}")
    print()
    try:
        proc = subprocess.run(cmd)
        return proc.returncode
    except FileNotFoundError:
        print("  [X] Cannot launch script (no interpreter?)")
        return 1
    except KeyboardInterrupt:
        print("\n  [!] Interrupted by user.")
        return 130


# ─── Отрисовка меню ─────────────────────────────────────────────────────────
def show_menu(file1, file2, cfg_results, s2, s3):
    """Рисует строго симметричное ASCII-меню."""
    width = 62

    print()
    print(f"  {'=' * width}")
    print(f"  {'HSRP -> VRRP Migration Toolkit'.center(width)}")
    print(f"  {'=' * width}")
    print()

    # Статусы (выравниваем пробелами с помощью :<22)
    c1 = f"{file1} [OK]" if cfg_results[file1][0] else f"{file1} [FAIL]"
    c2 = f"{file2} [OK]" if cfg_results[file2][0] else f"{file2} [FAIL]"
    
    sc2 = "migrate_to_vrrp2.py [OK]" if s2 else "migrate_to_vrrp2.py [FAIL]"
    sc3 = "migrate_to_vrrp3.py [OK]" if s3 else "migrate_to_vrrp3.py [FAIL]"

    print(f"  Configs: {c1:<25} {c2}")
    print(f"  Scripts: {sc2:<25} {sc3}")
    print()

    print(f"  {'-' * width}")
    print()

    # Пункты меню
    print("    [1]  Migrate to VRRPv2  (with authentication)")
    print("    [2]  Migrate to VRRPv3  (no authentication)")
    print("    [0]  Exit")
    print()

    print(f"  {'=' * width}")
    print()

    # Ввод
    while True:
        try:
            choice = input("  Your choice (0/1/2): ").strip()
        except EOFError:
            return '0'
        if choice in ('0', '1', '2'):
            return choice
        print("  [!] Invalid choice. Enter 0, 1 or 2.")


# ─── Сообщение о завершении дочернего скрипта ───────────────────────────────
def _show_rc(rc, name):
    print()
    if rc == 0:
        print(f"  [OK] {name} finished successfully")
    else:
        print(f"  [X]  {name} finished with code {rc}")


# ─── Основная логика ────────────────────────────────────────────────────────
def main():
    print(BANNER)

    file1 = sys.argv[1] if len(sys.argv) > 1 else 'core1.txt'
    file2 = sys.argv[2] if len(sys.argv) > 2 else 'core2.txt'

    cfg_ok, cfg_results = check_configs(file1, file2)
    s2, s3 = check_scripts()

    if not s2 and not s3:
        print()
        print("  [X] No migration scripts found next to hsrp2vrrp.py.")
        print("  Place migrate_to_vrrp2.py and migrate_to_vrrp3.py in the same folder.")
        print()
        sys.exit(1)

    if not cfg_ok:
        print()
        print("  [!] Not all core config files are available.")
        print("  Export core configs:")
        print('    ssh admin@core1 "show run" > core1.txt')
        print('    ssh admin@core2 "show run" > core2.txt')
        print("  Or pass paths as arguments:")
        print("    python3 hsrp2vrrp.py path/core1.txt path/core2.txt")
        try:
            ans = input("\n  Continue anyway? (y/N): ").strip().lower()
        except EOFError:
            ans = 'n'
        if ans != 'y':
            print("  Exit.")
            sys.exit(1)

    # ── Основной цикл ──
    while True:
        choice = show_menu(file1, file2, cfg_results, s2, s3)

        if choice == '0':
            print()
            print("  [OK] Goodbye!")
            print()
            sys.exit(0)

        if choice == '1':
            if not s2:
                print("  [X] migrate_to_vrrp2.py not found.")
                continue
            rc = run_script(s2, file1, file2)
            _show_rc(rc, 'migrate_to_vrrp2.py')

        elif choice == '2':
            if not s3:
                print("  [X] migrate_to_vrrp3.py not found.")
                continue
            rc = run_script(s3, file1, file2)
            _show_rc(rc, 'migrate_to_vrrp3.py')

        # Возврат в меню
        print()
        try:
            ans = input("  Press Enter to return to menu (or n to exit)... ").strip().lower()
        except EOFError:
            ans = 'n'
        if ans == 'n':
            print("  Goodbye!")
            sys.exit(0)
        # Если нажат Enter — цикл while True начнется заново


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  [!] Interrupted by user.")
        sys.exit(130)
