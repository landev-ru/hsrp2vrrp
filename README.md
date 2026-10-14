# 🔄 HSRP → VRRP Migration Toolkit

<p align="center">
  <img src="https://img.shields.io/badge/python-3.6%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Cisco-IOS%20%7C%20IOS--XE-1BA0D7?style=for-the-badge&logo=cisco&logoColor=white" alt="Cisco"/>
  <img src="https://img.shields.io/badge/VRRP-v2%20%7C%20v3-success?style=for-the-badge" alt="VRRP"/>
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge" alt="License"/>
</p>

<p align="center">
  <b>Автоматическая генерация команд для плавного перехода с HSRP на VRRPv2 / VRRPv3 на двух ядрах сети.</b><br/>
  Минимизация простоя, последовательное применение, поддержка аутентификации.
</p>

---

## 📖 Содержание

- [О проекте](#-о-проекте)
- [Возможности](#-возможности)
- [Требования](#-требования)
- [Быстрый старт](#-быстрый-старт)
- [Подготовка](#-подготовка)
- [Использование](#-использование)
- [Пример вывода](#-пример-вывода)
- [Структура проекта](#-структура-проекта)
- [Важные замечания](#️-важные-замечания)
- [FAQ](#-faq)
- [Лицензия](#-лицензия)

---

## 🎯 О проекте

Набор из двух Python-скриптов, которые анализируют конфигурации двух ядер сети (active / standby), находят общие VLAN и группы HSRP и генерируют готовую последовательность команд для перевода резервирования шлюза на **VRRPv2** или **VRRPv3**.

Скрипты определяют, какое ядро является активным (по приоритету HSRP, а при равенстве — по IP-адресу интерфейса) и формируют команды в правильном порядке:

> 🟢 **Сначала standby-ядро** → 🔵 **затем active-ядро**

Такой порядок позволяет минимизировать простой хостов в сегменте.

---

## ✨ Возможности

| Возможность | VRRPv2 | VRRPv3 |
|---|:---:|:---:|
| Автопарсинг конфигов HSRP | ✅ | ✅ |
| Определение active/standby ядра | ✅ | ✅ |
| Последовательный вывод (standby → active) | ✅ | ✅ |
| Выбор аутентификации (text / md5) | ✅ | ❌ *(Cisco не поддерживает)* |
| Глобальная команда `fhrp version vrrp v3` | — | ✅ |
| Настройка `address-family ipv4` | — | ✅ |
| Настройка `ip ospf cost` | ✅ | ✅ |
| Preempt delay `180` сек | ✅ | ✅ |
| Приоритеты `110` / `105` | ✅ | ✅ |

---

## 📦 Требования

- **Python** `3.6+` (команда `python3`)
- Два текстовых файла с конфигурациями ядер:
  - `core1.txt`
  - `core2.txt`
- Оборудование Cisco с поддержкой VRRP:
  - для VRRPv3 — команда `fhrp version vrrp v3` в глобальном режиме.

> ℹ️ В современных Linux-дистрибутивах (Ubuntu 20.04+, Debian 11+) команда `python` отсутствует. Используйте `python3`. При необходимости можно установить псевдоним:
>
> ```bash
> sudo apt install python-is-python3
> ```

---

## 🚀 Быстрый старт

```bash
# Клонируем репозиторий
git clone https://github.com/your-org/hsrp2vrrp.git
cd hsrp2vrrp

# VRRPv2 (с выбором аутентификации)
python3 migrate_to_vrrp2.py core1.txt core2.txt

# VRRPv3 (без аутентификации)
python3 migrate_to_vrrp3.py core1.txt core2.txt
