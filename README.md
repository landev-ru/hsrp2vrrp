<p align="center">
  <img src="https://raw.githubusercontent.com/landev-ru/hsrp2vrrp/main/logo.png" alt="hsrp2vrrp — HSRP → VRRP Migration Toolkit" width="480"/>
</p>


<p align="center">
  <img src="https://img.shields.io/badge/python-3.6%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Cisco-IOS%20%7C%20IOS--XE-1BA0D7?style=for-the-badge&logo=cisco&logoColor=white" alt="Cisco"/>
  <img src="https://img.shields.io/badge/VRRP-v2%20%7C%20v3-success?style=for-the-badge" alt="VRRP"/>
  <img src="https://img.shields.io/badge/license-MIT-yellow?style=for-the-badge" alt="License"/>
</p>

<p align="center">
  <b>Автоматическая генерация команд для плавного перехода с HSRP на VRRPv2 / VRRPv3 на двух ядрах сети.</b><br/>
  Последовательное применение, минимизация разрыва, поддержка аутентификации.
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

- **Автопарсинг HSRP** — автоматически находит VLAN и группы HSRP в конфигах обоих ядер. Не нужно вручную выписывать VIP и приоритеты.
- **Определение ролей** — ядро с большим приоритетом HSRP считается active. При равенстве сравниваются IP-адреса интерфейсов.
- **Последовательный вывод** — для каждого VLAN команды выводятся в порядке standby → active. Это минимизирует простой хостов.
- **Аутентификация VRRPv2** — интерактивный выбор: без аутентификации, текстовая или MD5. Единый ключ применяется к обоим ядрам.
- **VRRPv3 из коробки** — глобальная команда `fhrp version vrrp v3` и настройка `address-family ipv4`.
- **OSPF cost** — автоматическая установка стоимости OSPF: 1 для active, 10 для standby.

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

# VRRPv2 (с выбором аутентификации)
python3 migrate_to_vrrp2.py core1.txt core2.txt

# VRRPv3 (без аутентификации)
python3 migrate_to_vrrp3.py core1.txt core2.txt
```

На выходе появится файл `migrate_vrrp2_sequential.cfg` или `migrate_vrrp3_sequential.cfg` с готовыми командами.

### Альтернативный запуск (без вызова интерпретатора)

Скрипты содержат shebang `#!/usr/bin/env python3`, поэтому их можно сделать исполняемыми и запускать напрямую:

```bash
chmod +x migrate_to_vrrp2.py migrate_to_vrrp3.py

./migrate_to_vrrp2.py core1.txt core2.txt
./migrate_to_vrrp3.py core1.txt core2.txt
```

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

Два скрипта — два сценария. Выбирайте под свою задачу.

### 🔹 VRRPv2 — `migrate_to_vrrp2.py`

```bash
python3 migrate_to_vrrp2.py core1.txt core2.txt
```

Скрипт интерактивно запросит тип аутентификации:

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
 vrrp <group> priority 110        ! 105 для standby
 vrrp <group> authentication ...  ! если выбрана
 ip ospf cost 1                   ! 10 для standby
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
  preempt delay minimum 180
 exit
 ip ospf cost 1                ! 10 для standby
```

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

Фрагмент сгенерированного файла `migrate_vrrp2_sequential.cfg`:

```cisco
# ========== Vlan2 (group 2) ==========
# --- Standby core (core2.txt) ---
interface Vlan2
 no standby 2
 vrrp 2 ip 10.80.68.1
 vrrp 2 preempt delay minimum 180
 vrrp 2 priority 105
 vrrp 2 authentication md5 key-string MySecretKey
 ip ospf cost 10
!

# --- Active core (core1.txt) ---
interface Vlan2
 no standby 2
 vrrp 2 ip 10.80.68.1
 vrrp 2 preempt delay minimum 180
 vrrp 2 priority 110
 vrrp 2 authentication md5 key-string MySecretKey
 ip ospf cost 1
!
```

---

## 📁 Структура проекта

```text
hsrp2vrrp/
├── migrate_to_vrrp2.py          # Скрипт для VRRPv2
├── migrate_to_vrrp3.py          # Скрипт для VRRPv3
├── core1.txt                    # Пример конфига первого ядра
├── core2.txt                    # Пример конфига второго ядра
├── migrate_vrrp2_sequential.cfg # Результат (генерируется)
├── migrate_vrrp3_sequential.cfg # Результат (генерируется)
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

> 🔵 **OSPF cost**
> По умолчанию: `1` для active, `10` для standby. При необходимости скорректируйте значения в скрипте.

> ◉ **Preempt delay**
> Установлена задержка `180` секунд для предотвращения частых переключений ролей.

> ⚫ **Проверка синтаксиса**
> Синтаксис VRRP может отличаться в зависимости от версии IOS/IOS-XE. **Перед массовым применением протестируйте на одном VLAN**.

---

## ❓ FAQ

<details>
<summary><b>Почему команда <code>python</code> не найдена?</b></summary>

В современных Linux-дистрибутивах (Ubuntu 20.04+, Debian 11+) команда `python` отсутствует. Используйте `python3`:

```bash
python3 migrate_to_vrrp2.py core1.txt core2.txt
```

Либо установите псевдоним:

```bash
sudo apt install python-is-python3
```

После этого команда `python` будет работать как `python3`.
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
chmod +x migrate_to_vrrp2.py migrate_to_vrrp3.py
```

Затем запускать напрямую:

```bash
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

<p align="center">
  <i>Сделано с ❤️ для сетевых инженеров</i>
</p>
