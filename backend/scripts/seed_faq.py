import asyncio

from sqlalchemy import select

from app.db import async_session_maker
from app.models import Categoria, FaqItem

SEED = [
    (
        "conta",
        "Conta",
        [
            ("Como eu cadastro uma conta nova?", "Acesse a página de cadastro e preencha seu e-mail e senha."),
            ("Como recupero minha senha?", "Clique em 'Esqueci minha senha' na tela de login e siga as instruções enviadas por e-mail."),
            ("Como cancelo minha conta?", "Entre em contato pelo suporte para solicitar o encerramento do cadastro."),
            ("Posso mudar meu e-mail de cadastro?", "Sim, isso pode ser feito nas configurações da conta."),
            ("Esqueci meu login, o que fazer?", "Use a opção 'Esqueci minha senha' informando o e-mail cadastrado."),
        ],
    ),
    (
        "pagamentos",
        "Pagamentos",
        [
            ("Quais formas de pagamento são aceitas?", "Aceitamos cartão de crédito, boleto e Pix."),
            ("Como solicito reembolso?", "Solicite o reembolso pelo suporte em até 7 dias após a compra."),
            ("A fatura não chegou, o que faço?", "Verifique sua caixa de spam ou entre em contato com o suporte."),
            ("Posso parcelar minha compra?", "Sim, em até 12x no cartão de crédito."),
            ("Como altero o cartão cadastrado?", "Acesse configurações de pagamento e edite o cartão salvo."),
        ],
    ),
    (
        "suporte",
        "Suporte Técnico",
        [
            ("O aplicativo não abre, o que faço?", "Tente reinstalar o aplicativo ou verificar atualizações disponíveis."),
            ("Como reporto um bug?", "Envie os detalhes do problema pelo formulário de contato do suporte."),
            ("O site está fora do ar?", "Verifique nossa página de status para atualizações sobre disponibilidade."),
            ("Como falo com um atendente humano?", "Use o botão de contato no rodapé do site para abrir um chamado."),
            ("Qual o horário de atendimento?", "Nosso suporte funciona de segunda a sexta, das 9h às 18h."),
        ],
    ),
]


async def seed() -> None:
    async with async_session_maker() as session:
        result = await session.execute(select(FaqItem.id).limit(1))
        if result.first() is not None:
            print("Base de FAQ já populada, pulando seed.")
            return

        for slug, nome, perguntas in SEED:
            categoria = Categoria(nome=nome, slug=slug)
            session.add(categoria)
            await session.flush()
            for pergunta, resposta in perguntas:
                session.add(FaqItem(categoria_id=categoria.id, pergunta=pergunta, resposta=resposta))
        await session.commit()
        print(f"Seed concluído: {sum(len(p) for _, _, p in SEED)} perguntas em {len(SEED)} categorias.")


if __name__ == "__main__":
    asyncio.run(seed())
