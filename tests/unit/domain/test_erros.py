from cadastro_cliente.domain.erros import (
    ClienteNaoEncontradoError,
    ColetorErros,
    DadosInvalidosError,
    DocumentoDuplicadoError,
    ErroCampo,
)


def test_dados_invalidos_carrega_lista_de_erros():
    erros = [ErroCampo("email", "email_invalido", "E-mail inválido.")]
    exc = DadosInvalidosError(erros)
    assert exc.erros == erros


def test_mensagens_nao_contem_valor_informado():
    coletor = ColetorErros()
    coletor.texto("x" * 300, "nome", 2, 150)
    coletor.texto("   ", "bairro", 1, 100)
    for erro in coletor.erros:
        assert "xxx" not in erro.message


def test_coletor_acumula_e_verifica():
    coletor = ColetorErros()
    assert coletor.texto("  Ana  ", "nome", 2, 150) == "Ana"
    assert coletor.texto("", "nome", 2, 150) is None
    assert coletor.texto(None, "complemento", 0, 100, obrigatorio=False) is None
    assert [e.code for e in coletor.erros] == ["obrigatorio"]
    try:
        coletor.verificar()
    except DadosInvalidosError as exc:
        assert exc.erros[0].field == "nome"
    else:
        raise AssertionError("deveria lançar DadosInvalidosError")


def test_erros_de_negocio_tem_codigo():
    assert DocumentoDuplicadoError().erro.code == "documento_duplicado"
    assert ClienteNaoEncontradoError().erro.code == "cliente_nao_encontrado"
