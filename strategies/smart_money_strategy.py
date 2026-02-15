
from dataclasses import dataclass
import pandas as pd
import numpy as np

from .base import BaseStrategy, StrategyMetadata


@dataclass
class SmartMoneyStrategyConfig:
    # Estructura
    swing_length: int = 5        # Velas a izq/der para definir swing high/low
    
    # Fair Value Gaps (FVG)
    use_fvg: bool = True
    fvg_min_size_pct: float = 0.1  # Tamaño mínimo del gap en % del precio
    
    # Order Blocks (OB)
    use_ob: bool = True
    ob_mitigation_buffer: float = 0.0005 # Buffer para considerar mitigación
    
    # Filtro de tendencia
    trend_ema_window: int = 200
    
    # Gestión
    allow_short: bool = True

    def __post_init__(self) -> None:
        assert self.swing_length > 0, "swing_length must be positive"
        assert self.fvg_min_size_pct > 0, "fvg_min_size_pct must be positive"
        assert self.ob_mitigation_buffer >= 0, "ob_mitigation_buffer must be non-negative"
        assert self.trend_ema_window > 0, "trend_ema_window must be positive"


class SmartMoneyStrategy(BaseStrategy[SmartMoneyStrategyConfig]):
    """
    Estrategia basada en conceptos de Smart Money (SMC):
    1. Identificación de Fair Value Gaps (FVG).
    2. Identificación de Order Blocks (OB) tras quiebre de estructura (BOS).
    3. Entrada cuando el precio regresa (mitiga) un FVG o OB activo a favor de la tendencia.
    """

    def __init__(self, config: SmartMoneyStrategyConfig, meta: StrategyMetadata | None = None):
        super().__init__(config=config, meta=meta)

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Genera señales basadas en re-test de FVGs u OBs.
        """
        data = df.copy().reset_index(drop=True)
        
        # 1. Indicadores básicos
        data['ema_trend'] = data['close'].ewm(span=self.config.trend_ema_window, adjust=False).mean()
        
        # 2. Identificar FVGs
        # Bullish FVG: High[i-2] < Low[i]
        # Bearish FVG: Low[i-2] > High[i]
        
        high = data['high']
        low = data['low']
        close = data['close']
        open_ = data['open']
        
        # Shift para comparar i con i-2
        # i es la vela actual (que cierra el gap), i-1 es la vela del movimiento, i-2 es la vela previa
        # PERO FVG se forma en la vela i-1.
        # Definición estándar:
        # Vela 1: Previa
        # Vela 2: La que crea el gap (impulsiva)
        # Vela 3: La siguiente
        # Gap Bullish: Low(3) > High(1). El espacio está entre High(1) y Low(3).
        # Se confirma al cerrar la vela 3.
        
        # Usaremos shift para vectorizar.
        # En el índice 'i', miramos 'i' (vela 3), 'i-1' (vela 2), 'i-2' (vela 1).
        
        high_1 = high.shift(2)
        low_1 = low.shift(2)
        
        high_2 = high.shift(1)
        low_2 = low.shift(1)
        
        low_3 = low
        high_3 = high
        
        # Detectar Bullish FVG (confirmado en vela i)
        # Condición: Low[i] > High[i-2] y (Low[i] - High[i-2]) > umbral
        gap_size_bull = (low_3 - high_1) / close * 100
        is_bull_fvg = (low_3 > high_1) & (gap_size_bull >= self.config.fvg_min_size_pct) & (close > open_) # Vela 3 alcista o indiferente? Normalmente la vela 2 es la fuerte.
        # Refinamiento: Vela 2 debe ser alcista fuerte y dejar el gap.
        # Simplificación: Solo miramos el hueco geométrico.
        
        # Detectar Bearish FVG
        # Condición: High[i] < Low[i-2]
        gap_size_bear = (low_1 - high_3) / close * 100
        is_bear_fvg = (high_3 < low_1) & (gap_size_bear >= self.config.fvg_min_size_pct)
        
        # 3. Gestión de zonas activas (FVGs)
        # Esto es complejo vectorizar perfectamente porque un FVG dura hasta que es mitigado.
        # Haremos una aproximación iterativa rápida o usaremos una lógica simplificada:
        # "Si el precio toca un FVG reciente (últimas N velas) y la tendencia acompaña -> Signal"
        
        # Para hacerlo vectorizado y rápido en backtest, podemos marcar "zonas de interés"
        # y ver si el precio low/high toca esas zonas en velas futuras.
        
        # Vamos a iterar para ser precisos con la mitigación, ya que SMC depende mucho de niveles precisos.
        # Dado que backtesting.py corre todo el DF, iterar 30k velas en python puro es lento.
        # Usaremos numba si fuera necesario, o lógica vectorizada con "rolling max/min".
        
        # APROXIMACIÓN VECTORIZADA:
        # Crear máscara de FVG.
        # Propagar el nivel del FVG hacia adelante hasta que sea tocado.
        
        # Inicializamos columnas de señales
        data['signal'] = 0
        
        # Arrays numpy para velocidad
        c_high = high.values
        c_low = low.values
        c_close = close.values
        c_ema = data['ema_trend'].values
        
        # Listas de zonas activas
        # Cada zona: {'top': float, 'bottom': float, 'type': 'bull'/'bear', 'created_at': index}
        active_fvgs = []
        
        signals = np.zeros(len(data))
        
        # Iteramos (es lo más seguro para lógica de mitigación correcta)
        # Optimizaremos no haciendo demasiadas cosas dentro del loop.
        
        min_gap_pct = self.config.fvg_min_size_pct
        
        for i in range(2, len(data)):
            # 1. Detectar nuevos FVG en vela i (que se formó con i-2, i-1, i)
            
            # Bullish FVG
            if c_low[i] > c_high[i-2]:
                gap = (c_low[i] - c_high[i-2]) / c_close[i] * 100
                if gap >= min_gap_pct:
                    # Nuevo Bullish FVG
                    active_fvgs.append({
                        'top': c_low[i],      # El gap es hasta el low de la vela 3
                        'bottom': c_high[i-2], # Desde el high de la vela 1
                        'type': 'bull',
                        'created_at': i
                    })
            
            # Bearish FVG
            elif c_high[i] < c_low[i-2]:
                gap = (c_low[i-2] - c_high[i]) / c_close[i] * 100
                if gap >= min_gap_pct:
                    # Nuevo Bearish FVG
                    active_fvgs.append({
                        'top': c_low[i-2],     # Desde low vela 1
                        'bottom': c_high[i],   # Hasta high vela 3
                        'type': 'bear',
                        'created_at': i
                    })
            
            # 2. Verificar mitigación y señales en vela i (revisar zonas anteriores)
            # Una zona creada en i NO puede ser mitigada en i (ya es parte de la formación).
            # Solo revisamos zonas creadas antes de i.
            
            # Filtramos zonas ya mitigadas o muy viejas (opcional, por rendimiento)
            # Aquí "mitigada" significa que el precio entra en el gap.
            # Si entra, lanzamos señal y borramos la zona (o la marcamos usada).
            
            remaining_fvgs = []
            
            trend_bull = c_close[i] > c_ema[i]
            trend_bear = c_close[i] < c_ema[i]
            
            for fvg in active_fvgs:
                if fvg['created_at'] == i:
                    remaining_fvgs.append(fvg)
                    continue
                
                # Check mitigación
                if fvg['type'] == 'bull':
                    # Precio baja y toca la zona (High > Bottom y Low < Top)
                    # Zona: [Bottom, Top]
                    # Si Low[i] entra en la zona (Low < Top) y no la ha cruzado totalmente hacia abajo antes...
                    # Simplificación: Si Low[i] <= Top, toca la zona.
                    if c_low[i] <= fvg['top']:
                        # Toca zona bullish.
                        # Si además respeta el stop (no cierra por debajo del bottom, o no baja mucho más)
                        # Generamos señal LONG si tendencia acompaña.
                        if trend_bull and c_low[i] >= fvg['bottom']: # Mitigación válida (no invalida la zona rompiéndola)
                            signals[i] = 1
                            # Consumimos la zona (un trade por zona)
                            continue 
                        elif c_close[i] < fvg['bottom']:
                            # Zona invalidada (cierre por debajo)
                            continue
                        else:
                            # Toca pero no hay trend o es mecha profunda sin romper cierre... 
                            # La mantenemos si queremos re-entry o la quitamos. 
                            # SMC estricto: "mitigation" suele ser toque y rechazo.
                            # Para simplificar: primer toque = señal.
                            if trend_bull:
                                signals[i] = 1
                                continue # Consumida
                            
                            # Si no hay trend, la zona sigue viva hasta que se rompa o se use.
                            remaining_fvgs.append(fvg)
                    else:
                        remaining_fvgs.append(fvg)
                        
                elif fvg['type'] == 'bear':
                    # Precio sube y toca zona (High >= Bottom)
                    if c_high[i] >= fvg['bottom']:
                        if trend_bear and c_high[i] <= fvg['top']:
                            if self.config.allow_short:
                                signals[i] = -1
                            continue
                        elif c_close[i] > fvg['top']:
                            # Invalidada
                            continue
                        else:
                            if trend_bear and self.config.allow_short:
                                signals[i] = -1
                                continue
                            remaining_fvgs.append(fvg)
                    else:
                        remaining_fvgs.append(fvg)
            
            # Limitamos memoria: solo guardar últimos 20 FVG activos para no explotar
            if len(remaining_fvgs) > 20:
                remaining_fvgs = remaining_fvgs[-20:]
                
            active_fvgs = remaining_fvgs

        # Order Block detection (if enabled)
        if self.config.use_ob:
            active_obs = []
            ob_buffer = self.config.ob_mitigation_buffer

            for i in range(2, len(data)):
                # Detect new Order Blocks
                # Strong bullish move: current candle is bullish with body > 1.5x avg body
                body_curr = abs(c_close[i] - data["open"].values[i])
                body_avg = np.mean(
                    [abs(c_close[j] - data["open"].values[j]) for j in range(max(0, i - 10), i)]
                ) if i > 0 else body_curr

                # Bullish OB: last bearish candle before a strong bullish move
                if (
                    c_close[i] > data["open"].values[i]
                    and body_curr > 1.5 * body_avg
                    and i >= 1
                ):
                    # Check if candle i-1 was bearish (the OB candle)
                    if c_close[i - 1] < data["open"].values[i - 1]:
                        active_obs.append({
                            "top": data["open"].values[i - 1],
                            "bottom": c_close[i - 1],
                            "type": "bull",
                            "created_at": i,
                        })

                # Bearish OB: last bullish candle before a strong bearish move
                if (
                    c_close[i] < data["open"].values[i]
                    and body_curr > 1.5 * body_avg
                    and i >= 1
                ):
                    if c_close[i - 1] > data["open"].values[i - 1]:
                        active_obs.append({
                            "top": c_close[i - 1],
                            "bottom": data["open"].values[i - 1],
                            "type": "bear",
                            "created_at": i,
                        })

                # Check OB mitigation and generate signals
                remaining_obs = []
                trend_bull = c_close[i] > c_ema[i]
                trend_bear = c_close[i] < c_ema[i]

                for ob in active_obs:
                    if ob["created_at"] == i:
                        remaining_obs.append(ob)
                        continue

                    if ob["type"] == "bull":
                        # Price retraces down to the OB zone
                        if c_low[i] <= ob["top"] + ob_buffer:
                            if trend_bull and c_close[i] >= ob["bottom"]:
                                if signals[i] == 0:
                                    signals[i] = 1
                                continue  # consumed
                            elif c_close[i] < ob["bottom"]:
                                continue  # invalidated
                            else:
                                remaining_obs.append(ob)
                        else:
                            remaining_obs.append(ob)

                    elif ob["type"] == "bear":
                        if c_high[i] >= ob["bottom"] - ob_buffer:
                            if trend_bear and c_close[i] <= ob["top"]:
                                if signals[i] == 0 and self.config.allow_short:
                                    signals[i] = -1
                                continue
                            elif c_close[i] > ob["top"]:
                                continue
                            else:
                                remaining_obs.append(ob)
                        else:
                            remaining_obs.append(ob)

                if len(remaining_obs) > 20:
                    remaining_obs = remaining_obs[-20:]
                active_obs = remaining_obs

        data['signal'] = signals
        return data
