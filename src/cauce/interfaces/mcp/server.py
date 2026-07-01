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
from cauce.application.proyectar_acumulacion import ProyectarAcumulacion
from cauce.application.simular_ciclo_de_vida import ResultadoCicloDeVida, SimularCicloDeVida
from cauce.domain.entities.modalidad import Modalidad
from cauce.domain.entities.perfil_acumulacion import PerfilAcumulacion
from cauce.domain.entities.perfil_previsional import PerfilPrevisional
from cauce.domain.entities.persona import Persona
from cauce.domain.entities.senda_planeo import SendaDePlaneo
from cauce.domain.value_objects.edad import Edad
from cauce.domain.value_objects.genero import Genero
from cauce.domain.value_objects.saldo import SaldoPrevisional
from cauce.domain.value_objects.supuestos import Supuestos
from cauce.domain.value_objects.supuestos_acumulacion import SupuestosAcumulacion
from cauce.infrastructure.calibracion.tasas_reguladas import (
    TASA_DESCUENTO_RP,
    TASA_DESCUENTO_RP_FUENTE,
    TASA_RV_VEJEZ,
    TASA_RV_VEJEZ_FUENTE,
)
from cauce.infrastructure.mortalidad.adaptador import AdaptadorMortalidad
from cauce.infrastructure.persistencia.memoria import RepositorioSimulacionesMemoria
from cauce.infrastructure.retornos.parametrico import GeneradorRetornosParametrico
from cauce.infrastructure.simulacion.acumulacion import SimuladorAcumulacion
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
    modalidades = _modalidades_payload(res)
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


def _modalidades_payload(res: ResultadoComparacion) -> list[dict[str, Any]]:
    return [
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


def _formatear_ciclo(res: ResultadoCicloDeVida) -> dict[str, Any]:
    m = res.acumulacion
    return {
        "acumulacion_saldo_a_jubilacion_uf": {
            "p10": round(float(m.saldo_p10_uf)),
            "p50": round(float(m.saldo_p50_uf)),
            "p90": round(float(m.saldo_p90_uf)),
            "esperado": round(float(m.saldo_esperado_uf)),
        },
        "pensiones_por_percentil": [
            {
                "percentil": p.percentil,
                "saldo_uf": round(float(p.saldo_uf)),
                "modalidades": _modalidades_payload(p.comparacion),
            }
            for p in res.pensiones
        ],
        "no_recomendacion": _NO_RECOMENDACION,
        "disclaimer": res.disclaimer,
    }


def crear_servidor(directorio_mortalidad: Path = DIR_MORTALIDAD) -> FastMCP:
    """Arma el servidor MCP cableando los adaptadores reales sobre el caso de uso."""
    simulador = SimuladorMonteCarlo(
        AdaptadorMortalidad(directorio_mortalidad),
        GeneradorRetornosParametrico(),
        TarificadorConmutacion(),
    )
    caso_uso = CompararModalidades(simulador, RepositorioSimulacionesMemoria())
    ciclo_uso = SimularCicloDeVida(ProyectarAcumulacion(SimuladorAcumulacion()), caso_uso)
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

    @mcp.tool
    def proyectar_ciclo_vida(
        edad_inicial: int,
        edad_jubilacion: int,
        genero: str,
        cotizacion_anual_uf: float,
        saldo_inicial_uf: float = 0.0,
        w_joven: float = 0.9,
        w_final: float = 0.2,
        sensibilidad_riqueza: float = 0.5,
        n_acumulacion: int = 5000,
        n_desacumulacion: int = 3000,
    ) -> dict[str, Any]:
        """Ciclo de vida completo: de la cotización a la mesada (Fase 4).

        Proyecta la acumulación con un glide path que depende de edad Y riqueza (ADR-015) y
        compara modalidades para tres saldos representativos a la jubilación (p10/p50/p90) →
        un rango de pensiones según cómo le vaya al ahorro. Supuestos de des-acumulación
        calibrados (SP/CMF). No recomienda: redirige la decisión a la AFP/asesor/SCOMP.

        Args:
            edad_inicial: edad al empezar a cotizar (años).
            edad_jubilacion: edad de jubilación (años).
            genero: 'M'/'Hombre' o 'F'/'Mujer'.
            cotizacion_anual_uf: aporte anual en UF.
            saldo_inicial_uf: saldo ya acumulado, en UF (default 0).
            w_joven: fracción en activo riesgoso al inicio (0..1).
            w_final: fracción en activo riesgoso a la jubilación (0..1).
            sensibilidad_riqueza: 0 = glide clásico por edad; >0 = ajuste por riqueza.
            n_acumulacion: escenarios Monte Carlo de acumulación (default 5000).
            n_desacumulacion: escenarios de des-acumulación por percentil (default 3000).
        """
        senda = SendaDePlaneo(
            nombre="perfil",
            edad_inicial=edad_inicial,
            edad_jubilacion=edad_jubilacion,
            w_joven=w_joven,
            w_final=w_final,
            sensibilidad_riqueza=sensibilidad_riqueza,
        )
        perfil = PerfilAcumulacion(
            id="mcp-ciclo",
            version=1,
            genero=_genero(genero),
            edad_inicial=Edad(edad_inicial),
            edad_jubilacion=Edad(edad_jubilacion),
            saldo_inicial=SaldoPrevisional(Decimal(str(saldo_inicial_uf))),
            cotizacion_anual=SaldoPrevisional(Decimal(str(cotizacion_anual_uf))),
            senda=senda,
            supuestos=SupuestosAcumulacion(
                retorno_riesgoso=Decimal("0.05"),
                volatilidad_riesgosa=Decimal("0.16"),
                retorno_seguro=Decimal("0.01"),
            ),
            semilla=42,
        )
        sup_desac = Supuestos(
            retorno_esperado=Decimal("0.03"),
            volatilidad=Decimal("0.10"),
            inflacion=Decimal("0.03"),
            tasa_descuento=TASA_DESCUENTO_RP,
            tasa_rv=TASA_RV_VEJEZ,
        )
        res = ciclo_uso.ejecutar(
            perfil,
            sup_desac,
            "2020",
            [Modalidad.RETIRO_PROGRAMADO, Modalidad.RV_INMEDIATA],
            n_acumulacion,
            n_desacumulacion,
        )
        return _formatear_ciclo(res)

    return mcp


mcp = crear_servidor()


def main() -> None:
    """Punto de entrada para Claude Desktop (stdio)."""
    mcp.run()


if __name__ == "__main__":
    main()
