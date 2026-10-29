from app.config import Settings


def test_database_url_do_provedor_e_adaptada_ao_asyncpg():
    settings = Settings(database_url="postgres://u:p@host-pooler.neon.tech/db?sslmode=require&channel_binding=require")

    assert settings.database_url == "postgresql+asyncpg://u:p@host-pooler.neon.tech/db?ssl=require"


def test_database_url_asyncpg_permanece_inalterada():
    url = "postgresql+asyncpg://postgres:postgres@postgres:5432/faq_chatbot"

    assert Settings(database_url=url).database_url == url


def test_cors_origins_aceita_lista_separada_por_virgula():
    settings = Settings(cors_origins="https://a.example, https://b.example")

    assert settings.cors_origins_list == ["https://a.example", "https://b.example"]
