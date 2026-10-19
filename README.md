<p align="center">
<img src="https://raw.githubusercontent.com/landev-ru/hsrp2vrrp/gh-pages/logo.png" alt="hsrp2vrrp — HSRP → VRRP Migration Toolkit" width="480"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.6%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Cisco-IOS%20%7C%20IOS--XE-1BA0D7?style=for-the-badge&logo=cisco&logoColor=white" alt="Cisco"/>
  <img src="https://img.shields.io/badge/VRRP-v2%20%7C%20v3-success?style=for-the-badge" alt="VRRP"/>
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge" alt="License"/>
</p>

<p align="center">
  <a href="#-русский"><img src="https://img.shields.io/badge/🇷🇺-Русский-2563eb?style=for-the-badge" alt="Русский"/></a>
  &nbsp;
  <a href="#-english"><img src="https://img.shields.io/badge/🇬🇧-English-6b7280?style=for-the-badge" alt="English"/></a>
</p>

<p align="center">
  <b>Планируемая миграция FHRP с HSRP на VRRPv2 / VRRPv3 на паре ядерных коммутаторов Cisco.</b><br/>
  <b>Planned FHRP migration from HSRP to VRRPv2 / VRRPv3 on a pair of Cisco core switches.</b>
</p>

---

<a id="-русский"></a>

# 🇷🇺 Русский

<p align="center">
  <a href="#-english"><img src="https://img.shields.io/badge/→_English-6b7280?style=for-the-badge" alt="English"/></a>
</p>

Набор инструментов для планируемой миграции FHRP с HSRP на VRRPv2 / VRRPv3 на паре ядерных коммутаторов Cisco. Полный разбор конфигураций, определение ролей active/standby, перенос track-объектов, интерактивная настройка аутентификации и пошаговая стратегия применения без массового простоя.

---

## 📖 Содержание (RU)

- [Назначение и область применения](#-назначение-и-область-применения)
- [Архитектура и принцип работы](#-архитектура-и-принцип-работы)
- [Возможности](#-возможности)
- [Требования](#-требования)
- [Быстрый старт](#-быстрый-старт)
- [Универсальный лаунчер — hsrp2vrrp.py](#-универсальный-лаунчер--hsrp2vrrppy)
- [Подготовка к миграции](#-подготовка-к-миграции)
- [Использование](#-использование)
- [Стратегия миграции](#-стратегия-миграции)
- [Проверка после миграции](#-проверка-после-миграции)
- [План отката](#-план-отката)
- [Пример вывода](#-пример-вывода)
- [Структура проекта](#-структура-проекта)
- [Важные замечания и ограничения](#️-важные-замечания-и-ограничения)
- [Матрица совместимости](#-матрица-совместимости)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq)
- [Лицензия](#-лицензия)

---

## 🎯 Назначение и область применения

Проект предназначен для сетевых инженеров, планирующих **плановую миграцию протокола резервирования первого хопа (FHRP)** с проприетарного Cisco HSRP на открытый VRRP (RFC 3768 / RFC 5798). Задача возникает при:

- переходе на вендор-независимую архитектуру;
- унификации политики FHRP в смешанной инфраструктуре;
- выполнении требований импортозамещения и перехода на открытые стандарты;
- подготовке к миграции на сторонние платформы (Arista, Juniper, Huawei, NX-OS), где HSRP либо не поддерживается, либо ограничен.

Инструмент решает три прикладные задачи:

1. **Автоматический анализ** двух конфигураций (`show running-config` с ядер core1 и core2): поиск общих VLAN, групп HSRP, VIP, приоритетов, `track`-объектов.
2. **Определение ролей active / standby** для каждой группы HSRP согласно правилам протокола.
3. **Генерация готовой последовательности команд VRRPv2 или VRRPv3** в порядке, минимизирующем простой хостов: сначала standby-ядро, затем active.

В комплекте идёт **обёртка `hsrp2vrrp.py`**, которая валидирует окружение (наличие конфигов и дочерних скриптов), отображает интерактивное меню выбора версии VRRP и возвращает управление по завершении миграции.

---

## 🔬 Архитектура и принцип работы

### Определение ролей active / standby

Алгоритм повторяет выбор active-роутера по правилам HSRP (RFC 2281):

1. Сравниваются **приоритеты** `standby <group> priority`:
   - более высокий приоритет → active;
   - при равенстве (или отсутствии явного указания — по умолчанию `100`) переходим к шагу 2.
2. Сравниваются **IP-адреса физических интерфейсов** (`ip address` на VLAN-интерфейсе): большее значение → active.
3. Если IP-адреса не найдены, ядро `core1` считается active по умолчанию.

Такая логика гарантирует **преемственность ролей**: тот же роутер, который был HSRP-active, становится VRRP-мастером после миграции.

### Порядок вывода команд

Для каждой группы HSRP в общем VLAN генерируется блок из двух частей:

```text
┌──────────────────────────────────────┐
│ 1. Блок Standby-ядра                 │  ← Применяется первым
│    ↓                                 │
│ 2. Проверка: show vrrp brief         │
│    ↓                                 │
│ 3. Блок Active-ядра                  │  ← Применяется вторым
│    ↓                                 │
│ 4. Проверка: show vrrp / ping VIP    │
└──────────────────────────────────────┘
```

**Почему именно так:**

- Первым переводится standby. После применения его команды (и снятия HSRP у обеих сторон), он становится VRRP-мастером — VIP временно переезжает на него.
- Затем переводится active, у которого приоритет VRRP выше. С включённым `preempt delay minimum 180` он вернёт себе мастер-роль через 180 секунд — без флаппинга.
- Простой в сегменте ограничивается обновлением ARP-таблиц (несколько секунд), а не полной потерей шлюза.

### Перенос track-объектов

Строки вида `standby <group> track <...>` анализируются и переносятся без изменения синтаксиса:

| HSRP | VRRPv2 | VRRPv3 |
|---|---|---|
| `standby 2 track 1 decrement 20` | `vrrp 2 track 1 decrement 20` | `track 1 decrement 20` (внутри `address-family ipv4`) |
| `standby 2 track GigabitEthernet0/0 10` | `vrrp 2 track GigabitEthernet0/0 10` | `track GigabitEthernet0/0 10` |

Поддерживаются оба варианта track:

- **object-tracking** — ссылка на IP SLA / object с decrement;
- **interface-tracking** — отслеживание состояния интерфейса с decrement.

### OSPF cost и preempt delay

| Параметр | Active-ядро | Standby-ядро |
|---|---|---|
| `ip ospf cost` | `1` | `10` |
| `vrrp priority` | `110` | `105` |
| `preempt delay minimum` | `180` сек | `180` сек |

- **OSPF cost 1/10** гарантирует, что при равных условиях трафик пойдёт через active-ядро.
- **Preempt delay 180** защищает от флаппинга ролей.

---

## ✨ Возможности

| Возможность | VRRPv2 | VRRPv3 |
|---|:---:|:---:|
| Универсальный лаунчер с меню выбора | ✅ | ✅ |
| Автопарсинг HSRP, VIP и приоритетов | ✅ | ✅ |
| Определение active / standby по RFC 2281 | ✅ | ✅ |
| Последовательный вывод команд (standby → active) | ✅ | ✅ |
| **Перенос track-объектов / interface-tracking** | ✅ | ✅ |
| Интерактивная настройка аутентификации | ✅ | ❌ *(не поддерживается Cisco)* |
| Глобальная команда `fhrp version vrrp v3` | — | ✅ |
| Настройка `address-family ipv4` | — | ✅ |
| Автоматический `ip ospf cost` | ✅ | ✅ |
| `preempt delay minimum 180` | ✅ | ✅ |
| Приоритеты `110` / `105` | ✅ | ✅ |
| Подробная статистика миграции | ✅ | ✅ |

---

## 📦 Требования

- **Python** `3.6+` (команда `python3`)
- Два текстовых файла с конфигурациями ядер: `core1.txt`, `core2.txt`
- Оборудование Cisco с поддержкой VRRP:
  - для VRRPv3 — команда `fhrp version vrrp v3` в глобальном режиме.
- Соответствие версии IOS/IOS-XE поддерживаемым платформам (см. [Матрица совместимости](#-матрица-совместимости)).

> ℹ️ В современных Linux-дистрибутивах (Ubuntu 20.04+, Debian 11+) команда `python` отсутствует. Используйте `python3`. При необходимости установите псевдоним:
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

Обёртка, упрощающая работу с проектом:

1. **Проверяет конфиги** `core1.txt` и `core2.txt` (наличие, права чтения, ненулевой размер).
2. **Ищет скрипты миграции** `migrate_to_vrrp2.py` и `migrate_to_vrrp3.py` рядом с собой (и в `PATH`).
3. Отображает **меню выбора**:

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

4. Запускает выбранный скрипт через `subprocess` (наследует stdin/stdout/stderr — интерактивный ввод работает).
5. Возвращает управление в меню после завершения — удобно для повторных прогонов.
6. Корректно обрабатывает `Ctrl+C` (код выхода `130`) и отсутствие файлов (код `1`).

### Использование

```bash
# по умолчанию ищет core1.txt и core2.txt в текущей папке
python3 hsrp2vrrp.py

# или с явными путями
python3 hsrp2vrrp.py /path/core1.txt /path/core2.txt
```

> ℹ️ Если конфиги не найдены, лаунчер выведет подсказку с командами экспорта и предложит продолжить или выйти.

---

## 🛠 Подготовка к миграции

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

Для VRRPv3:

```cisco
fhrp version vrrp v3
```

### 3. Проверка ACL

| Протокол | IP-протокол | Multicast-адрес |
|---|---|---|
| VRRPv2 | 112 | `224.0.0.18` |
| VRRPv3 | 112 | `224.0.0.18`, `ff02::12` |

### 4. Определение критичных сегментов

Для технологических и инфраструктурных ИУС/ИнфПАК выделите **отдельное окно обслуживания** — переход на VRRP вызывает кратковременный разрыв (смена виртуального MAC, обновление ARP).

### 5. Экспорт конфигураций

```bash
ssh admin@core1 "show run" > core1.txt
ssh admin@core2 "show run" > core2.txt
```

### 6. Снимок текущего состояния (baseline)

```cisco
show standby brief
show standby all
show ip ospf neighbor
show ip route summary
show track
```

---

## 📘 Использование

### 🔹 VRRPv2 — `migrate_to_vrrp2.py`

```bash
python3 migrate_to_vrrp2.py core1.txt core2.txt
```

Скрипт интерактивно запросит тип аутентификации:

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

## 🗺 Стратегия миграции

Пошаговый сценарий для одного VLAN. Повторяется для каждого VLAN, начиная с наименее критичных.

### Фаза 1. Подготовка (без изменений в конфиге)

1. Сохранить baseline: `show standby brief`, `show ip ospf neighbor`, `show ip route summary`, `show track`.
2. Убедиться, что ACL пропускают IP-протокол 112 на multicast `224.0.0.18`.
3. Проверить `show vrrp brief`.
4. Согласовать окно обслуживания для критичного сегмента.

### Фаза 2. Применение блока Standby-ядра

1. Войти на standby-ядро (для VLAN).
2. Применить блок из секции `# --- Standby core ---`.
3. Проверить: `show vrrp brief` — группа должна появиться в состоянии Master.
4. Проверить связность: с тестового хоста `ping <VIP>` — стабильно (возможны кратковременные потери 1–3 пакета).

### Фаза 3. Применение блока Active-ядра

1. Войти на active-ядро (для VLAN).
2. Применить блок из секции `# --- Active core ---`.
3. Проверить: `show vrrp brief` — на active-ядре статус Master, на standby — Backup.
4. `preempt delay minimum 180` вступает в силу — в течение 3 минут возможен Backup на active.

### Фаза 4. Верификация и документирование

1. `show vrrp brief` на обоих ядрах — роли соответствуют pre-migration.
2. `ping <VIP>` с нескольких хостов VLAN — стабильно.
3. `show track` — объекты Up.
4. `show ip ospf neighbor` — соседство через VIP восстановлено.
5. Зафиксировать результат в журнале изменений.

### Фаза 5. Переход к следующему VLAN

Только после успешной верификации. **Не параллелить** — это единственный способ гарантировать ограниченный blast-radius.

---

## ✅ Проверка после миграции

| Проверка | Команда | Ожидание |
|---|---|---|
| Роль VRRP | `show vrrp brief` | на active-ядре — Master, на standby — Backup |
| VIP активен | `ping <VIP>` с хоста | 0% loss после стабилизации |
| Track-объекты | `show track` | все Up |
| OSPF-соседство | `show ip ospf neighbor` | Full/2-Way |
| Маршрутизация | `show ip route summary` | маршруты через VIP живы |
| ARP/MAC | `show ip arp <VIP>` | MAC `0000.5e00.01xx` |
| Preempt | `show vrrp <group>` | `preempt delay minimum 180` |
| Аутентификация (v2) | `show vrrp <group>` | метод и ключ соответствуют |
| Логи | `show logging \| include VRRP` | без ошибок протокола |

Если хотя бы один пункт не сходится — перейти к [Плану отката](#-план-отката).

---

## ⏪ План отката

### Откат одного VLAN

```cisco
interface VlanX
 no vrrp <group> address-family ipv4    ! для v3
 ! или
 no vrrp <group> ip <VIP>               ! для v2
 standby <group> ip <VIP>               ! вернуть HSRP
 standby <group> priority <исходный>
 standby <group> preempt               ! если было
 standby <group> track ...             ! вернуть track
 ip ospf cost <исходный>               ! вернуть OSPF cost
```

Порядок: сначала standby-ядро, затем active.

### Полный откат из бэкапа

```cisco
copy flash:backup_core1.cfg running-config
copy flash:backup_core2.cfg running-config
```

### Критерии, при которых откат обязателен

- VIP недоступен более 60 секунд после стабилизации preempt;
- Track-объекты остаются Down дольше 5 минут;
- OSPF-соседство не восстанавливается;
- Потеря пакетов через VIP > 1% в течение 5 минут.

---

## 📋 Пример вывода

### Статистика при запуске

```text
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

### `migrate_vrrp2_sequential.cfg`

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

### `migrate_vrrp3_sequential.cfg`

```cisco
# Поочередный перевод HSRP -> VRRPv3 для ядра
# Глобальная команда: fhrp version vrrp v3
# ВНИМАНИЕ: VRRPv3 не поддерживает аутентификацию (RFC 5798).

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
├── migrate_to_vrrp2.py          # Генератор команд VRRPv2
├── migrate_to_vrrp3.py          # Генератор команд VRRPv3
├── core1.txt                    # Пример конфига ядра core1
├── core2.txt                    # Пример конфига ядра core2
├── migrate_vrrp2_sequential.cfg # Результат (генерируется)
├── migrate_vrrp3_sequential.cfg # Результат (генерируется)
├── logo.png                     # Логотип проекта
├── index.html                   # Страница проекта (GitHub Pages)
└── README.md
```

---

## ⚠️ Важные замечания и ограничения

> 🔴 **Аутентификация**
> - VRRPv2 поддерживает текстовую и MD5-аутентификацию.
> - VRRPv3 **не поддерживает** аутентификацию (RFC 5798).

> ◉ **Ключи HSRP**
> Скрипт для VRRPv2 **игнорирует** их и использует единый ключ, введённый вручную.

> ◉ **Виртуальный MAC**
> VRRP использует MAC `0000.5e00.01xx`, отличный от HSRP (`0000.0c07.acXX`). Возможен кратковременный разрыв (1–5 сек на VLAN). На коммутаторах с port-security/sticky MAC проверьте политику заранее.

> 🟢 **Track-объекты**
> Переносятся в том же блоке группы. Поддерживаются object-tracking и interface-tracking.

> 🔵 **OSPF cost**
> По умолчанию: `1` для active, `10` для standby.

> ◉ **Preempt delay**
> `180` секунд. Для DC — можно `30–60`, для WAN — `300–600`.

> 🎛 **Расположение лаунчера**
> `hsrp2vrrp.py` ищет скрипты миграции **рядом с собой** (и в `PATH`).

> ⚫ **Проверка синтаксиса**
> Синтаксис VRRP может отличаться в зависимости от версии IOS/IOS-XE. **Протестируйте на одном VLAN.**

> 🟡 **Не параллелить**
> Мигрируйте VLAN **поочерёдно**.

> 🔐 **Безопасность**
> MD5-аутентификация VRRPv2 не защищает от перехвата. Для критичных сегментов используйте ACL на `224.0.0.18` / `ff02::12`.

---

## 🧩 Матрица совместимости

| Платформа / версия | VRRPv2 | VRRPv3 | `fhrp version vrrp v3` |
|---|:---:|:---:|:---:|
| Cisco IOS 12.4 | ✅ | ❌ | ❌ |
| Cisco IOS 15.x | ✅ | ✅ | ✅ |
| Cisco IOS-XE 3.x | ✅ | ✅ | ✅ |
| Cisco IOS-XE 16.x / 17.x | ✅ | ✅ | ✅ |
| Cisco NX-OS | ✅ | ✅ | ✅ (через feature) |
| Cisco ASA / FTD | ❌ (только HSRP) | ❌ | ❌ |
| Cisco IOS-XR | ✅ | ✅ | ✅ |

---

## 🔧 Troubleshooting

### VRRP-группа не поднимается

1. `show vrrp` — если `Init`, мастер не выбран.
2. Проверьте одинаковый **VRID** на обоих ядрах.
3. `show vrrp <group> | include State`.
4. `show ip access-lists | include 224.0.0.18` — не блокирует ли.
5. `show logging | include VRRP` — ошибки аутентификации.

### Ошибка аутентификации

```
%VRRP-4-BADAUTH: Bad authentication from 10.80.68.2, group 2
```

- На **обоих ядрах** ключ и метод (text/md5) идентичны.
- MD5-ключ до 20 символов, не обрезан.
- В VRRPv3 аутентификация отсутствует.

### Preempt не работает

- `preempt delay minimum 180` — мастер вернётся **только через 180 секунд**.
- `show vrrp <group> | include Priority` — приоритет выше.
- На некоторых версиях IOS `preempt` по умолчанию выключен.

### Track-объект остаётся Down

- `show track 1` — состояние.
- Объект существует на данном ядре (IP SLA настроен).
- VRRP `track` **не создаёт** объект — ссылается на существующий.

### VIP недоступен после миграции

- `show ip arp <VIP>` — MAC `0000.5e00.01xx`.
- **`no standby <group>`** применилось (иначе обе стороны — мастер).
- `show vrrp brief` — группа не в Init.

### `hsrp2vrrp.py` не находит скрипты

- `migrate_to_vrrp2.py` и `migrate_to_vrrp3.py` в **той же папке**.
- Либо `export PATH="$PATH:/path/to/hsrp2vrrp"`.

---

## ❓ FAQ

<details>
<summary><b>Почему команда <code>python</code> не найдена?</b></summary>

Используйте `python3`:

```bash
python3 hsrp2vrrp.py
```

Либо `sudo apt install python-is-python3`.
</details>

<details>
<summary><b>Чем отличается запуск через <code>hsrp2vrrp.py</code> от прямого?</b></summary>

Лаунчер `hsrp2vrrp.py` проверяет наличие конфигов и скриптов, показывает меню и запускает нужный скрипт через `subprocess`. Прямой запуск работает так же, но без проверок и меню. Результат идентичен.
</details>

<details>
<summary><b>Что делать, если лаунчер не находит конфиги?</b></summary>

Экспортируйте конфиги:

```bash
ssh admin@core1 "show run" > core1.txt
ssh admin@core2 "show run" > core2.txt
```

Или передайте пути:

```bash
python3 hsrp2vrrp.py /path/core1.txt /path/core2.txt
```
</details>

<details>
<summary><b>Почему в VRRPv3 нет аутентификации?</b></summary>

RFC 5798 не предусматривает механизмов аутентификации. Используйте VRRPv2 либо ACL/сегментацию.
</details>

<details>
<summary><b>Как переносятся track-и?</b></summary>

- **VRRPv2:** `vrrp <group> track <...>`
- **VRRPv3:** `track <...>` внутри `vrrp <group> address-family ipv4`

Поддерживаются object-tracking и interface-tracking.
</details>

<details>
<summary><b>Как определить, какое ядро active?</b></summary>

По приоритету HSRP. При равенстве — больше IP = active.
</details>

<details>
<summary><b>Можно ли применить всё сразу?</b></summary>

Технически — да, но это длительный разрыв на всех сегментах. Применяйте поочерёдно.
</details>

<details>
<summary><b>Как сделать скрипты исполняемыми?</b></summary>

```bash
chmod +x hsrp2vrrp.py migrate_to_vrrp2.py migrate_to_vrrp3.py
./hsrp2vrrp.py
```
</details>

---

## 📄 Лицензия

Проект распространяется под лицензией **MIT**.

Скрипты предоставляются **«как есть»**. Автор не несёт ответственности за возможные сбои. Всегда тестируйте на стенде перед применением в production.

<p align="center">
  <a href="#-русский">↑ Наверх (RU)</a> &nbsp;|&nbsp; <a href="#-english">🇬🇧 English version ↓</a>
</p>

---

<a id="-english"></a>

# 🇬🇧 English

<p align="center">
<img src="https://raw.githubusercontent.com/landev-ru/hsrp2vrrp/gh-pages/logo.png" alt="hsrp2vrrp — HSRP → VRRP Migration Toolkit" width="480"/>
</p>

Toolkit for planned FHRP migration from HSRP to VRRPv2 / VRRPv3 on a pair of Cisco core switches. Full configuration analysis, active/standby role detection, track-object transfer, interactive authentication setup, and a step-by-step rollout strategy without mass downtime.

---

## 📖 Table of contents (EN)

- [Purpose and scope](#-purpose-and-scope)
- [Architecture and operation](#-architecture-and-operation)
- [Features](#-features)
- [Requirements](#-requirements)
- [Quickstart](#-quickstart)
- [Universal launcher — hsrp2vrrp.py](#-universal-launcher--hsrp2vrrppy)
- [Migration preparation](#-migration-preparation)
- [Usage](#-usage)
- [Migration strategy](#-migration-strategy)
- [Post-migration verification](#-post-migration-verification)
- [Rollback plan](#-rollback-plan)
- [Sample output](#-sample-output)
- [Project structure](#-project-structure)
- [Important notes and limitations](#️-important-notes-and-limitations)
- [Compatibility matrix](#-compatibility-matrix)
- [Troubleshooting](#-troubleshooting)
- [FAQ](#-faq-1)
- [License](#-license)

---

## 🎯 Purpose and scope

The project is intended for network engineers planning a **scheduled migration of the First Hop Redundancy Protocol (FHRP)** from proprietary Cisco HSRP to open-standard VRRP (RFC 3768 / RFC 5798). Typical scenarios:

- moving to a vendor-neutral architecture;
- unifying FHRP policy in mixed environments;
- meeting open-standard / import-substitution requirements;
- preparing migrations to third-party platforms (Arista, Juniper, Huawei, NX-OS) where HSRP is unsupported or limited.

The tool solves three practical tasks:

1. **Automatic analysis** of two configuration dumps (`show running-config` from core1 and core2): find common VLANs, HSRP groups, VIPs, priorities, and `track` objects.
2. **Active / standby role detection** for each HSRP group per protocol rules.
3. **Generation of VRRPv2 or VRRPv3 command sequences** in the order that minimizes host downtime: standby core first, then active.

Includes the **`hsrp2vrrp.py` wrapper**, which validates the environment (configs and child scripts), shows an interactive VRRP-version menu, and returns control after migration completes.

---

## 🔬 Architecture and operation

### Active / standby role detection

The algorithm follows the HSRP active-router election (RFC 2281):

1. Compare **priorities** `standby <group> priority`:
   - higher priority → active;
   - on tie (or absence of explicit priority — default `100`) proceed to step 2.
2. Compare **physical interface IP addresses** (`ip address` on the VLAN interface): higher value → active.
3. If IP addresses are not found, `core1` is treated as active by default.

This guarantees **role continuity**: the same router that was HSRP-active becomes VRRP-master after migration.

### Command output order

For each HSRP group in a shared VLAN a two-part block is generated:

```text
┌──────────────────────────────────────┐
│ 1. Standby core block                │  ← Applied first
│    ↓                                 │
│ 2. Verify: show vrrp brief           │
│    ↓                                 │
│ 3. Active core block                 │  ← Applied second
│    ↓                                 │
│ 4. Verify: show vrrp / ping VIP      │
└──────────────────────────────────────┘
```

**Why this order:**

- Standby is migrated first. After applying its commands (and removing HSRP on both sides), it becomes VRRP-master — the VIP temporarily moves to it.
- Active is migrated next; its VRRP priority is higher. With `preempt delay minimum 180` it reclaims master role after 180 seconds — without flapping.
- Segment outage is limited to ARP table refresh (a few seconds), not total gateway loss.

### Track-object transfer

Lines like `standby <group> track <...>` are parsed and preserved without syntax changes:

| HSRP | VRRPv2 | VRRPv3 |
|---|---|---|
| `standby 2 track 1 decrement 20` | `vrrp 2 track 1 decrement 20` | `track 1 decrement 20` (inside `address-family ipv4`) |
| `standby 2 track GigabitEthernet0/0 10` | `vrrp 2 track GigabitEthernet0/0 10` | `track GigabitEthernet0/0 10` |

Both track variants are supported:

- **object-tracking** — IP SLA / object reference with decrement;
- **interface-tracking** — interface state tracking with decrement.

### OSPF cost and preempt delay

| Parameter | Active core | Standby core |
|---|---|---|
| `ip ospf cost` | `1` | `10` |
| `vrrp priority` | `110` | `105` |
| `preempt delay minimum` | `180` sec | `180` sec |

- **OSPF cost 1/10** ensures traffic prefers the active core under equal conditions.
- **Preempt delay 180** protects against role flapping.

---

## ✨ Features

| Feature | VRRPv2 | VRRPv3 |
|---|:---:|:---:|
| Universal launcher with menu | ✅ | ✅ |
| Auto-parse HSRP, VIP and priorities | ✅ | ✅ |
| Active / standby detection per RFC 2281 | ✅ | ✅ |
| Sequential output (standby → active) | ✅ | ✅ |
| **Track-object / interface-tracking transfer** | ✅ | ✅ |
| Interactive authentication setup | ✅ | ❌ *(not supported by Cisco)* |
| Global command `fhrp version vrrp v3` | — | ✅ |
| Configure `address-family ipv4` | — | ✅ |
| Automatic `ip ospf cost` | ✅ | ✅ |
| `preempt delay minimum 180` | ✅ | ✅ |
| Priorities `110` / `105` | ✅ | ✅ |
| Detailed migration statistics | ✅ | ✅ |

---

## 📦 Requirements

- **Python** `3.6+` (command `python3`)
- Two text files with core configs: `core1.txt`, `core2.txt`
- Cisco equipment with VRRP support:
  - for VRRPv3 — command `fhrp version vrrp v3` in global mode.
- Platform / IOS / IOS-XE version matching the [compatibility matrix](#-compatibility-matrix).

> ℹ️ Modern Linux distributions (Ubuntu 20.04+, Debian 11+) lack the `python` command. Use `python3`. Optionally install the alias:
>
> ```bash
> sudo apt update && sudo apt install python-is-python3
> ```

---

## 🚀 Quickstart

```bash
# Clone the repository
git clone https://github.com/landev-ru/hsrp2vrrp.git
cd hsrp2vrrp

# Way 1 (recommended) — universal launcher
python3 hsrp2vrrp.py

# Way 2 — directly
python3 migrate_to_vrrp2.py core1.txt core2.txt
python3 migrate_to_vrrp3.py core1.txt core2.txt
```

Output: `migrate_vrrp2_sequential.cfg` or `migrate_vrrp3_sequential.cfg` with ready-to-apply commands.

### Alternative launch (without interpreter)

```bash
chmod +x hsrp2vrrp.py migrate_to_vrrp2.py migrate_to_vrrp3.py

./hsrp2vrrp.py
./migrate_to_vrrp2.py core1.txt core2.txt
./migrate_to_vrrp3.py core1.txt core2.txt
```

---

## 🎛 Universal launcher — `hsrp2vrrp.py`

Wrapper that simplifies the workflow:

1. **Validates configs** `core1.txt` and `core2.txt` (existence, read permission, non-zero size).
2. **Locates migration scripts** `migrate_to_vrrp2.py` and `migrate_to_vrrp3.py` next to itself (and in `PATH`).
3. Shows the **selection menu**:

```text
======================================================================
MAIN MENU
======================================================================
1 — Migrate to VRRPv2  (migrate_to_vrrp2.py)
2 — Migrate to VRRPv3  (migrate_to_vrrp3.py)
0 — Exit
======================================================================
Your choice (0/1/2):
```

4. Launches the selected script via `subprocess` (inherits stdin/stdout/stderr — interactive input works).
5. Returns to the menu after completion — handy for repeated runs.
6. Correctly handles `Ctrl+C` (exit code `130`) and missing files (code `1`).

### Usage

```bash
# by default looks for core1.txt and core2.txt in the current folder
python3 hsrp2vrrp.py

# or with explicit paths
python3 hsrp2vrrp.py /path/core1.txt /path/core2.txt
```

> ℹ️ If configs are missing, the launcher prints export hints and asks whether to continue or exit.

---

## 🛠 Migration preparation

> ⚠️ **Before starting**, complete the following steps.

### 1. Back up configurations

```cisco
copy running-config startup-config
copy startup-config flash:backup_core1.cfg
copy startup-config flash:backup_core2.cfg
```

### 2. Verify VRRP support

```cisco
show vrrp
show vrrp brief
```

For VRRPv3:

```cisco
fhrp version vrrp v3
```

### 3. Verify ACLs

| Protocol | IP protocol | Multicast address |
|---|---|---|
| VRRPv2 | 112 | `224.0.0.18` |
| VRRPv3 | 112 | `224.0.0.18`, `ff02::12` |

### 4. Identify critical segments

For process control and infrastructure segments (ICS / OT), allocate a **dedicated maintenance window** — VRRP transition triggers a brief outage (virtual MAC change, ARP refresh).

### 5. Export configurations

```bash
ssh admin@core1 "show run" > core1.txt
ssh admin@core2 "show run" > core2.txt
```

### 6. Baseline snapshot

```cisco
show standby brief
show standby all
show ip ospf neighbor
show ip route summary
show track
```

---

## 📘 Usage

### 🔹 VRRPv2 — `migrate_to_vrrp2.py`

```bash
python3 migrate_to_vrrp2.py core1.txt core2.txt
```

The script prompts for authentication type:

| Choice | Action |
|:---:|---|
| `1` | No authentication |
| `2` | Prompt for text key → `vrrp <g> authentication text <key>` |
| `3` | Prompt for MD5 key → `vrrp <g> authentication md5 key-string <key>` |

**Generated commands:**

```cisco
interface VlanX
 no standby <group>
 vrrp <group> ip <VIP>
 vrrp <group> preempt delay minimum 180
 vrrp <group> priority 110              ! 105 for standby
 vrrp <group> track <...>               ! if HSRP had track
 vrrp <group> authentication ...        ! if selected
 ip ospf cost 1                         ! 10 for standby
```

### 🔹 VRRPv3 — `migrate_to_vrrp3.py`

```bash
python3 migrate_to_vrrp3.py core1.txt core2.txt
```

Authentication is **not used** — Cisco does not support it in VRRPv3 (RFC 5798).

**Generated commands:**

```cisco
fhrp version vrrp v3
!
interface VlanX
 no standby <group>
 vrrp <group> address-family ipv4
  address <VIP> primary
  priority 110                 ! 105 for standby
  timers advertise 5000
  track <...>                  ! if HSRP had track
  preempt delay minimum 180
 exit
 ip ospf cost 1                ! 10 for standby
```

> ℹ️ In VRRPv3 the `track` command is placed **inside** the `address-family ipv4` block.

---

## 🗺 Migration strategy

Per-VLAN step-by-step scenario. Repeat for each VLAN, starting with the least critical.

### Phase 1. Preparation (no config changes)

1. Save baseline: `show standby brief`, `show ip ospf neighbor`, `show ip route summary`, `show track`.
2. Ensure ACLs allow IP protocol 112 to multicast `224.0.0.18`.
3. Verify `show vrrp brief`.
4. Agree on a maintenance window for critical segments.

### Phase 2. Apply Standby core block

1. Log into standby core (for the VLAN).
2. Apply the `# --- Standby core ---` block.
3. Verify: `show vrrp brief` — the group should appear as Master.
4. Verify connectivity: `ping <VIP>` from a test host — stable (1–3 packet loss possible).

### Phase 3. Apply Active core block

1. Log into active core (for the VLAN).
2. Apply the `# --- Active core ---` block.
3. Verify: `show vrrp brief` — active is Master, standby is Backup.
4. `preempt delay minimum 180` takes effect — active may stay Backup for up to 3 minutes.

### Phase 4. Verification and documentation

1. `show vrrp brief` on both cores — roles match pre-migration.
2. `ping <VIP>` from multiple hosts — stable.
3. `show track` — objects Up.
4. `show ip ospf neighbor` — adjacency restored.
5. Log the result in the change record.

### Phase 5. Move to next VLAN

Only after successful verification. **Do not parallelize** — the only way to guarantee bounded blast radius.

---

## ✅ Post-migration verification

| Check | Command | Expected |
|---|---|---|
| VRRP role | `show vrrp brief` | active core — Master, standby — Backup |
| VIP reachable | `ping <VIP>` from a host | 0% loss after stabilization |
| Track objects | `show track` | all Up |
| OSPF adjacency | `show ip ospf neighbor` | Full/2-Way |
| Routing | `show ip route summary` | routes via VIP alive |
| ARP/MAC | `show ip arp <VIP>` | MAC `0000.5e00.01xx` |
| Preempt | `show vrrp <group>` | `preempt delay minimum 180` |
| Auth (v2) | `show vrrp <group>` | method and key correct |
| Logs | `show logging \| include VRRP` | no protocol errors |

If any check fails — proceed to [Rollback plan](#-rollback-plan).

---

## ⏪ Rollback plan

### Rollback one VLAN

```cisco
interface VlanX
 no vrrp <group> address-family ipv4    ! for v3
 ! or
 no vrrp <group> ip <VIP>               ! for v2
 standby <group> ip <VIP>               ! restore HSRP
 standby <group> priority <original>
 standby <group> preempt               ! if any
 standby <group> track ...             ! restore tracks
 ip ospf cost <original>               ! restore OSPF cost
```

Order: standby core first, then active.

### Full rollback from backup

```cisco
copy flash:backup_core1.cfg running-config
copy flash:backup_core2.cfg running-config
```

### Mandatory rollback criteria

- VIP unreachable > 60 sec after preempt stabilization;
- Track objects stay Down > 5 minutes;
- OSPF adjacency does not recover;
- Packet loss via VIP > 1% for 5 minutes.

---

## 📋 Sample output

### Statistics at startup

```text
======================================================================
  STATISTICS
======================================================================
  File 1:                              core1.txt
  File 2:                              core2.txt
  Common interfaces:                   12
  HSRP groups found (total):           14
  Common groups (on both cores):       12
  Will be migrated to VRRP:            12
  Track objects to transfer:           8

  Planned for migration:
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

### `migrate_vrrp2_sequential.cfg`

```cisco
# Sequential HSRP -> VRRPv2 migration for the core
# Order: standby first, then active for each VLAN.
# Authentication: md5 (key: MySecretKey)

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

### `migrate_vrrp3_sequential.cfg`

```cisco
# Sequential HSRP -> VRRPv3 migration for the core
# Global command: fhrp version vrrp v3
# WARNING: VRRPv3 does not support authentication (RFC 5798).

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

## 📁 Project structure

```text
hsrp2vrrp/
├── hsrp2vrrp.py                 # Universal launcher (selection menu)
├── migrate_to_vrrp2.py          # VRRPv2 command generator
├── migrate_to_vrrp3.py          # VRRPv3 command generator
├── core1.txt                    # Sample core1 config
├── core2.txt                    # Sample core2 config
├── migrate_vrrp2_sequential.cfg # Result (generated)
├── migrate_vrrp3_sequential.cfg # Result (generated)
├── logo.png                     # Project logo
├── index.html                   # Project page (GitHub Pages)
└── README.md
```

---

## ⚠️ Important notes and limitations

> 🔴 **Authentication**
> - VRRPv2 supports text and MD5 authentication.
> - VRRPv3 **does not support** authentication (RFC 5798).

> ◉ **HSRP keys**
> The VRRPv2 script **ignores** original HSRP keys and uses a single manually entered key.

> ◉ **Virtual MAC**
> VRRP uses `0000.5e00.01xx`, different from HSRP (`0000.0c07.acXX`). Brief outage (1–5 sec per VLAN). On switches with port-security or sticky MAC, verify policy in advance.

> 🟢 **Track objects**
> Preserved in the same group block. Both object-tracking and interface-tracking are supported.

> 🔵 **OSPF cost**
> Defaults: `1` for active, `10` for standby.

> ◉ **Preempt delay**
> `180` seconds. For DC — can be `30–60`, for WAN — `300–600`.

> 🎛 **Launcher location**
> `hsrp2vrrp.py` looks for migration scripts **next to itself** (and in `PATH`).

> ⚫ **Syntax check**
> VRRP syntax may differ across IOS/IOS-XE versions. **Test on a single VLAN first.**

> 🟡 **Do not parallelize**
> Migrate VLANs **one at a time**.

> 🔐 **Security**
> VRRPv2 MD5 authentication does not protect against interception. For critical segments add ACLs on `224.0.0.18` / `ff02::12`.

---

## 🧩 Compatibility matrix

| Platform / version | VRRPv2 | VRRPv3 | `fhrp version vrrp v3` |
|---|:---:|:---:|:---:|
| Cisco IOS 12.4 | ✅ | ❌ | ❌ |
| Cisco IOS 15.x | ✅ | ✅ | ✅ |
| Cisco IOS-XE 3.x | ✅ | ✅ | ✅ |
| Cisco IOS-XE 16.x / 17.x | ✅ | ✅ | ✅ |
| Cisco NX-OS | ✅ | ✅ | ✅ (via feature) |
| Cisco ASA / FTD | ❌ (HSRP only) | ❌ | ❌ |
| Cisco IOS-XR | ✅ | ✅ | ✅ |

---

## 🔧 Troubleshooting

### VRRP group does not come up

1. `show vrrp` — if `Init`, no master elected.
2. Verify the same **VRID** on both cores.
3. `show vrrp <group> | include State`.
4. `show ip access-lists | include 224.0.0.18` — not blocked?
5. `show logging | include VRRP` — authentication errors.

### Authentication error

```
%VRRP-4-BADAUTH: Bad authentication from 10.80.68.2, group 2
```

- Key and method (text/md5) must be **identical on both cores**.
- MD5 key up to 20 chars, not truncated.
- VRRPv3 has no authentication.

### Preempt not working

- `preempt delay minimum 180` — master returns **only after 180 seconds**.
- `show vrrp <group> | include Priority` — priority higher.
- On some IOS versions `preempt` is disabled by default.

### Track object stays Down

- `show track 1` — status.
- The object exists on this core (IP SLA configured).
- VRRP `track` **does not create** the object — references an existing one.

### VIP unreachable after migration

- `show ip arp <VIP>` — MAC `0000.5e00.01xx`.
- **`no standby <group>`** applied (otherwise both sides are master).
- `show vrrp brief` — group not stuck in Init.

### `hsrp2vrrp.py` does not find migration scripts

- `migrate_to_vrrp2.py` and `migrate_to_vrrp3.py` in **the same folder**.
- Or `export PATH="$PATH:/path/to/hsrp2vrrp"`.

---

## ❓ FAQ

<details>
<summary><b>Why is <code>python</code> not found?</b></summary>

Use `python3`:

```bash
python3 hsrp2vrrp.py
```

Or `sudo apt install python-is-python3`.
</details>

<details>
<summary><b>How is running via <code>hsrp2vrrp.py</code> different from direct?</b></summary>

`hsrp2vrrp.py` validates configs and scripts, shows a menu, and launches the selected script via `subprocess`. Direct run works the same, without checks and menu. Generated output is identical.
</details>

<details>
<summary><b>What if the launcher does not find configs?</b></summary>

Export configs:

```bash
ssh admin@core1 "show run" > core1.txt
ssh admin@core2 "show run" > core2.txt
```

Or pass paths:

```bash
python3 hsrp2vrrp.py /path/core1.txt /path/core2.txt
```
</details>

<details>
<summary><b>Why no authentication in VRRPv3?</b></summary>

RFC 5798 does not define authentication. Use VRRPv2 or rely on ACLs / segmentation.
</details>

<details>
<summary><b>How are track objects transferred?</b></summary>

- **VRRPv2:** `vrrp <group> track <...>`
- **VRRPv3:** `track <...>` inside `vrrp <group> address-family ipv4`

Both object-tracking and interface-tracking are supported.
</details>

<details>
<summary><b>How to determine which core is active?</b></summary>

By HSRP priority. On tie — higher IP = active.
</details>

<details>
<summary><b>Can everything be applied at once?</b></summary>

Technically yes, but it causes prolonged outage across all segments. Apply one VLAN at a time.
</details>

<details>
<summary><b>How to make scripts executable?</b></summary>

```bash
chmod +x hsrp2vrrp.py migrate_to_vrrp2.py migrate_to_vrrp3.py
./hsrp2vrrp.py
```
</details>

---

## 📄 License

Distributed under the **MIT License**.

Scripts are provided **"as is"**. The author is not liable for any failures. Always test in the lab before using in production.

<p align="center">
  <a href="#-english">↑ Back to top (EN)</a> &nbsp;|&nbsp; <a href="#-русский">🇷🇺 Русская версия ↑</a>
</p>
