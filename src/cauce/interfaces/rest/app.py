"""Adaptador REST (FastAPI) — composition root del MVP de des-acumulación.

Es la única capa que cablea los adaptadores concretos (mortalidad, retornos, tarificador,
persistencia) sobre el caso de uso. **Toda respuesta incluye el disclaimer de no-asesoría**
(C-21/ADR-009): la comparación se entrega siempre con sus supuestos y su rastro.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from cauce.application.comparar_modalidades import CompararModalidades
from cauce.application.proyectar_acumulacion import ProyectarAcumulacion
from cauce.application.simular_ciclo_de_vida import SimularCicloDeVida
from cauce.domain.entities.modalidad import Modalidad
from cauce.domain.entities.perfil_acumulacion import PerfilAcumulacion
from cauce.domain.entities.perfil_previsional import PerfilPrevisional
from cauce.domain.entities.persona import Persona
from cauce.domain.entities.senda_planeo import SendaDePlaneo
from cauce.domain.services.comparador_modalidades import MetricasModalidad
from cauce.domain.value_objects.edad import Edad
from cauce.domain.value_objects.genero import Genero
from cauce.domain.value_objects.saldo import SaldoPrevisional
from cauce.domain.value_objects.supuestos import Supuestos
from cauce.domain.value_objects.supuestos_acumulacion import SupuestosAcumulacion
from cauce.infrastructure.calibracion.tasas_reguladas import (
    TASA_DESCUENTO_RP,
    TASA_RV_VEJEZ,
)
from cauce.infrastructure.mortalidad.adaptador import AdaptadorMortalidad
from cauce.infrastructure.persistencia.memoria import RepositorioSimulacionesMemoria
from cauce.infrastructure.retornos.parametrico import GeneradorRetornosParametrico
from cauce.infrastructure.simulacion.acumulacion import SimuladorAcumulacion
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


class CicloVidaRequest(BaseModel):
    """Insumos de una simulación de ciclo de vida: acumulación + des-acumulación (Fase 4)."""

    edad_inicial: int = Field(ge=18, le=70)
    edad_jubilacion: int = Field(ge=50, le=80)
    genero: str = Field(description="Sexo registral: 'F' o 'M'")
    saldo_inicial_uf: Decimal = Field(default=Decimal("0"), ge=0)
    cotizacion_anual_uf: Decimal = Field(gt=0)
    # Glide path (ADR-015): sensibilidad_riqueza=0 -> clásica solo por edad.
    w_joven: float = Field(default=0.9, ge=0, le=1)
    w_final: float = Field(default=0.2, ge=0, le=1)
    sensibilidad_riqueza: float = Field(default=0.5, ge=0)
    # Supuestos de acumulación (activo riesgoso / seguro), reales anuales.
    retorno_riesgoso: Decimal = Decimal("0.05")
    volatilidad_riesgosa: Decimal = Decimal("0.16")
    retorno_seguro: Decimal = Decimal("0.01")
    # Supuestos de des-acumulación (defaults calibrados SP/CMF, ADR-014).
    retorno_esperado: Decimal = Decimal("0.03")
    volatilidad: Decimal = Decimal("0.10")
    inflacion: Decimal = Decimal("0.03")
    tasa_descuento: Decimal = TASA_DESCUENTO_RP
    tasa_rv: Decimal = TASA_RV_VEJEZ
    margen_rv: Decimal = Field(default=Decimal("0"), ge=0, lt=1)
    semilla: int = 42
    n_acumulacion: int = Field(default=10_000, ge=1, le=200_000)
    n_desacumulacion: int = Field(default=5_000, ge=1, le=200_000)
    modalidades: list[str] = Field(default=["retiro_programado", "rv_inmediata"])


class AcumulacionResponse(BaseModel):
    saldo_p10_uf: Decimal
    saldo_p50_uf: Decimal
    saldo_p90_uf: Decimal
    saldo_esperado_uf: Decimal


class PensionPercentilResponse(BaseModel):
    percentil: str
    saldo_uf: Decimal
    modalidades: list[MetricaResponse]


class CicloVidaResponse(BaseModel):
    acumulacion: AcumulacionResponse
    pensiones: list[PensionPercentilResponse]
    disclaimer: str


def _metricas_response(
    metricas: Mapping[Modalidad, MetricasModalidad],
) -> list[MetricaResponse]:
    return [
        MetricaResponse(
            modalidad=mod.value,
            mesada_inicial_uf=m.mesada_inicial_uf,
            herencia_esperada_uf=m.herencia_esperada_uf,
            herencia_p50_uf=m.herencia_p50_uf,
            erosion_mediana=m.erosion_mediana,
            riesgo_dominante=m.riesgo_dominante,
        )
        for mod, m in metricas.items()
    ]


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
    proyectar = ProyectarAcumulacion(SimuladorAcumulacion())
    ciclo_uso = SimularCicloDeVida(proyectar, caso_uso)

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
            modalidades=_metricas_response(resultado.metricas_por_modalidad),
            disclaimer=resultado.rastro.disclaimer,
        )

    @app.post("/ciclo-vida", response_model=CicloVidaResponse)
    def ciclo_vida(req: CicloVidaRequest) -> CicloVidaResponse:
        try:
            genero = Genero(req.genero.upper())
            modalidades = [Modalidad(m) for m in req.modalidades]
            senda = SendaDePlaneo(
                nombre="perfil",
                edad_inicial=req.edad_inicial,
                edad_jubilacion=req.edad_jubilacion,
                w_joven=req.w_joven,
                w_final=req.w_final,
                sensibilidad_riqueza=req.sensibilidad_riqueza,
            )
            perfil_acum = PerfilAcumulacion(
                id="rest-ciclo",
                version=1,
                genero=genero,
                edad_inicial=Edad(req.edad_inicial),
                edad_jubilacion=Edad(req.edad_jubilacion),
                saldo_inicial=SaldoPrevisional(req.saldo_inicial_uf),
                cotizacion_anual=SaldoPrevisional(req.cotizacion_anual_uf),
                senda=senda,
                supuestos=SupuestosAcumulacion(
                    retorno_riesgoso=req.retorno_riesgoso,
                    volatilidad_riesgosa=req.volatilidad_riesgosa,
                    retorno_seguro=req.retorno_seguro,
                ),
                semilla=req.semilla,
            )
            sup_desac = Supuestos(
                retorno_esperado=req.retorno_esperado,
                volatilidad=req.volatilidad,
                inflacion=req.inflacion,
                tasa_descuento=req.tasa_descuento,
                tasa_rv=req.tasa_rv,
                margen_rv=req.margen_rv,
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        try:
            res = ciclo_uso.ejecutar(
                perfil_acum,
                sup_desac,
                "2020",
                modalidades,
                req.n_acumulacion,
                req.n_desacumulacion,
                req.semilla,
            )
        except (ValueError, NotImplementedError) as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        m = res.acumulacion
        return CicloVidaResponse(
            acumulacion=AcumulacionResponse(
                saldo_p10_uf=m.saldo_p10_uf,
                saldo_p50_uf=m.saldo_p50_uf,
                saldo_p90_uf=m.saldo_p90_uf,
                saldo_esperado_uf=m.saldo_esperado_uf,
            ),
            pensiones=[
                PensionPercentilResponse(
                    percentil=p.percentil,
                    saldo_uf=p.saldo_uf,
                    modalidades=_metricas_response(p.comparacion.metricas_por_modalidad),
                )
                for p in res.pensiones
            ],
            disclaimer=res.disclaimer,
        )

    return app


app = crear_app()
