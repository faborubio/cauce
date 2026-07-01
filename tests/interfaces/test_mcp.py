"""Tests de la capa MCP (Fase 3): herramientas, disclaimer (C-21) y guardrail C-22.

Sin pytest-asyncio: el round-trip del cliente FastMCP se ejecuta con ``asyncio.run``.
"""

import asyncio
from pathlib import Path
from typing import Any

from fastmcp import Client

from cauce.interfaces.mcp.server import INSTRUCCIONES, crear_servidor

DIR_MORTALIDAD = Path(__file__).resolve().parents[2] / "data" / "mortalidad"


def _llamar(nombre: str, args: dict[str, Any]) -> dict[str, Any]:
    mcp = crear_servidor(DIR_MORTALIDAD)

    async def go() -> dict[str, Any]:
        async with Client(mcp) as cliente:
            resultado = await cliente.call_tool(nombre, args)
            return resultado.data  # type: ignore[no-any-return]

    return asyncio.run(go())


def test_tools_registradas() -> None:
    mcp = crear_servidor(DIR_MORTALIDAD)

    async def go() -> list[str]:
        async with Client(mcp) as cliente:
            return [t.name for t in await cliente.list_tools()]

    assert set(asyncio.run(go())) == {
        "comparar_modalidades",
        "simular_escenario",
        "proyectar_ciclo_vida",
    }


def test_comparar_lleva_disclaimer_y_no_recomendacion() -> None:
    args = {"edad": 66, "saldo_uf": 3000, "genero": "M", "n_trayectorias": 400}
    d = _llamar("comparar_modalidades", args)
    # C-21: disclaimer con encuadre paramétrico en cada salida.
    assert "NO constituye asesoría" in d["disclaimer"]
    assert "ilustrativos" in d["disclaimer"] and "SCOMP" in d["disclaimer"]
    # C-22: la salida nunca recomienda y redirige.
    assert "NO recomienda" in d["no_recomendacion"]


def test_comparar_evolucion_rp_baja_rv_fija() -> None:
    args = {"edad": 66, "saldo_uf": 3000, "genero": "M", "n_trayectorias": 600}
    d = _llamar("comparar_modalidades", args)
    por_mod = {m["modalidad"]: m for m in d["modalidades"]}
    assert "Baja" in por_mod["retiro_programado"]["evolucion"]
    assert por_mod["rv_inmediata"]["evolucion"] == "Se mantiene fija de por vida"
    assert por_mod["rv_inmediata"]["herencia_esperada_uf"] == 0.0


def test_simular_escenario_acepta_supuestos() -> None:
    args = {
        "edad": 65,
        "saldo_uf": 2500,
        "genero": "F",
        "retorno_esperado": 0.01,
        "n_trayectorias": 400,
    }
    d = _llamar("simular_escenario", args)
    assert d["entrada"]["supuestos"]["retorno_esperado"] == 0.01
    assert "NO constituye asesoría" in d["disclaimer"]


def test_proyectar_ciclo_vida() -> None:
    args = {
        "edad_inicial": 25,
        "edad_jubilacion": 65,
        "genero": "F",
        "cotizacion_anual_uf": 60,
        "n_acumulacion": 500,
        "n_desacumulacion": 250,
    }
    d = _llamar("proyectar_ciclo_vida", args)
    assert [p["percentil"] for p in d["pensiones_por_percentil"]] == ["p10", "p50", "p90"]
    assert "NO constituye asesoría" in d["disclaimer"]
    assert "NO recomienda" in d["no_recomendacion"]


def test_servidor_instruye_no_recomendar_c22() -> None:
    # C-22 codificado a nivel servidor: el host recibe la regla de no recomendar y redirigir.
    assert "NUNCA recomiendes" in INSTRUCCIONES
    assert "SCOMP" in INSTRUCCIONES
