import logging

import pytest

from app.utils.logger import get_logger

pytestmark = pytest.mark.unit


def test_retorna_logger_com_nome_correto():
    log = get_logger("meu-modulo")
    assert isinstance(log, logging.Logger)
    assert log.name == "meu-modulo"


def test_nome_padrao_e_pipeline():
    log = get_logger()
    assert log.name == "pipeline"


def test_nivel_e_info():
    log = get_logger("test-nivel")
    assert log.getEffectiveLevel() == logging.INFO


def test_mesma_instancia_para_mesmo_nome():
    log1 = get_logger("singleton")
    log2 = get_logger("singleton")
    assert log1 is log2
