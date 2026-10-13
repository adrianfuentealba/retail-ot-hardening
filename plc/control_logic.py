"""Controlador ficticio de aula. No es lógica de un PLC/SIS productivo.
Registro 0: consigna °C. Registro 4: sesgo de sensor, décimas + 1000.
Registro 5: señal de sensor conectada (1/0). Solo destinos internos del lab.
"""
def initial_state():
    return dict(temperature=2.0, setpoint=2, heater=False, compressor=True,
                exposure=0.0, spoiled=False, thermal_risk=False, plc_guard=False,
                opcua_secure=False, opcua_rbac=False, opcua_tls_only=False,
                opcua_ready=False, sensor_bias=0.0, sensor_connected=True,
                measured_temperature=2.0, sensor_valid=True, input_guard=False,
                fallback_active=False, alarm=False, door_open=False,
                modbus_reads=0, modbus_writes=0, rejected_writes=0, cycle=0)


def validate_change(state, address, value):
    """Misma barrera semántica para FC06, FC16 y Write OPC UA.
    Devuelve (permitido, razón, excepción Modbus). No aplica cambios parciales.
    """
    if address not in (0, 4, 5):
        return False, 'Registro de telemetría de solo lectura', 2
    if not isinstance(value, (int, float)) or not float(value).is_integer():
        return False, 'Valor entero requerido por el mapa de aula', 3
    value = int(value)
    if address == 0:
        if not 0 <= value <= 50:
            return False, 'Consigna fuera del rango físico del simulador', 3
        if state['plc_guard'] and not 0 <= value <= 6:
            return False, 'Interlock: consigna permitida 0–6 °C', 3
    if address == 4:
        if not 500 <= value <= 1500:
            return False, 'Sesgo fuera del rango del simulador', 3
        if state['input_guard']:
            return False, 'Entrada analógica: calibración remota no autorizada', 2
    if address == 5:
        if value not in (0, 1):
            return False, 'Entrada digital requiere 0 o 1', 3
        if state['input_guard']:
            return False, 'Bornes del sensor: modificación remota no autorizada', 2
    return True, 'Valor aceptado en mapa de aula', 0


def apply_changes(state, changes):
    """Valida todas las posiciones antes de mutar. FC16 es atómico en el lab."""
    for address, value in changes:
        ok, reason, code = validate_change(state, address, value)
        if not ok:
            state['rejected_writes'] += 1
            return False, reason, code
    for address, value in changes:
        if address == 0:
            state['setpoint'] = int(value)
            state['heater'] = value > 6
        elif address == 4:
            state['sensor_bias'] = (int(value) - 1000) / 10
        elif address == 5:
            state['sensor_connected'] = bool(value)
    return True, 'Cambios aplicados tras validación centralizada', 0


def control_cycle(state):
    """CPU: señal → plausibilidad → lógica → relés. Un ciclo del modelo."""
    measured = state['temperature'] + state['sensor_bias'] if state['sensor_connected'] else None
    valid = measured is not None and -30 <= measured <= 50
    mismatch = measured is None or abs(measured - state['temperature']) > 3
    fallback = state['input_guard'] and (not valid or mismatch)
    # Referencia independiente ideal del simulador, NO un segundo sensor físico.
    effective = state['temperature'] if fallback else measured
    state.update(measured_temperature=measured, sensor_valid=valid,
                 fallback_active=fallback, alarm=fallback or state['door_open'])
    state['heater'] = state['setpoint'] > 6
    if state['heater'] or effective is None:
        state['compressor'] = False
    elif effective > state['setpoint'] + 0.3:
        state['compressor'] = True
    elif effective < state['setpoint'] - 0.3:
        state['compressor'] = False
    # Modelo acelerado: no predice termodinámica ni inocuidad alimentaria.
    target = state['setpoint'] if state['heater'] else 2.0 if state['compressor'] else 18.0
    if state['door_open']:
        target += 4.0
    state['temperature'] += (target - state['temperature']) * 0.08
    if state['temperature'] > 8:
        state['exposure'] += 1
    state['spoiled'] = state['spoiled'] or state['exposure'] >= 12
    state['thermal_risk'] = state['heater'] and state['temperature'] > 35
    state['cycle'] += 1
    return state


def registers(state):
    return [int(state['setpoint']), int(state['temperature'] * 10) + 1000,
            int(state['heater']), int(state['spoiled']), int(state['sensor_bias'] * 10) + 1000,
            int(state['sensor_connected']), int(state['compressor']), int(state['alarm'])]
