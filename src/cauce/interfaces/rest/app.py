"""Adaptador REST (FastAPI) — composition root del MVP de des-acumulación.

Es la única capa que cablea los adaptadores concretos (mortalidad, retornos, tarificador,
persistencia) sobre el caso de uso. **Toda respuesta incluye el disclaimer de no-asesoría**
(C-21/ADR-009): la comparación se entrega siempre con sus supuestos y su rastro.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from cauce.application.comparar_modalidades import CompararModalidades
from cauce.domain.entities.modalidad import Modalidad
from cauce.domain.entities.perfil_previsional import PerfilPrevisional
from cauce.domain.entities.persona import Persona
from cauce.domain.value_objects.edad import Edad
from cauce.domain.value_objects.genero import Genero
from cauce.domain.value_objects.saldo import SaldoPrevisional
from cauce.domain.value_objects.supuestos import Supuestos
from cauce.infrastructure.calibracion.tasas_reguladas import (
    TASA_DESCUENTO_RP,
    TASA_RV_VEJEZ,
)
from cauce.infrastructure.mortalidad.adaptador import AdaptadorMortalidad
from cauce.infrastructure.persistencia.memoria import RepositorioSimulacionesMemoria
from cauce.infrastructure.retornos.parametrico import GeneradorRetornosParametrico
from cauce.infrastructure.simulacion.montecarlo import SimuladorMonteCarlo
from cauce.infrastructure.tarificacion.conmutacion import TarificadorConmutacion

DIR_MORTALIDAD = Path(__file__).resolve().parents[4] / "data" / "mortalidad"
# Frontend de orientación familiar, servido por la misma app (ADR-012).
WEB_INDEX = Path(__file__).resolve().parents[1] / "web" / "index.html"


class PerfilRequest(BaseModel):
    """Insumos de una comparación (datos sintéticos, nunca una persona real)."""

    edad: int = Field(ge=0, le=120)
    saldo_uf: Decimal = Field(gt=0)
    genero: str = Field(description="Sexo registral: 'F' o 'M'")
    retorno_esperado: Decimal = Decimal("0.03")
    volatilidad: Decimal = Decimal("0.10")
    inflacion: Decimal = Decimal("0.03")
    # Defaults calibrados a tasas públicas reguladas SP/CMF (ADR-014); el cliente puede
    # sobrescribirlos. Son promedios de mercado, no la oferta personal del SCOMP.
    tasa_descuento: Decimal = TASA_DESCUENTO_RP  # TITRP (interés técnico del RP)
    tasa_rv: Decimal = TASA_RV_VEJEZ  # tasa media RV Vejez (C-28)
    margen_rv: Decimal = Field(default=Decimal("0"), ge=0, lt=1)  # carga comercial RV (C-27)
    semilla: int = 42
    n_trayectorias: int = Field(default=10_000, ge=1, le=200_000)
    modalidades: list[str] = Field(default=["retiro_programado", "rv_inmediata"])


class MetricaResponse(BaseModel):
    modalidad: str
    mesada_inicial_uf: Decimal
    herencia_esperada_uf: Decimal
    herencia_p50_uf: Decimal
    erosion_mediana: float
    riesgo_dominante: str


class ComparacionResponse(BaseModel):
    simulacion_id: str
    n_trayectorias: int
    modalidades: list[MetricaResponse]
    disclaimer: str


def _construir_perfil(req: PerfilRequest) -> PerfilPrevisional:
    try:
        genero = Genero(req.genero.upper())
        modalidades = [Modalidad(m) for m in req.modalidades]
        persona = Persona(Edad(req.edad), SaldoPrevisional(req.saldo_uf), genero)
        supuestos = Supuestos(
            retorno_esperado=req.retorno_esperado,
            volatilidad=req.volatilidad,
            inflacion=req.inflacion,
            tasa_descuento=req.tasa_descuento,
            tasa_rv=req.tasa_rv,
            margen_rv=req.margen_rv,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return PerfilPrevisional(
        id="rest",
        version=1,
        persona=persona,
        supuestos=supuestos,
        modalidades_a_comparar=modalidades,
        tabla_mortalidad="2020",
        semilla=req.semilla,
    )


def crear_app(directorio_mortalidad: Path = DIR_MORTALIDAD) -> FastAPI:
    """Arma la app cableando los adaptadores reales sobre el caso de uso."""
    simulador = SimuladorMonteCarlo(
        AdaptadorMortalidad(directorio_mortalidad),
        GeneradorRetornosParametrico(),
        TarificadorConmutacion(),
    )
    caso_uso = CompararModalidades(simulador, RepositorioSimulacionesMemoria())

    app = FastAPI(
        title="Cauce — Comparador de modalidades de pensión",
        description="Simulador educativo. NO constituye asesoría previsional.",
        version="0.1.0",
    )

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        """Web de orientación familiar: cero instalación, consume /comparar (ADR-012)."""
        return FileResponse(WEB_INDEX, media_type="text/html")

    @app.post("/comparar", response_model=ComparacionResponse)
    def comparar(req: PerfilRequest) -> ComparacionResponse:
        perfil = _construir_perfil(req)
        try:
            resultado = caso_uso.ejecutar(perfil, req.n_trayectorias)
        except (ValueError, NotImplementedError) as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        return ComparacionResponse(
            simulacion_id=resultado.simulacion_id,
            n_trayectorias=resultado.rastro.n_trayectorias,
            modalidades=[
                MetricaResponse(
                    modalidad=mod.value,
                    mesada_inicial_uf=m.mesada_inicial_uf,
                    herencia_esperada_uf=m.herencia_esperada_uf,
                    herencia_p50_uf=m.herencia_p50_uf,
                    erosion_mediana=m.erosion_mediana,
                    riesgo_dominante=m.riesgo_dominante,
                )
                for mod, m in resultado.metricas_por_modalidad.items()
            ],
            disclaimer=resultado.rastro.disclaimer,
        )

    return app


app = crear_app()
