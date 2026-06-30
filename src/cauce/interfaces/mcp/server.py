"""Adaptador MCP (FastMCP, stdio) — composition root hermano de la REST.

Read-only + simulación sobre el mismo `CompararModalidades` (SAD §5.3). Es la única capa
—junto con la REST— que cablea los adaptadores concretos sobre el caso de uso.

**Toda salida lleva el disclaimer de no-asesoría** (C-21/ADR-009/013), heredado del dominio.
Y el servidor **instruye al host** (caso borde C-22): ante "¿cuál me conviene?", mostrar los
números de ambas modalidades y **redirigir a la AFP / asesor previsional registrado / SCOMP**,
sin recomendar nunca una modalidad.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from cauce.application.comparar_modalidades import CompararModalidades, ResultadoComparacion
from cauce.domain.entities.modalidad import Modalidad
from cauce.domain.entities.perfil_previsional import PerfilPrevisional
from cauce.domain.entities.persona import Persona
from cauce.domain.value_objects.edad import Edad
from cauce.domain.value_objects.genero import Genero
from cauce.domain.value_objects.saldo import SaldoPrevisional
from cauce.domain.value_objects.supuestos import Supuestos
from cauce.infrastructure.calibracion.tasas_reguladas import (
    TASA_DESCUENTO_RP,
    TASA_DESCUENTO_RP_FUENTE,
    TASA_RV_VEJEZ,
    TASA_RV_VEJEZ_FUENTE,
)
from cauce.infrastructure.mortalidad.adaptador import AdaptadorMortalidad
from cauce.infrastructure.persistencia.memoria import RepositorioSimulacionesMemoria
from cauce.infrastructure.retornos.parametrico import GeneradorRetornosParametrico
from cauce.infrastructure.simulacion.montecarlo import SimuladorMonteCarlo
from cauce.infrastructure.tarificacion.conmutacion import TarificadorConmutacion

DIR_MORTALIDAD = Path(__file__).resolve().parents[4] / "data" / "mortalidad"

# Instrucciones a nivel servidor: codifican el caso borde C-22 en la capa MCP (SAD §5.3).
INSTRUCCIONES = (
    "Cauce es un SIMULADOR EDUCATIVO de pensiones chilenas (des-acumulación), "
    "NO asesoría previsional. Reglas al usar estas herramientas:\n"
    "1. NUNCA recomiendes una modalidad ni respondas '¿cuál me conviene?'. Muestra los "
    "números de ambas y explica qué riesgo asume cada una (longevidad vs. irrevocabilidad).\n"
    "2. Redirige SIEMPRE la decisión a la AFP, a un asesor previsional registrado y al SCOMP.\n"
    "3. Los montos son ilustrativos (promedios de mercado regulados), no la oferta real para "
    "esa persona; dilo explícitamente.\n"
    "4. Incluye el disclaimer que viene en cada resultado."
)

_NOMBRE = {
    Modalidad.RETIRO_PROGRAMADO: "Retiro Programado",
    Modalidad.RV_INMEDIATA: "Renta Vitalicia",
    Modalidad.RT_RV_DIFERIDA: "Renta Temporal con Renta Vitalicia Diferida",
    Modalidad.RV_INM_CON_RP: "Renta Vitalicia Inmediata con Retiro Programado",
}

_NO_RECOMENDACION = (
    "Este resultado NO recomienda ninguna modalidad. La elección es de la persona, con su "
    "AFP, un asesor previsional registrado y el SCOMP. Aquí solo se muestran los números."
)


def _genero(valor: str) -> Genero:
    g = valor.strip().lower()
    if g in ("m", "masculino", "hombre", "varón", "varon"):
        return Genero.MASCULINO
    if g in ("f", "femenino", "mujer"):
        return Genero.FEMENINO
    raise ValueError("Género inválido: use 'M'/'Hombre' o 'F'/'Mujer'.")


def _evolucion(erosion: float) -> str:
    """Traduce ``erosion_mediana`` (fracción que queda; 1.0 = fija) a lenguaje humano."""
    if erosion >= 0.99:
        return "Se mantiene fija de por vida"
    return f"Baja ~{round((1 - erosion) * 100)}% hacia el final"


def _construir_perfil(
    edad: int, saldo_uf: Decimal, genero: str, supuestos: Supuestos
) -> PerfilPrevisional:
    persona = Persona(Edad(edad), SaldoPrevisional(saldo_uf), _genero(genero))
    return PerfilPrevisional(
        id="mcp",
        version=1,
        persona=persona,
        supuestos=supuestos,
        modalidades_a_comparar=[Modalidad.RETIRO_PROGRAMADO, Modalidad.RV_INMEDIATA],
        tabla_mortalidad="2020",
        semilla=42,
    )


def _formatear(
    edad: int, saldo_uf: Decimal, genero: str, supuestos: Supuestos, res: ResultadoComparacion
) -> dict[str, Any]:
    modalidades = [
        {
            "modalidad": mod.value,
            "nombre": _NOMBRE[mod],
            "mesada_inicial_uf": round(float(m.mesada_inicial_uf), 2),
            "evolucion": _evolucion(m.erosion_mediana),
            "herencia_esperada_uf": round(float(m.herencia_esperada_uf), 1),
            "riesgo_dominante": m.riesgo_dominante,
        }
        for mod, m in res.metricas_por_modalidad.items()
    ]
    return {
        "entrada": {
            "edad": edad,
            "saldo_uf": float(saldo_uf),
            "genero": _genero(genero).value,
            "supuestos": {
                "retorno_esperado": float(supuestos.retorno_esperado),
                "inflacion": float(supuestos.inflacion),
                "tasa_descuento_rp": float(supuestos.tasa_descuento),
                "tasa_rv": float(supuestos.tasa_rv),
                "fuentes": [TASA_DESCUENTO_RP_FUENTE, TASA_RV_VEJEZ_FUENTE],
            },
        },
        "modalidades": modalidades,
        "no_recomendacion": _NO_RECOMENDACION,
        "disclaimer": res.rastro.disclaimer,
        "simulacion_id": res.simulacion_id,
    }


def crear_servidor(directorio_mortalidad: Path = DIR_MORTALIDAD) -> FastMCP:
    """Arma el servidor MCP cableando los adaptadores reales sobre el caso de uso."""
    simulador = SimuladorMonteCarlo(
        AdaptadorMortalidad(directorio_mortalidad),
        GeneradorRetornosParametrico(),
        TarificadorConmutacion(),
    )
    caso_uso = CompararModalidades(simulador, RepositorioSimulacionesMemoria())
    mcp: FastMCP = FastMCP("cauce", instructions=INSTRUCCIONES)

    def _comparar(
        edad: int, saldo_uf: Decimal, genero: str, supuestos: Supuestos, n_trayectorias: int
    ) -> dict[str, Any]:
        perfil = _construir_perfil(edad, saldo_uf, genero, supuestos)
        res = caso_uso.ejecutar(perfil, n_trayectorias)
        return _formatear(edad, saldo_uf, genero, supuestos, res)

    @mcp.tool
    def comparar_modalidades(
        edad: int, saldo_uf: float, genero: str, n_trayectorias: int = 5000
    ) -> dict[str, Any]:
        """Compara Retiro Programado vs Renta Vitalicia para una persona.

        Usa supuestos calibrados a tasas públicas reguladas (SP/CMF). Devuelve, por modalidad,
        la mesada inicial, cómo evoluciona, la herencia esperada y qué riesgo domina, más el
        disclaimer. NO recomienda ninguna modalidad: redirige la decisión a la AFP/asesor/SCOMP.

        Args:
            edad: edad de la persona (años).
            saldo_uf: saldo previsional acumulado, en UF.
            genero: 'M'/'Hombre' o 'F'/'Mujer' (para las tablas de mortalidad).
            n_trayectorias: número de escenarios Monte Carlo (default 5000).
        """
        supuestos = Supuestos(
            retorno_esperado=Decimal("0.03"),
            volatilidad=Decimal("0.10"),
            inflacion=Decimal("0.03"),
            tasa_descuento=TASA_DESCUENTO_RP,
            tasa_rv=TASA_RV_VEJEZ,
        )
        return _comparar(edad, Decimal(str(saldo_uf)), genero, supuestos, n_trayectorias)

    @mcp.tool
    def simular_escenario(
        edad: int,
        saldo_uf: float,
        genero: str,
        retorno_esperado: float = 0.03,
        inflacion: float = 0.03,
        tasa_descuento: float = float(TASA_DESCUENTO_RP),
        tasa_rv: float = float(TASA_RV_VEJEZ),
        n_trayectorias: int = 5000,
    ) -> dict[str, Any]:
        """'¿Y si...?' Recalcula la comparación con supuestos económicos distintos.

        Para explorar sensibilidad: retornos peores/mejores, otra inflación, u otras tasas
        técnica (RP) y de la compañía (RV). Misma salida y mismo disclaimer; tampoco recomienda.

        Args:
            edad: edad de la persona (años).
            saldo_uf: saldo previsional acumulado, en UF.
            genero: 'M'/'Hombre' o 'F'/'Mujer'.
            retorno_esperado: retorno real anual esperado (fracción, p.ej. 0.03 = 3%).
            inflacion: inflación anual (fracción).
            tasa_descuento: tasa de interés técnica del Retiro Programado (fracción).
            tasa_rv: tasa de la compañía para la Renta Vitalicia (fracción).
            n_trayectorias: número de escenarios Monte Carlo (default 5000).
        """
        supuestos = Supuestos(
            retorno_esperado=Decimal(str(retorno_esperado)),
            volatilidad=Decimal("0.10"),
            inflacion=Decimal(str(inflacion)),
            tasa_descuento=Decimal(str(tasa_descuento)),
            tasa_rv=Decimal(str(tasa_rv)),
        )
        return _comparar(edad, Decimal(str(saldo_uf)), genero, supuestos, n_trayectorias)

    return mcp


mcp = crear_servidor()


def main() -> None:
    """Punto de entrada para Claude Desktop (stdio)."""
    mcp.run()


if __name__ == "__main__":
    main()
