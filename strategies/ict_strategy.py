
from dataclasses import dataclass
from typing import Optional
import pandas as pd
import numpy as np

from .base import BaseStrategy, StrategyMetadata


@dataclass
class ICTStrategyConfig:
    # Kill Zones (UTC)
    # Ejemplo: London 07:00-10:00 UTC, NY 12:00-15:00 UTC
    kill_zone_start_hour: int = 7
    kill_zone_end_hour: int = 10
    
    # Estructura
    swing_length: int = 5        # Velas para definir swing high/low
    liquidity_lookback: int = 20 # Cuántas velas atrás buscar liquidez
    
    # FVG
    fvg_min_size_pct: float = 0.05
    
    # Gestión
    allow_short: bool = True


class ICTStrategy(BaseStrategy[ICTStrategyConfig]):
    """
    Estrategia ICT (Inner Circle Trader) simplificada:
    1. Kill Zone: Solo busca setups en horas específicas.
    2. Liquidity Sweep: Precio toma un Swing High/Low reciente.
    3. MSS (Market Structure Shift): Quiebre de estructura en dirección opuesta.
    4. FVG Entry: Entrada en el FVG creado por el MSS.
    """

    def __init__(self, config: ICTStrategyConfig, meta: StrategyMetadata | None = None):
        super().__init__(config=config, meta=meta)

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy().reset_index(drop=True)
        
        # Asegurar datetime
        if not pd.api.types.is_datetime64_any_dtype(data['timestamp']):
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            
        # Extraer hora para Kill Zone
        data['hour'] = data['timestamp'].dt.hour
        
        # Arrays para velocidad
        c_high = data['high'].values
        c_low = data['low'].values
        c_close = data['close'].values
        c_hour = data['hour'].values
        
        signals = np.zeros(len(data))
        
        # Estado de la estrategia
        # Necesitamos trackear Swing Highs y Lows
        
        # Función auxiliar para detectar swings en i
        # Swing High: High[i] es mayor que N velas a izq y der.
        # Solo lo sabemos en i + swing_length.
        
        sw_len = self.config.swing_length
        
        # Pre-calcular swings (vectorizado parcialmente)
        # Un swing high en 'i' se confirma en 'i + sw_len'
        # Guardaremos los swings en listas: (index, price)
        
        # Iteración principal
        # Estado:
        # 0: Buscando Liquidity Sweep (dentro de Kill Zone)
        # 1: Sweep detectado, buscando MSS
        # 2: MSS detectado, esperando FVG retrace
        
        state = 'SCAN' # SCAN, WAIT_MSS, WAIT_ENTRY
        
        setup_side = None # 'BULL' (buscamos compras tras sweep de sell-side), 'BEAR'
        sweep_level = 0.0
        mss_level = 0.0 # El nivel que debe romper para confirmar MSS
        entry_fvg = None # {top, bottom}
        
        # Variables para timeout del setup
        setup_start_idx = 0
        MAX_SETUP_DURATION = 50 # Velas máximas para que se complete la secuencia
        
        # Cache de swings recientes
        recent_highs = [] # (price, index)
        recent_lows = []
        
        for i in range(sw_len * 2, len(data)):
            # 1. Actualizar Swings (detectados con retraso sw_len)
            # Miramos si i - sw_len fue un swing
            pivot_idx = i - sw_len
            
            # Check Swing High
            is_sh = True
            for k in range(1, sw_len + 1):
                if c_high[pivot_idx] <= c_high[pivot_idx - k] or c_high[pivot_idx] <= c_high[pivot_idx + k]:
                    is_sh = False
                    break
            if is_sh:
                recent_highs.append((c_high[pivot_idx], pivot_idx))
                # Limpiar viejos
                recent_highs = [x for x in recent_highs if x[1] > i - self.config.liquidity_lookback]
                
            # Check Swing Low
            is_sl = True
            for k in range(1, sw_len + 1):
                if c_low[pivot_idx] >= c_low[pivot_idx - k] or c_low[pivot_idx] >= c_low[pivot_idx + k]:
                    is_sl = False
                    break
            if is_sl:
                recent_lows.append((c_low[pivot_idx], pivot_idx))
                recent_lows = [x for x in recent_lows if x[1] > i - self.config.liquidity_lookback]
            
            # 2. Lógica de Estado
            
            # Reset por tiempo si tarda mucho
            if state != 'SCAN' and (i - setup_start_idx > MAX_SETUP_DURATION):
                state = 'SCAN'
                setup_side = None
            
            # Kill Zone check
            in_kill_zone = self.config.kill_zone_start_hour <= c_hour[i] < self.config.kill_zone_end_hour
            
            if state == 'SCAN':
                if not in_kill_zone:
                    continue
                
                # Buscar Sweep
                # Bearish Setup: Precio toma un Swing High (Buy Side Liquidity)
                # Bullish Setup: Precio toma un Swing Low (Sell Side Liquidity)
                
                # Check High Sweep
                if self.config.allow_short:
                    for (sh_price, sh_idx) in recent_highs:
                        if c_high[i] > sh_price:
                            # Sweep detectado!
                            # Ahora buscamos ventas.
                            # El MSS será romper el Swing Low más reciente previo al sweep.
                            # Buscamos el último Swing Low antes de este movimiento.
                            # Simplificación: El último Swing Low confirmado.
                            if recent_lows:
                                last_sl = recent_lows[-1]
                                mss_level = last_sl[0]
                                state = 'WAIT_MSS'
                                setup_side = 'BEAR'
                                setup_start_idx = i
                                break
                
                # Check Low Sweep (si no encontramos High Sweep en esta vela)
                if state == 'SCAN': 
                    for (sl_price, sl_idx) in recent_lows:
                        if c_low[i] < sl_price:
                            # Sweep detectado! Buscamos compras.
                            if recent_highs:
                                last_sh = recent_highs[-1]
                                mss_level = last_sh[0]
                                state = 'WAIT_MSS'
                                setup_side = 'BULL'
                                setup_start_idx = i
                                break
            
            elif state == 'WAIT_MSS':
                # Esperamos que el precio rompa mss_level con cuerpo (cierre)
                
                if setup_side == 'BEAR':
                    # Buscamos quiebre a la baja de mss_level
                    if c_close[i] < mss_level:
                        # MSS Confirmado!
                        # Ahora buscamos si esta vela (o la anterior) dejó un FVG
                        # FVG Bearish: High[i] < Low[i-2]
                        # Revisamos las últimas 3 velas por si el FVG se formó en el impulso
                        found_fvg = False
                        # Check FVG en i (formado por i-2, i-1, i)
                        if c_high[i] < c_low[i-2]:
                            gap = (c_low[i-2] - c_high[i]) / c_close[i] * 100
                            if gap >= self.config.fvg_min_size_pct:
                                entry_fvg = {'top': c_low[i-2], 'bottom': c_high[i]}
                                found_fvg = True
                        
                        if found_fvg:
                            state = 'WAIT_ENTRY'
                        else:
                            # Si rompió pero no dejó FVG claro inmediato, 
                            # o bien buscamos FVG en velas siguientes o cancelamos.
                            # SMC estricto: el desplazamiento debe dejar FVG.
                            # Damos un margen de 1-2 velas más para que aparezca FVG?
                            # Por simplicidad: si no hay FVG en el quiebre, reset.
                            state = 'SCAN'
                            
                elif setup_side == 'BULL':
                    # Buscamos quiebre al alza de mss_level
                    if c_close[i] > mss_level:
                        # MSS Confirmado
                        # Check FVG Bullish: Low[i] > High[i-2]
                        found_fvg = False
                        if c_low[i] > c_high[i-2]:
                            gap = (c_low[i] - c_high[i-2]) / c_close[i] * 100
                            if gap >= self.config.fvg_min_size_pct:
                                entry_fvg = {'top': c_low[i], 'bottom': c_high[i-2]}
                                found_fvg = True
                        
                        if found_fvg:
                            state = 'WAIT_ENTRY'
                        else:
                            state = 'SCAN'

            elif state == 'WAIT_ENTRY':
                # Esperamos retrace al FVG
                
                if setup_side == 'BEAR':
                    # FVG Bearish es [Bottom, Top]. Precio está abajo. Esperamos subida.
                    # Entrada si High >= Bottom
                    if c_high[i] >= entry_fvg['bottom']:
                        # Check si invalida (Close > Top)
                        if c_close[i] > entry_fvg['top']:
                            state = 'SCAN' # Invalidado
                        else:
                            # ENTRY!
                            signals[i] = -1
                            state = 'SCAN' # Trade tomado, reset
                            
                elif setup_side == 'BULL':
                    # FVG Bullish es [Bottom, Top]. Precio está arriba. Esperamos bajada.
                    # Entrada si Low <= Top
                    if c_low[i] <= entry_fvg['top']:
                        # Check si invalida (Close < Bottom)
                        if c_close[i] < entry_fvg['bottom']:
                            state = 'SCAN'
                        else:
                            # ENTRY!
                            signals[i] = 1
                            state = 'SCAN'

        data['signal'] = signals
        return data
