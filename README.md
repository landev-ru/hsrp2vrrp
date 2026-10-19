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
| Универсальный лаунчер с ASCII-меню | ✅ | ✅ |
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
| Компактная статистика миграции | ✅ | ✅ |

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

На выходе появится файл `migrate_vrrp2_sequential.cfg` или `migrate_vrrp3_sequential.cfg` с готовыми командами. Вывод самих команд в консоль отключён (чтобы не засорять терминал).

---

## 🎛 Универсальный лаунчер — `hsrp2vrrp.py`

Обёртка, упрощающая работу с проектом:

1. **Проверяет конфиги** `core1.txt` и `core2.txt` (наличие, права чтения, ненулевой размер).
2. **Ищет скрипты миграции** `migrate_to_vrrp2.py` и `migrate_to_vrrp3.py` рядом с собой (и в `PATH`).
3. Отображает **строгое ASCII-меню** (без цветов и Unicode-символов, чтобы не ломалось в любых терминалах, включая `sudo` и RHEL/CentOS):

```text
======================================================================
  HSRP -> VRRP Migration Toolkit
======================================================================

  configs:  core1.txt [OK]   core2.txt [OK]
  scripts:  migrate_to_vrrp2.py [OK]   migrate_to_vrrp3.py [OK]

  --------------------------------------------------------------

   [1]  Migrate to VRRPv2  (with authentication)
   [2]  Migrate to VRRPv3  (no authentication)
   [0]  Exit

======================================================================

  Your choice (0/1/2):
```

4. Запускает выбранный скрипт через `subprocess`.
5. Возвращает управление в меню после завершения — удобно для повторных прогонов (проверка на стенде, отработка сценария, откат).
6. Корректно обрабатывает `Ctrl+C` (код выхода `130`) и отсутствие файлов (код `1`).

### Использование

```bash
# по умолчанию ищет core1.txt и core2.txt в текущей папке
python3 hsrp2vrrp.py

# или с явными путями
python3 hsrp2vrrp.py /path/core1.txt /path/core2.txt
```

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

Для технологических и инфраструктурных ИУС/ИнфПАК выделите **отдельное окно обслуживания** — переход на VRRP вызывает кратковременный разрыв.

### 5. Экспорт конфигураций

```bash
ssh admin@core1 "show run" > core1.txt
ssh admin@core2 "show run" > core2.txt
```

---

## 📘 Использование

### 🔹 VRRPv2 — `migrate_to_vrrp2.py`

```bash
python3 migrate_to_vrrp2.py core1.txt core2.txt
```

Скрипт выведет статистику и интерактивно запросит тип аутентификации:

| Выбор | Действие |
|:---:|---|
| `1` | Аутентификация не добавляется |
| `2` | Запрос текстового ключа → `vrrp <g> authentication text <key>` |
| `3` | Запрос MD5-ключа → `vrrp <g> authentication md5 key-string <key>` |

**Формируемые команды (сохраняются в файл):**

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

**Формируемые команды (сохраняются в файл):**

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
 standby <group> track ...             ! вернуть исходные track
 ip ospf cost <исходный>               ! вернуть OSPF cost
```

Порядок: сначала standby-ядро, затем active.

### Критерии, при которых откат обязателен

- VIP недоступен более 60 секунд после стабилизации preempt;
- Track-объекты остаются Down дольше 5 минут;
- OSPF-соседство не восстанавливается;
- Потеря пакетов через VIP > 1% в течение 5 минут.

---

## 📋 Пример вывода

### Статистика при запуске (компактная)

```text
======================================================================
  СТАТИСТИКА
======================================================================
  Файл 1:                              core1.txt
  Файл 2:                              core2.txt
  Общих интерфейсов:                   105
  Найдено HSRP-групп (всего):          18
  Общих групп (в обоих ядрах):         18
  Будет переведено в VRRP:             18
  Track-ов будет перенесено:           18
  Только в core1.txt: 150 шт. (GigabitEthernet1/1/1, GigabitEthernet1/1/10, ... и ещё 145)
  Только в core2.txt: 155 шт. (FastEthernet1, GigabitEthernet1/2/1, ... и ещё 150)

  Планируемые к миграции:
    - Vlan2: group 2
    - Vlan3: group 3
    - Vlan10: group 10
    ...
======================================================================

Сохранено в migrate_vrrp2_sequential.cfg
```

### Пример сгенерированного файла `migrate_vrrp2_sequential.cfg`

```cisco
# Поочередный перевод HSRP -> VRRPv2 для ядра
# Порядок: сначала standby, затем active для каждого VLAN.
# Аутентификация: md5 (ключ: MySecretKey)

# ========== Vlan2 (group 2) ==========
# --- Standby core (core2) ---
interface Vlan2
 no standby 2
 vrrp 2 ip 10.80.68.1
 vrrp 2 preempt delay minimum 180
 vrrp 2 priority 105
 vrrp 2 track 1 decrement 20
 vrrp 2 authentication md5 key-string MySecretKey
 ip ospf cost 10
!

# --- Active core (core1) ---
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

> ⚫ **Проверка синтаксиса**
> Синтаксис VRRP может отличаться в зависимости от версии IOS/IOS-XE. **Протестируйте на одном VLAN.**

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
3. `show ip access-lists | include 224.0.0.18` — не блокирует ли.
4. `show logging | include VRRP` — ошибки аутентификации.

### Ошибка аутентификации

```
%VRRP-4-BADAUTH: Bad authentication from 10.80.68.2, group 2
```
- На **обоих ядрах** ключ и метод (text/md5) идентичны.
- В VRRPv3 аутентификация отсутствует.

### Preempt не работает

- `preempt delay minimum 180` — мастер вернётся **только через 180 секунд**.
- На некоторых версиях IOS `preempt` по умолчанию выключен.

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
<summary><b>Почему скрипт не выводит сгенерированный конфиг в консоль?</b></summary>

Для удобства работы вывод конфигурации отключён (чтобы не засорять терминал сотнями строк). Все сгенерированные команды сохраняются в файл `migrate_vrrpX_sequential.cfg`. В конце работы скрипт выводит только подтверждение: `Сохранено в migrate_vrrpX_sequential.cfg`.
</details>

<details>
<summary><b>Как переносятся track-и?</b></summary>

- **VRRPv2:** `vrrp <group> track <...>`
- **VRRPv3:** `track <...>` внутри `vrrp <group> address-family ipv4`

Поддерживаются object-tracking и interface-tracking.
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
  <a href="#-русский"><img src="https://img.shields.io/badge/←_Русский-6b7280?style=for-the-badge" alt="Русский"/></a>
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

The project is intended for network engineers planning a **scheduled migration of the First Hop Redundancy Protocol (FHRP)** from proprietary Cisco HSRP to open-standard VRRP (RFC 3768 / RFC 5798).

The tool solves three practical tasks:

1. **Automatic analysis** of two configuration dumps (`show running-config` from core1 and core2).
2. **Active / standby role detection** for each HSRP group per protocol rules.
3. **Generation of VRRPv2 or VRRPv3 command sequences** in the order that minimizes host downtime.

Includes the **`hsrp2vrrp.py` wrapper**, which validates the environment, shows an interactive VRRP-version menu, and returns control after migration completes.

---

## 🔬 Architecture and operation

### Active / standby role detection

1. Compare **priorities** `standby <group> priority`:
   - higher priority → active.
2. Compare **physical interface IP addresses** (if priorities are equal).
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
- Standby is migrated first. After applying its commands, it becomes VRRP-master — the VIP temporarily moves to it.
- Active is migrated next; its VRRP priority is higher. With `preempt delay minimum 180` it reclaims master role after 180 seconds — without flapping.

### Track-object transfer

Lines like `standby <group> track <...>` are parsed and preserved without syntax changes:

| HSRP | VRRPv2 | VRRPv3 |
|---|---|---|
| `standby 2 track 1 decrement 20` | `vrrp 2 track 1 decrement 20` | `track 1 decrement 20` (inside `address-family ipv4`) |
| `standby 2 track GigabitEthernet0/0 10` | `vrrp 2 track GigabitEthernet0/0 10` | `track GigabitEthernet0/0 10` |

---

## ✨ Features

| Feature | VRRPv2 | VRRPv3 |
|---|:---:|:---:|
| Universal launcher with ASCII menu | ✅ | ✅ |
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
| Compact migration statistics | ✅ | ✅ |

---

## 📦 Requirements

- **Python** `3.6+` (command `python3`)
- Two text files with core configs: `core1.txt`, `core2.txt`
- Cisco equipment with VRRP support:
  - for VRRPv3 — command `fhrp version vrrp v3` in global mode.

> ℹ️ Modern Linux distributions (Ubuntu 20.04+, Debian 11+) lack the `python` command. Use `python3`. Optionally install the alias:
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

Output: `migrate_vrrp2_sequential.cfg` or `migrate_vrrp3_sequential.cfg` with ready-to-apply commands. The console output of the config itself is disabled to keep the terminal clean.

---

## 🎛 Universal launcher — `hsrp2vrrp.py`

Wrapper that simplifies the workflow:

1. **Validates configs** `core1.txt` and `core2.txt` (existence, read permission).
2. **Locates migration scripts** next to itself (and in `PATH`).
3. Shows the **strict ASCII menu** (no colors or Unicode symbols to avoid rendering issues in any terminal, including `sudo` and RHEL/CentOS):

```text
======================================================================
  HSRP -> VRRP Migration Toolkit
======================================================================

  configs:  core1.txt [OK]   core2.txt [OK]
  scripts:  migrate_to_vrrp2.py [OK]   migrate_to_vrrp3.py [OK]

  --------------------------------------------------------------

   [1]  Migrate to VRRPv2  (with authentication)
   [2]  Migrate to VRRPv3  (no authentication)
   [0]  Exit

======================================================================

  Your choice (0/1/2):
```

4. Launches the selected script via `subprocess`.
5. Returns to the menu after completion.
6. Correctly handles `Ctrl+C` and missing files.

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

**Generated commands (saved to file):**

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

**Generated commands (saved to file):**

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

---

## 📋 Sample output

### Compact startup statistics

```text
======================================================================
  STATISTICS
======================================================================
  File 1:                              core1.txt
  File 2:                              core2.txt
  Common interfaces:                   105
  HSRP groups found (total):           18
  Common groups (on both cores):       18
  Will be migrated to VRRP:            18
  Track objects to transfer:           18
  Only in core1.txt: 150 pcs. (GigabitEthernet1/1/1, GigabitEthernet1/1/10, ... and 145 more)
  Only in core2.txt: 155 pcs. (FastEthernet1, GigabitEthernet1/2/1, ... and 150 more)

  Planned for migration:
    - Vlan2: group 2
    - Vlan3: group 3
    - Vlan10: group 10
    ...
======================================================================

Сохранено в migrate_vrrp2_sequential.cfg
```
*(Note: the save confirmation is always in Russian, as per the script's hardcoded output).*

---

## 🛠 Migration preparation

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

### 4. Export configurations
```bash
ssh admin@core1 "show run" > core1.txt
ssh admin@core2 "show run" > core2.txt
```

### 5. Baseline snapshot
```cisco
show standby brief
show standby all
show ip ospf neighbor
show ip route summary
show track
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

> ⚫ **Syntax check**
> VRRP syntax may differ across IOS/IOS-XE versions. **Test on a single VLAN first.**

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
<summary><b>Why doesn't the script print the generated config to the console?</b></summary>

To keep the terminal clean, the config output is disabled. All generated commands are saved to `migrate_vrrpX_sequential.cfg`. At the end, the script only prints: `Сохранено в migrate_vrrpX_sequential.cfg`.
</details>

<details>
<summary><b>How are track objects transferred?</b></summary>

- **VRRPv2:** `vrrp <group> track <...>`
- **VRRPv3:** `track <...>` inside `vrrp <group> address-family ipv4`

Both object-tracking and interface-tracking are supported.
</details>

---

## 📄 License

Distributed under the **MIT License**.

Scripts are provided **"as is"**. The author is not liable for any failures. Always test in the lab before using in production.

<p align="center">
  <a href="#-english">↑ Back to top (EN)</a> &nbsp;|&nbsp; <a href="#-русский">🇷🇺 Русская версия ↑</a>
</p>
