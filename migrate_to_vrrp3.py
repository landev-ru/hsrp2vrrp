#!/usr/bin/env python3
import re
import sys

def parse_config(path):
    with open(path, encoding='utf-8') as f:
        text = f.read()

    parts = re.split(r'(?=^interface\s+)', text, flags=re.M)
    interfaces = {}

    for part in parts:
        part = part.strip()
        if not part.startswith('interface '):
            continue

        lines = part.splitlines()
        iface = lines[0].split()[1]
        data = {'name': iface, 'ip': None, 'standby': {}}

        for line in lines[1:]:
            s = line.strip()
            if s.startswith('ip address '):
                tokens = s.split()
                if len(tokens) >= 3:
                    data['ip'] = tokens[2]
            elif s.startswith('standby '):
                tokens = s.split()
                if len(tokens) < 3:
                    continue
                group = tokens[1]
                rest = tokens[2:]
                key = rest[0]
                d = data['standby'].setdefault(group, {})
                if key == 'ip' and len(rest) >= 2:
                    d['ip'] = rest[1]
                elif key == 'priority' and len(rest) >= 2:
                    d['priority'] = int(rest[1])
                elif key == 'preempt':
                    d['preempt'] = True

        interfaces[iface] = data

    return interfaces


def ip_to_int(ip):
    parts = list(map(int, ip.split('.')))
    return (parts[0] << 24) + (parts[1] << 16) + (parts[2] << 8) + parts[3]


def determine_active(cfg1, cfg2, iface, group):
    d1 = cfg1[iface]['standby'].get(group, {})
    d2 = cfg2[iface]['standby'].get(group, {})
    p1 = d1.get('priority', 100)
    p2 = d2.get('priority', 100)

    if p1 > p2:
        return cfg1[iface], cfg2[iface], 'core1', 'core2'
    elif p2 > p1:
        return cfg2[iface], cfg1[iface], 'core2', 'core1'
    else:
        ip1 = cfg1[iface]['ip']
        ip2 = cfg2[iface]['ip']
        if ip1 and ip2:
            if ip_to_int(ip1) > ip_to_int(ip2):
                return cfg1[iface], cfg2[iface], 'core1', 'core2'
            else:
                return cfg2[iface], cfg1[iface], 'core2', 'core1'
        else:
            return cfg1[iface], cfg2[iface], 'core1', 'core2'


def vrrp3_block(iface_data, group, is_active):
    out = []
    iface = iface_data['name']
    vip = iface_data['standby'][group]['ip']
    priority = 110 if is_active else 105
    ospf_cost = 1 if is_active else 10

    out.append(f'interface {iface}')
    out.append(f' no standby {group}')
    out.append(f' vrrp {group} address-family ipv4')
    out.append(f'  address {vip} primary')
    out.append(f'  priority {priority}')
    out.append(f'  timers advertise 5000')
    out.append(f'  preempt delay minimum 180')
    out.append(f' exit')
    out.append(f' ip ospf cost {ospf_cost}')
    out.append('!')
    return '\n'.join(out)


def main():
    if len(sys.argv) != 3:
        print("Usage: python migrate_to_vrrp3.py core1.txt core2.txt")
        sys.exit(1)

    file1, file2 = sys.argv[1], sys.argv[2]
    cfg1 = parse_config(file1)
    cfg2 = parse_config(file2)

    common = sorted(
        set(cfg1) & set(cfg2),
        key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0
    )

    out = []
    out.append('# Поочередный перевод HSRP -> VRRPv3 для ядра')
    out.append('# Глобальная команда: fhrp version vrrp v3')
    out.append('# ВНИМАНИЕ: VRRPv3 не поддерживает аутентификацию (RFC 5798).')
    out.append('# Если требуется аутентификация, используйте VRRPv2.')
    out.append('')
    out.append('fhrp version vrrp v3')
    out.append('!')

    for iface in common:
        groups1 = set(cfg1[iface]['standby'].keys())
        groups2 = set(cfg2[iface]['standby'].keys())
        common_groups = sorted(groups1 & groups2, key=lambda x: int(x))

        for group in common_groups:
            if 'ip' not in cfg1[iface]['standby'][group] or 'ip' not in cfg2[iface]['standby'][group]:
                continue

            active_data, standby_data, active_file, standby_file = determine_active(
                cfg1, cfg2, iface, group
            )

            out.append(f'# ========== {iface} (group {group}) ==========')
            out.append(f'# --- Standby core ({standby_file}) ---')
            out.append(vrrp3_block(standby_data, group, is_active=False))
            out.append('')
            out.append(f'# --- Active core ({active_file}) ---')
            out.append(vrrp3_block(active_data, group, is_active=True))
            out.append('')

    result = '\n'.join(out)

    with open('migrate_vrrp3_sequential.cfg', 'w', encoding='utf-8') as f:
        f.write(result)

    print(result)
    print('\nСохранено в migrate_vrrp3_sequential.cfg')


if __name__ == '__main__':
    main()
