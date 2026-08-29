# Reporte Pentest — Hack The Box: Meow

## 1. Executive Summary

| Campo | Valor |
|-------|-------|
| **Alcance** | 10.129.134.54 (HTB Machine "Meow") |
| **Fecha** | 2026-06-27 |
| **Tipo** | CTF / Authorization implicita por plataforma HTB |
| **Resultado** | Root flag capturada |
| **Riesgo global** | **Critical** |
| **Tiempo total** | ~15 minutos |

**Resumen ejecutivo**: La máquina Meow ejecuta un servicio Telnet (puerto 23) con credenciales por defecto: usuario `root` con contraseña vacía. Esto otorga acceso root directo al sistema sin necesidad de escalación de privilegios.

---

## 2. Methodology (PTES)

### Pre-engagement
- Target: `10.129.134.54`
- Callback: `10.10.15.76` (VPN HTB)

### Intelligence Gathering
- **Rustscan** (`nmap/initial_rustscan.txt`): Escaneo rápido de puertos. Resultado: único puerto abierto `23/tcp`.

### Threat Modeling
- Solo un vector identificado: Telnet (puerto 23).
- SSH (22), HTTP (80) y otros servicios comunes: **no presentes**.
- Telnet transmite credenciales en texto plano → inherentemente inseguro.

### Vulnerability Analysis
- **Nmap -sV** (`nmap/initial_rustscan.txt:44-46`): Confirmó `Linux telnetd`.
- Prueba manual de credenciales: usuario `root`, contraseña vacía → acceso concedido.

### Exploitation
- Conexión directa vía `telnet 10.129.134.54` con credenciales `root:`.
- Lectura de `flag.txt` desde directorio home.

### Post Exploitation
- No requiere escalación: acceso root directo.
- Flag capturada: `b40abdfe23665f766f9c61ecba8a4c19`

---

## 3. Findings

### [FIND-001] Telnet con credenciales por defecto (root / blank password)

| Campo | Valor |
|-------|-------|
| **Severidad** | **Critical** |
| **CVSS 3.1** | 9.8 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H) |
| **CWE** | CWE-521 (Weak Password Requirements) |
| **CVE** | N/A (mala configuración) |
| **Ubicación** | 10.129.134.54:23 |

**Descripción**: El servicio Telnet (telnetd) acepta autenticación con usuario `root` y contraseña vacía. Esto permite acceso remoto completo al sistema con privilegios root sin autenticación efectiva.

**Evidencia**:
- Puerto confirmado: `nmap/initial_rustscan.txt` → `23/tcp open telnet Linux telnetd`
- Acceso verificado manualmente vía `telnet 10.129.134.54` con user `root` y password vacía.
- Flag extraída: `flag.txt` en directorio home.

**Impacto**: Control total remoto del sistema. Lectura/escritura de archivos, instalación de backdoors, pivoteo a otras máquinas de la red interna.

**Remediación**:
1. Deshabilitar Telnet, reemplazar por SSH con autenticación por llaves.
2. Si Telnet es requerido, exigir contraseñas robustas y restringir acceso por IP.
3. Eliminar cuentas con credenciales por defecto.

---

## 4. Evidence Inventory

| Archivo | Tipo | Hallazgo |
|---------|------|----------|
| `nmap/initial_rustscan.txt` | Port scan | Puerto 23/tcp (telnet) abierto |
| `loot/passlist.txt` | Credenciales | Lista de prueba usada |

---

## 5. Remediation Summary

| Prioridad | Acción | Esfuerzo |
|-----------|--------|----------|
| **Quick win** | Cambiar contraseña de root | Inmediato |
| **Quick win** | Deshabilitar Telnet, usar SSH | Corto plazo |
| **Medium** | Implementar autenticación por llaves SSH | Corto plazo |
| **Long term** | Auditoría de servicios expuestos | Medio plazo |

---

## 6. Lessons Learned

- **Puerto 23 siempre revisar**: Telnet es inseguro pero sigue siendo explotado cuando está expuesto.
- **Credenciales por defecto**: La primera prueba debe ser siempre con credenciales default antes de intentar exploits complejos.
- **Máquina fácil**: Un solo paso (telnet con root vacío) resuelve la room completa.
