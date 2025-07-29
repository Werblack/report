from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class OrdemSafra:
    """Modelo de dados para uma ordem Safra"""
    ordem_pagbank: int
    status_tratativa: Optional[str] = None
    provider: Optional[str] = None
    sla_cliente: Optional[int] = None
    dias_em_aberto: Optional[int] = None
    status_sla: Optional[str] = None
    prioridade: Optional[str] = None
    data_processamento: Optional[datetime] = None
    estado: Optional[str] = None
    cidade: Optional[str] = None

@dataclass
class ExportacaoRegistro:
    """Modelo para registro de exportação"""
    data_exportacao: datetime
    polo_id: str
    quantidade_ordens: int
    formato_exportacao: str
    usuario: str

@dataclass
class EstatisticasPolo:
    """Modelo para estatísticas de um polo"""
    polo_id: str
    total_ordens: int
    ordens_criticas: int
    ordens_altas: int
    media_dias_aberto: float
