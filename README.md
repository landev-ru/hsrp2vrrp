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
  <b>Набор инструментов для планируемой миграции FHRP с HSRP на VRRPv2 / VRRPv3 на паре ядерных коммутаторов Cisco.</b><br/>
  Полный разбор конфигураций, определение ролей active/standby, перенос track-объектов, интерактивная настройка аутентификации и пошаговая стратегия применения без массового простоя.
</p>

---

## 📖 Содержание

- [Назначение и область применения](#-назначение-и-область-применения)
- [Архитектура и принцип работы](#-архитектура-и-принцип-работы)
- [Возможности](#-возможности)
- [Требования](#-требования)
- [Быстрый старт](#-быстрый-старт)
- [Универсальный лаунчер — `hsrp2vrrp.py`](#-универсальный-лаунчер--hsrp2vrrppy)
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

Такая логика гарантирует **преемственность ролей**: тот же роутер, который был HSRP-active, становится VRRP-мастером после миграции. Это критично, поскольку правила выбора мастера в HSRP и VRRP совпадают по приоритету, но расходятся по tie-breaker (в VRRP — по IP, в HSRP — по IP при равных приоритетах тоже, но механика голосования иная). Скрипт приводит роли к детерминированному состоянию до миграции.

### Порядок вывода команд

Для каждой группы HSRP в общем VLAN генерируется блок из двух частей:

```
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
- Затем переводится active, у которого приоритет VRRP выше. С включённым `preempt delay minimum 180` он вернёт себе мастер-роль через 180 секунд — без флаппинга, если хост-сегмент в этот момент нестабилен.
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

Синтаксис сохраняется «как есть» — ручное переписывание не требуется.

### OSPF cost и preempt delay

Для минимизации «перекоса» трафика в переходный период:

| Параметр | Active-ядро | Standby-ядро |
|---|---|---|
| `ip ospf cost` | `1` | `10` |
| `vrrp priority` | `110` | `105` |
| `preempt delay minimum` | `180` сек | `180` сек |

- **OSPF cost 1/10** гарантирует, что при равных условиях трафик пойдёт через active-ядро, а standby используется только при отказе.
- **Preempt delay 180** защищает от флаппинга ролей: если active-ядро кратковременно уйдёт в down, оно не будет немедленно возвращать мастер-роль, давая сессии стабилизироваться.
- Значение `180` секунд выбрано как компромисс между скоростью возврата и устойчивостью к кратковременным сбоям (перезагрузка OSPF, BGP-сессии, OSPF SPF-реконвергенция).

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

- **Автопарсинг** — без ручного выписывания VIP, приоритетов и track-ов.
- **Определение ролей** — по приоритету HSRP; при равенстве — по IP-адресу интерфейса.
- **Перенос track** — в том же блоке группы; поддерживаются object- и interface-tracking.
- **Последовательный вывод** — для каждого VLAN сначала standby, затем active.
- **Аутентификация VRRPv2** — интерактивный выбор: без аутентификации / text / MD5; единый ключ для обоих ядер.
- **VRRPv3** — глобальная команда `fhrp version vrrp v3` и `address-family ipv4`.
- **OSPF cost** — автоматическая установка `1` / `10` для active / standby.
- **Preempt delay** — `180` секунд, защита от флаппинга.
- **Статистика миграции** — количество найденных групп, к переводу, число перенесённых track-ов, список VLAN/групп.
- **Проверка окружения** — лаунчер валидирует наличие конфигов и скриптов до запуска.

---

## 📦 Требования

- **Python** `3.6+` (команда `python3`)
- Два текстовых файла с конфигурациями ядер:
  - `core1.txt`
  - `core2.txt`
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
5. Возвращает управление в меню после завершения — удобно для повторных прогонов (проверка на стенде, отработка сценария, откат).
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

### 6. Снимок текущего состояния (baseline)

Перед миграцией сохраните вывод диагностики — это база для сравнения после изменений:

```cisco
show standby brief
show standby all
show ip ospf neighbor
show ip route summary
show track
```

Для post-migration verification эти же команды (заменяя `standby` на `vrrp`) должны показать эквивалентную топологию.

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
3. Проверить `show vrrp brief` — пустой или с ожидаемыми группами (для VRRPv3 — доступна `fhrp version vrrp v3`).
4. Согласовать окно обслуживания для критичного сегмента.

### Фаза 2. Применение блока Standby-ядра

1. Войти на standby-ядро (для VLAN).
2. Применить блок из секции `# --- Standby core ---`.
3. Проверить: `show vrrp brief` — группа должна появиться в состоянии Master (standby стал мастером, поскольку HSRP-active ещё не мигрировал).
4. Проверить связность: с тестового хоста `ping <VIP>` — должно быть стабильно (возможны кратковременные потери 1–3 пакета).

### Фаза 3. Применение блока Active-ядра

1. Войти на active-ядро (для VLAN).
2. Применить блок из секции `# --- Active core ---`.
3. Проверить: `show vrrp brief` — на active-ядре статус Master (по приоритету 110 > 105), на standby — Backup.
4. Проверить, что `preempt delay minimum 180` вступил в силу: в течение 3 минут после возврата active мог сохраняться Backup — это ожидаемое поведение.

### Фаза 4. Верификация и документирование

1. `show vrrp brief` на обоих ядрах — роли соответствуют pre-migration.
2. `ping <VIP>` с нескольких хостов VLAN — стабильно.
3. `show track` — объекты в состоянии Up.
4. `show ip ospf neighbor` — соседство через VIP восстановлено.
5. Зафиксировать результат в журнале изменений.

### Фаза 5. Переход к следующему VLAN

Только после успешной верификации текущего VLAN. **Не параллелить** — это единственный способ гарантировать ограниченный blast-radius при возникновении проблемы.

---

## ✅ Проверка после миграции

Чек-лист на каждый VLAN:

| Проверка | Команда | Ожидание |
|---|---|---|
| Роль VRRP | `show vrrp brief` | на active-ядре — Master, на standby — Backup |
| VIP активен | `ping <VIP>` с хоста | 0% loss после стабилизации |
| Track-объекты | `show track` | все Up |
| OSPF-соседство | `show ip ospf neighbor` | Full/2-Way по ожидаемым интерфейсам |
| Маршрутизация | `show ip route summary` | маршруты через VIP живы |
| ARP/MAC | `show ip arp <VIP>` | виртуальный MAC `0000.5e00.01xx` |
| Preempt | `show vrrp <group>` | `preempt delay minimum 180` |
| Аутентификация (v2) | `show vrrp <group>` | метод и ключ соответствуют заданным |
| Логи | `show logging | include VRRP` | без ошибок протокола |

Если хотя бы один пункт не сходится — перейти к [Плану отката](#-план-отката) **до** продолжения миграции остальных VLAN.

---

## ⏪ План отката

Откат выполняется на **уже мигрированном** VLAN, если post-migration verification не прошла.

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

Порядок: сначала standby-ядро (обратный порядок миграции), затем active.

### Полный откат из бэкапа

Если проблема не локализуется — восстановление из резервной копии:

```cisco
copy flash:backup_core1.cfg running-config
copy flash:backup_core2.cfg running-config
```

С последующим `reload` или `write memory` по политике эксплуатации.

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
> - VRRPv3 **не поддерживает** аутентификацию (RFC 5798). Если требуется — используйте VRRPv2 или полагайтесь на ACL/сегментацию.

> ◉ **Ключи HSRP**
> В исходных конфигах ключи HSRP могут различаться. Скрипт для VRRPv2 **игнорирует** их и использует единый ключ, введённый вручную — единый для обоих ядер.

> ◉ **Виртуальный MAC**
> VRRP использует MAC `0000.5e00.01xx` (последний байт = group ID), отличный от HSRP (`0000.0c07.acXX`). Это вызовет обновление ARP-таблиц на хостах и кратковременный разрыв (обычно 1–5 секунд на VLAN). На коммутаторах с port-security или sticky MAC возможна фильтрация нового MAC — проверьте это заранее.

> 🟢 **Track-объекты**
> Скрипт переносит track-и из HSRP в VRRP **в том же блоке группы**. Поддерживаются object-tracking (`track 1 decrement 20`) и interface-tracking (`track GigabitEthernet0/0 10`). При переносе проверьте, что decrement аналогичен по величине (по умолчанию HSRP `10`, VRRP — наследуется из `track`).

> 🔵 **OSPF cost**
> По умолчанию: `1` для active, `10` для standby. При необходимости скорректируйте значения в скрипте — например, для multi-area OSPF или при наличии TE-туннелей.

> ◉ **Preempt delay**
> Установлена задержка `180` секунд. Для дата-центров с быстрым reconvergence её можно уменьшить до `30–60`, а для WAN/филиалов — увеличить до `300–600` для защиты от flapping.

> 🎛 **Расположение лаунчера**
> `hsrp2vrrp.py` ищет `migrate_to_vrrp2.py` / `migrate_to_vrrp3.py` **рядом с собой** (и в `PATH`). Держите все три скрипта в одной папке.

> ⚫ **Проверка синтаксиса**
> Синтаксис VRRP может отличаться в зависимости от версии IOS/IOS-XE. **Перед массовым применением протестируйте на одном VLAN.**

> 🟡 **Не параллелить**
> Мигрируйте VLAN **поочерёдно**. Пакетное применение всех блоков одновременно приведёт к длительному разрыву на всех сегментах.

> 🔐 **Безопасность**
> MD5-аутентификация VRRPv2 не защищает от перехвата (слабый ключ, отсутствие HMAC). Для критичных сегментов используйте дополнительно ACL на `224.0.0.18` и/или VRRPv3 с ACL на `ff02::12`.

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

Точную поддержку проверяйте командой `show vrrp ?` и `show running-config | include vrrp` на целевой платформе **до** миграции.

---

## 🔧 Troubleshooting

### VRRP-группа не поднимается

1. Проверьте `show vrrp` — если `Init`, значит мастер не выбран.
2. Убедитесь, что обе стороны настроены на **одинаковый VRID**.
3. Проверьте `show vrrp <group> | include State` на обоих ядрах.
4. Проверьте ACL: `show ip access-lists | include 224.0.0.18` — не блокирует ли.
5. Проверьте `show logging | include VRRP` — не видно ли ошибок аутентификации.

### Ошибка аутентификации

```
%VRRP-4-BADAUTH: Bad authentication from 10.80.68.2, group 2
```

- Убедитесь, что **на обоих ядрах** ключ и метод (text/md5) идентичны.
- В VRRPv2 длина MD5-ключа — до 20 символов. Проверьте, что ключ не обрезан.
- В VRRPv3 аутентификация отсутствует — если вы применили команды `authentication`, они будут проигнорированы или отклонены.

### Preempt не работает

- `preempt delay minimum 180` — мастер вернётся **только через 180 секунд**. Если вы проверяете сразу после возврата — это ожидаемое поведение.
- Проверьте, что приоритет реально выше: `show vrrp <group> | include Priority`.
- На некоторых версиях IOS `preempt` по умолчанию выключен — убедитесь, что он в конфиге.

### Track-объект остаётся Down

- Проверьте `show track 1` — состояние объекта.
- Убедитесь, что объект существует на данном ядре (например, IP SLA не настроен).
- В VRRPv2/V3 `track` **не создаёт** объект, а ссылается на уже существующий.

### VIP недоступен после миграции

- Проверьте `show ip arp <VIP>` — виртуальный MAC `0000.5e00.01xx`.
- Проверьте, что **`no standby <group>`** применилось (иначе обе стороны будут считать себя мастером).
- Проверьте `show vrrp brief` — не осталось ли группы в Init.

### `hsrp2vrrp.py` не находит скрипты миграции

- Убедитесь, что `migrate_to_vrrp2.py` и `migrate_to_vrrp3.py` лежат **в той же папке**, что и лаунчер.
- Либо добавьте эту папку в `PATH`:
  ```bash
  export PATH="$PATH:/path/to/hsrp2vrrp"
  ```

---

## ❓ FAQ

<details>
<summary><b>Почему команда <code>python</code> не найдена?</b></summary>

В современных Linux-дистрибутивах команда `python` отсутствует. Используйте `python3`:

```bash
python3 hsrp2vrrp.py
```

Либо установите псевдоним:

```bash
sudo apt install python-is-python3
```
</details>

<details>
<summary><b>Чем отличается запуск через <code>hsrp2vrrp.py</code> от прямого?</b></summary>

Лаунчер `hsrp2vrrp.py` — обёртка: проверяет наличие конфигов и скриптов, показывает меню и запускает нужный скрипт через `subprocess`. Прямой запуск работает так же, но без проверок и меню. Результат генерации конфигов идентичен.
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
</details>

<details>
<summary><b>Почему в VRRPv3 нет аутентификации?</b></summary>

Протокол VRRPv3 (RFC 5798) не предусматривает механизмов аутентификации. Используйте VRRPv2 либо компенсируйте ACL/сегментацией.
</details>

<details>
<summary><b>Как переносятся track-и?</b></summary>

Скрипт находит строки `standby <group> track ...` и сохраняет всё после `track`:

- **VRRPv2:** `vrrp <group> track <...>`
- **VRRPv3:** `track <...>` внутри `vrrp <group> address-family ipv4`

Поддерживаются object-tracking (`track 1 decrement 20`) и interface-tracking (`track GigabitEthernet0/0 10`).
</details>

<details>
<summary><b>Как определить, какое ядро active, а какое standby?</b></summary>

Скрипт сравнивает приоритеты HSRP (`standby <g> priority`). Выше приоритет — active. При равенстве — больше IP = active.
</details>

<details>
<summary><b>Можно ли применить всё сразу, не по одному VLAN?</b></summary>

Технически — да, но это приведёт к длительному разрыву на всех сегментах одновременно. Рекомендуется применять **поочерёдно**, с проверкой после каждого VLAN.
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
</details>

---

## 📄 Лицензия

Проект распространяется под лицензией **MIT**.

Скрипты предоставляются **«как есть»**. Автор не несёт ответственности за возможные сбои. Всегда тестируйте на стенде перед применением в production.

---
