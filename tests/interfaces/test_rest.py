"""Tests de la REST: comparación, disclaimer siempre presente (C-21), validación de bordes."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cauce.interfaces.rest.app import crear_app

DIR_MORTALIDAD = Path(__file__).resolve().parents[2] / "data" / "mortalidad"


@pytest.fixture
def client() -> TestClient:
    return TestClient(crear_app(DIR_MORTALIDAD))


def test_comparar_ok(client: TestClient) -> None:
    r = client.post(
        "/comparar",
        json={"edad": 65, "saldo_uf": "3000", "genero": "M", "n_trayectorias": 500},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["modalidades"]) == 2
    assert {m["modalidad"] for m in body["modalidades"]} == {"retiro_programado", "rv_inmediata"}


def test_c21_disclaimer_en_toda_salida(client: TestClient) -> None:
    r = client.post(
        "/comparar",
        json={"edad": 65, "saldo_uf": "3000", "genero": "F", "n_trayectorias": 300},
    )
    assert r.status_code == 200
    assert "NO constituye asesoría" in r.json()["disclaimer"]


def test_edad_bajo_rango_de_tabla_da_422(client: TestClient) -> None:
    # mujer de 18: bajo el rango de RV-2020-MUJERES (parte en 20) -> C-02
    r = client.post(
        "/comparar",
        json={"edad": 18, "saldo_uf": "1000", "genero": "F", "n_trayectorias": 100},
    )
    assert r.status_code == 422


def test_modalidad_mixta_no_soportada_da_422(client: TestClient) -> None:
    r = client.post(
        "/comparar",
        json={
            "edad": 65,
            "saldo_uf": "3000",
            "genero": "M",
            "n_trayectorias": 100,
            "modalidades": ["rt_rv_diferida"],
        },
    )
    assert r.status_code == 422
