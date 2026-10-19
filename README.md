<p align="center">
  <img src="logo.png" alt="hsrp2vrrp — HSRP → VRRP Migration Toolkit" width="480"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.6%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Cisco-IOS%20%7C%20IOS--XE-1BA0D7?style=for-the-badge&logo=cisco&logoColor=white" alt="Cisco"/>
  <img src="https://img.shields.io/badge/VRRP-v2%20%7C%20v3-success?style=for-the-badge" alt="VRRP"/>
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge" alt="License"/>
</p>

<p align="center">
  <b>Автоматическая генерация команд для плавного перехода с HSRP на VRRPv2 / VRRPv3 на двух ядрах сети.</b><br/>
  Универсальный лаунчер, последовательное применение, минимизация разрыва, поддержка аутентификации, перенос track-объектов.
</p>

---

## 📖 Содержание

- [О проекте](#-о-проекте)
- [Возможности](#-возможности)
- [Требования](#-требования)
- [Быстрый старт](#-быстрый-старт)
- [Универсальный лаунчер](#-универсальный-лаунчер--hsrp2vrrppy)
- [Подготовка](#-подготовка)
- [Использование](#-использование)
- [Пример вывода](#-пример-вывода)
- [Структура проекта](#-структура-проекта)
- [Важные замечания](#️-важные-замечания)
- [FAQ](#-faq)
- [Лицензия](#-лицензия)

---

## 🎯 О проекте

Набор из двух Python-скриптов, которые анализируют конфигурации двух ядер сети (active / standby), находят общие VLAN, группы HSRP и track-объекты и генерируют готовую последовательность команд для перевода резервирования шлюза на **VRRPv2** или **VRRPv3**.

Скрипты определяют, какое ядро является активным (по приоритету HSRP, а при равенстве — по IP-адресу интерфейса), **переносят track-и в той же группе и на том же интерфейсе**, где они были в HSRP, и формируют команды в правильном порядке:

> 🟢 **Сначала standby-ядро** → 🔵 **затем active-ядро**

Такой порядок позволяет минимизировать простой хостов в сегменте.

В комплекте идёт **универсальный лаунчер `hsrp2vrrp.py`**, проверяет наличие конфигов и скриптов миграции и предлагает меню выбора — VRRPv2, VRRPv3 или выход.

При запуске скрипты выводят:

1. **Статистику**: сколько HSRP-групп найдено, сколько общих групп, сколько и какие будут переведены в VRRP, сколько track-ов перенесено.
2. **Сгенерированный конфиг** (также сохраняется в файл).

---

## ✨ Возможности

| Возможность | VRRPv2 | VRRPv3 |
|---|:---:|:---:|
| **Универсальный лаунчер с меню выбора** | ✅ | ✅ |
| Автопарсинг конфигов HSRP | ✅ | ✅ |
| Определение active/standby ядра | ✅ | ✅ |
| Последовательный вывод (standby → active) | ✅ | ✅ |
| **Перенос track-объектов / track-интерфейсов** | ✅ | ✅ |
| Выбор аутентификации (text / md5) | ✅ | ❌ *(Cisco не поддерживает)* |
| Глобальная команда `fhrp version vrrp v3` | — | ✅ |
| Настройка `address-family ipv4` | — | ✅ |
| Настройка `ip ospf cost` | ✅ | ✅ |
| Preempt delay `180` сек | ✅ | ✅ |
| Приоритеты `110` / `105` | ✅ | ✅ |
| Статистика миграции при запуске | ✅ | ✅ |

- **Универсальный лаунчер** — `hsrp2vrrp.py` проверяет наличие `core1.txt` / `core2.txt` и скриптов миграции, затем предлагает интерактивное меню.
- **Автопарсинг HSRP** — автоматически находит VLAN, группы HSRP и track-и в конфигах обоих ядер. Не нужно вручную выписывать VIP и приоритеты.
- **Определение ролей** — ядро с большим приоритетом HSRP считается active. При равенстве сравниваются IP-адреса интерфейсов.
- **Перенос track** — track-и из HSRP (`standby <g> track ...`) переносятся в VRRP в той же группе:
  - VRRPv2: `vrrp <g> track ...`
  - VRRPv3: `track ...` внутри `vrrp <g> address-family ipv4`
- **Последовательный вывод** — для каждого VLAN команды выводятся в порядке standby → active. Это минимизирует простой хостов.
- **Аутентификация VRRPv2** — интерактивный выбор: без аутентификации, текстовая или MD5. Единый ключ применяется к обоим ядрам.
- **VRRPv3 из коробки** — глобальная команда `fhrp version vrrp v3` и настройка `address-family ipv4`.
- **OSPF cost** — автоматическая установка стоимости OSPF: 1 для active, 10 для standby.
- **Статистика** — при запуске выводится подробная статистика по миграции.

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
> sudo apt update && sudo apt install python-is-python3
> ```

---

## 🚀 Быстрый старт

```bash
# Клонируем репозиторий
git clone https://github.com/landev-ru/hsrp2vrrp.git
cd hsrp2vrrp

# Способ 1 (рекомендуется) — универсальный лаунчер
python3 hsrp2vrrp.py

# Способ 2 — напрямую
python3 migrate_to_vrrp2.py core1.txt core2.txt
python3 migrate_to_vrrp3.py core1.txt core2.txt
```

На выходе появится файл `migrate_vrrp2_sequential.cfg` или `migrate_vrrp3_sequential.cfg` с готовыми командами.

### Альтернативный запуск (без вызова интерпретатора)

```bash
chmod +x hsrp2vrrp.py migrate_to_vrrp2.py migrate_to_vrrp3.py

./hsrp2vrrp.py
./migrate_to_vrrp2.py core1.txt core2.txt
./migrate_to_vrrp3.py core1.txt core2.txt
```

---

## 🎛 Универсальный лаунчер — `hsrp2vrrp.py`

Скрипт-обёртка, которая упрощает работу с проектом:

1. **Проверяет конфиги** `core1.txt` и `core2.txt` (наличие, права чтения, размер).
2. **Ищет скрипты миграции** `migrate_to_vrrp2.py` и `migrate_to_vrrp3.py` рядом с собой (и в `PATH`).
3. Показывает **меню выбора**:

```text
======================================================================
ГЛАВНОЕ МЕНЮ
======================================================================
1 — Перейти на VRRPv2  (migrate_to_vrrp2.py)
2 — Перейти на VRRPv3  (migrate_to_vrrp3.py)
0 — Выход
======================================================================
Ваш выбор (0/1/2):
```

4. Запускает выбранный скрипт через `subprocess` и возвращается в меню по завершении.
5. Корректно обрабатывает `Ctrl+C` и отсутствие файлов.

### Использование

```bash
# по умолчанию ищет core1.txt и core2.txt в текущей папке
python3 hsrp2vrrp.py

# или с явными путями к конфигам
python3 hsrp2vrrp.py /path/core1.txt /path/core2.txt
```

> ℹ️ Если конфиги не найдены, лаунчер подскажет команды экспорта и предложит продолжить или выйти.

---

## 🛠 Подготовка

> ⚠️ **Перед началом работ** обязательно выполните следующие шаги.

### 1. Резервное копирование конфигураций

```cisco
copy running-config startup-config
copy startup-config flash:backup_core1.cfg
copy startup-config flash:backup_core2.cfg
```

### 2. Проверка поддержки VRRP

```cisco
show vrrp
show vrrp brief
```

Для VRRPv3 убедитесь, что доступна команда:

```cisco
fhrp version vrrp v3
```

### 3. Проверка ACL

Убедитесь, что списки доступа на интерфейсах **пропускают служебные пакеты VRRP**:

| Протокол | IP-протокол | Multicast-адрес |
|---|---|---|
| VRRPv2 | 112 | `224.0.0.18` |
| VRRPv3 | 112 | `224.0.0.18`, `ff02::12` |

### 4. Определение критичных сегментов

Для технологических и инфраструктурных ИУС/ИнфПАК выделите **отдельное окно обслуживания** — переход на VRRP вызывает кратковременный разрыв (смена виртуального MAC, обновление ARP).

### 5. Экспорт конфигураций

Сохраните вывод `show running-config` обоих ядер в файлы `core1.txt` и `core2.txt`:

```bash
ssh admin@core1 "show run" > core1.txt
ssh admin@core2 "show run" > core2.txt
```

Либо вручную с консоли:

```cisco
show running-config
! скопировать вывод в файл core1.txt / core2.txt
```

---

## 📘 Использование

Три способа запуска: через лаунчер или напрямую каждый из скриптов.

### 🔹 VRRPv2 — `migrate_to_vrrp2.py`

```bash
python3 migrate_to_vrrp2.py core1.txt core2.txt
```

Скрипт выведет статистику и интерактивно запросит тип аутентификации:

```text
Выберите тип аутентификации для VRRPv2:
1 - Без аутентификации
2 - Текстовая аутентификация (text)
3 - MD5 аутентификация (md5)
Ваш выбор (1/2/3):
```

| Выбор | Действие |
|:---:|---|
| `1` | Аутентификация не добавляется |
| `2` | Запрос текстового ключа → `vrrp <g> authentication text <key>` |
| `3` | Запрос MD5-ключа → `vrrp <g> authentication md5 key-string <key>` |

**Формируемые команды:**

```cisco
interface VlanX
 no standby <group>
 vrrp <group> ip <VIP>
 vrrp <group> preempt delay minimum 180
 vrrp <group> priority 110              ! 105 для standby
 vrrp <group> track <...>               ! если был track в HSRP
 vrrp <group> authentication ...        ! если выбрана
 ip ospf cost 1                         ! 10 для standby
```

---

### 🔹 VRRPv3 — `migrate_to_vrrp3.py`

```bash
python3 migrate_to_vrrp3.py core1.txt core2.txt
```

Аутентификация **не используется** — Cisco не поддерживает её в VRRPv3 (RFC 5798).

**Формируемые команды:**

```cisco
fhrp version vrrp v3
!
interface VlanX
 no standby <group>
 vrrp <group> address-family ipv4
  address <VIP> primary
  priority 110                 ! 105 для standby
  timers advertise 5000
  track <...>                  ! если был track в HSRP
  preempt delay minimum 180
 exit
 ip ospf cost 1                ! 10 для standby
```

> ℹ️ В VRRPv3 команда `track` размещается **внутри** блока `address-family ipv4`.

---

### 🔄 Порядок применения

Для **каждого VLAN** применяйте команды в следующей последовательности:

```text
┌─────────────────────────────────────┐
│  1. Блок Standby-ядра               │
│         ↓                           │
│  2. Проверка: show vrrp brief       │
│         ↓                           │
│  3. Блок Active-ядра                │
│         ↓                           │
│  4. Проверка: show vrrp / ping VIP  │
└─────────────────────────────────────┘
```

Только после успешной проверки переходите к следующему VLAN.

---

## 📋 Пример вывода

### Пример статистики при запуске

```text
//
//░▒▓█▓▒░         ░▒▓██████▓▒░  ░▒▓███████▓▒░  ░▒▓███████▓▒░  ░▒▓████████▓▒░ ░▒▓█▓▒░░▒▓█▓▒░
//░▒▓█▓▒░        ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░        ░▒▓█▓▒░░▒▓█▓▒░
//░▒▓█▓▒░        ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░         ░▒▓█▓▒▒▓█▓▒░
//░▒▓█▓▒░        ░▒▓████████▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓██████▓▒░    ░▒▓█▓▒▒▓█▓▒░
//░▒▓█▓▒░        ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░          ░▒▓█▓▓█▓▒░
//░▒▓█▓▒░        ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░          ░▒▓█▓▓█▓▒░
//░▒▓████████▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓███████▓▒░  ░▒▓████████▓▒░    ░▒▓██▓▒░
//
//Created by LanDev
//https://github.com/landev-ru/Starlabix
//Contacts - fraso1989@gmail.com / Fraso@mail.ru

Выберите тип аутентификации для VRRPv2:
1 - Без аутентификации
2 - Текстовая аутентификация (text)
3 - MD5 аутентификация (md5)
Ваш выбор (1/2/3): 3
Введите MD5 ключ: MySecretKey

======================================================================
  СТАТИСТИКА
======================================================================
  Файл 1:                              core1.txt
  Файл 2:                              core2.txt
  Общих интерфейсов:                   12
  Найдено HSRP-групп (всего):          14
  Общих групп (в обоих ядрах):         12
  Будет переведено в VRRP:             12
  Track-ов будет перенесено:           8

  Планируемые к миграции:
    - Vlan2: group 2
    - Vlan3: group 3
    - Vlan10: group 10
    - Vlan20: group 20
    - Vlan30: group 30
    - Vlan40: group 40
    - Vlan50: group 50
    - Vlan60: group 60
    - Vlan70: group 70
    - Vlan80: group 80
    - Vlan90: group 90
    - Vlan100: group 100
======================================================================
```

### Пример сгенерированного файла `migrate_vrrp2_sequential.cfg`

```cisco
# Поочередный перевод HSRP -> VRRPv2 для ядра
# Порядок: сначала standby, затем active для каждого VLAN.
# Аутентификация: md5 (ключ: MySecretKey)

# ========== Vlan2 (group 2) ==========
# --- Standby core (core2.txt) ---
interface Vlan2
 no standby 2
 vrrp 2 ip 10.80.68.1
 vrrp 2 preempt delay minimum 180
 vrrp 2 priority 105
 vrrp 2 track 1 decrement 20
 vrrp 2 authentication md5 key-string MySecretKey
 ip ospf cost 10
!

# --- Active core (core1.txt) ---
interface Vlan2
 no standby 2
 vrrp 2 ip 10.80.68.1
 vrrp 2 preempt delay minimum 180
 vrrp 2 priority 110
 vrrp 2 track 1 decrement 20
 vrrp 2 authentication md5 key-string MySecretKey
 ip ospf cost 1
!
```

### Пример сгенерированного файла `migrate_vrrp3_sequential.cfg`

```cisco
# Поочередный перевод HSRP -> VRRPv3 для ядра
# Глобальная команда: fhrp version vrrp v3
# ВНИМАНИЕ: VRRPv3 не поддерживает аутентификацию (RFC 5798).
# Если требуется аутентификация, используйте VRRPv2.

fhrp version vrrp v3
!

# ========== Vlan2 (group 2) ==========
# --- Standby core (core2.txt) ---
interface Vlan2
 no standby 2
 vrrp 2 address-family ipv4
  address 10.80.68.1 primary
  priority 105
  timers advertise 5000
  track 1 decrement 20
  preempt delay minimum 180
 exit
 ip ospf cost 10
!

# --- Active core (core1.txt) ---
interface Vlan2
 no standby 2
 vrrp 2 address-family ipv4
  address 10.80.68.1 primary
  priority 110
  timers advertise 5000
  track 1 decrement 20
  preempt delay minimum 180
 exit
 ip ospf cost 1
!
```

---

## 📁 Структура проекта

```text
hsrp2vrrp/
├── hsrp2vrrp.py                 # Универсальный лаунчер (меню выбора)
├── migrate_to_vrrp2.py          # Скрипт для VRRPv2
├── migrate_to_vrrp3.py          # Скрипт для VRRPv3
├── core1.txt                    # Пример конфига первого ядра
├── core2.txt                    # Пример конфига второго ядра
├── migrate_vrrp2_sequential.cfg # Результат (генерируется)
├── migrate_vrrp3_sequential.cfg # Результат (генерируется)
├── logo.png                     # Логотип проекта
├── index.html                   # Страница проекта (GitHub Pages)
└── README.md
```

---

## ⚠️ Важные замечания

> 🔴 **Аутентификация**
> - VRRPv2 поддерживает текстовую и MD5-аутентификацию.
> - VRRPv3 **не поддерживает** аутентификацию (RFC 5798). Если она критична — используйте VRRPv2.

> ◉ **Ключи HSRP**
> В исходных конфигах ключи HSRP могут различаться. Скрипт для VRRPv2 **игнорирует** их и использует ключ, введённый вами вручную — единый для обоих ядер.

> ◉ **Виртуальный MAC**
> VRRP использует MAC `0000.5e00.01xx`, отличный от HSRP. Это вызовет обновление ARP-таблиц на хостах и кратковременный разрыв (несколько секунд на VLAN).

> 🟢 **Track-объекты**
> Скрипт переносит track-и из HSRP в VRRP **в том же блоке группы**. Поддерживаются как object-tracking (`track 1 decrement 20`), так и interface-tracking (`track GigabitEthernet0/0 10`). Синтаксис сохраняется «как есть».

> 🔵 **OSPF cost**
> По умолчанию: `1` для active, `10` для standby. При необходимости скорректируйте значения в скрипте.

> ◉ **Preempt delay**
> Установлена задержка `180` секунд для предотвращения частых переключений ролей.

> 🎛 **Расположение лаунчера**
> `hsrp2vrrp.py` ищет `migrate_to_vrrp2.py` / `migrate_to_vrrp3.py` **рядом с собой** (и в `PATH`). Держите все три скрипта в одной папке.

> ⚫ **Проверка синтаксиса**
> Синтаксис VRRP может отличаться в зависимости от версии IOS/IOS-XE. **Перед массовым применением протестируйте на одном VLAN**.

---

## ❓ FAQ

<details>
<summary><b>Почему команда <code>python</code> не найдена?</b></summary>

В современных Linux-дистрибутивах (Ubuntu 20.04+, Debian 11+) команда `python` отсутствует. Используйте `python3`:

```bash
python3 hsrp2vrrp.py
```

Либо установите псевдоним:

```bash
sudo apt install python-is-python3
```

После этого команда `python` будет работать как `python3`.
</details>

<details>
<summary><b>Чем отличается запуск через <code>hsrp2vrrp.py</code> от прямого?</b></summary>

Лаунчер `hsrp2vrrp.py` — это удобная обёртка: проверяет наличие конфигов и скриптов, показывает меню и запускает нужный скрипт через `subprocess`. Прямой запуск `migrate_to_vrrp2.py` / `migrate_to_vrrp3.py` работает так же, но без проверки и меню. Функционально результат идентичен.
</details>

<details>
<summary><b>Что делать, если лаунчер не находит конфиги?</b></summary>

Экспортируйте конфиги в текущую папку:

```bash
ssh admin@core1 "show run" > core1.txt
ssh admin@core2 "show run" > core2.txt
```

Либо передайте пути аргументами:

```bash
python3 hsrp2vrrp.py /path/core1.txt /path/core2.txt
```

Лаунчер также позволяет продолжить без конфигов (с предупреждением) — на ваш выбор.
</details>

<details>
<summary><b>Что делать, если ключи HSRP на ядрах различались?</b></summary>

Скрипт `migrate_to_vrrp2.py` игнорирует исходные ключи HSRP. Вы вводите единый ключ вручную, и он применяется к обоим ядрам. Это гарантирует совместимость.
</details>

<details>
<summary><b>Почему в VRRPv3 нет аутентификации?</b></summary>

Протокол VRRPv3 (RFC 5798) не предусматривает механизмов аутентификации. Если аутентификация обязательна — используйте VRRPv2.
</details>

<details>
<summary><b>Как переносятся track-и?</b></summary>

Скрипт находит строки `standby <group> track ...` в конфигах HSRP и сохраняет всё, что идёт после `track`. При генерации VRRP:

- **VRRPv2:** `vrrp <group> track <...>` — в том же блоке интерфейса/группы.
- **VRRPv3:** `track <...>` — внутри `vrrp <group> address-family ipv4`.

Поддерживаются оба варианта:

- object-tracking: `track 1 decrement 20`
- interface-tracking: `track GigabitEthernet0/0 10`
</details>

<details>
<summary><b>Как определить, какое ядро active, а какое standby?</b></summary>

Скрипт сравнивает приоритеты HSRP (`standby <g> priority`). Выше приоритет — active. При равенстве — сравниваются IP-адреса интерфейсов: больше IP = active.
</details>

<details>
<summary><b>Можно ли применить всё сразу, не по одному VLAN?</b></summary>

Технически можно, но это приведёт к длительному разрыву на всех сегментах одновременно. Рекомендуется применять **поочерёдно**, с проверкой после каждого VLAN.
</details>

<details>
<summary><b>Как сделать скрипты исполняемыми?</b></summary>

```bash
chmod +x hsrp2vrrp.py migrate_to_vrrp2.py migrate_to_vrrp3.py
```

Затем запускать напрямую:

```bash
./hsrp2vrrp.py
./migrate_to_vrrp2.py core1.txt core2.txt
./migrate_to_vrrp3.py core1.txt core2.txt
```

Убедитесь, что в начале скриптов есть строка:

```python
#!/usr/bin/env python3
```
</details>

---

## 📄 Лицензия

Проект распространяется под лицензией **MIT**.

Скрипты предоставляются **«как есть»**. Автор не несёт ответственности за возможные сбои. Всегда тестируйте на стенде перед применением в production.

---
