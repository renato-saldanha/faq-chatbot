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
            (
                "Como recupero minha senha?",
                "Clique em 'Esqueci minha senha' na tela de login e siga as instruções enviadas por e-mail.",
            ),
            ("Como cancelo minha conta?", "Entre em contato pelo suporte para solicitar o encerramento do cadastro."),
            ("Posso mudar meu e-mail de cadastro?", "Sim, isso pode ser feito nas configurações da conta."),
            (
                "Não lembro qual e-mail usei para me cadastrar, como descubro?",
                "Entre em contato pelo suporte informando seu nome completo e telefone para localizarmos o cadastro.",
            ),
            (
                "Como altero minha senha atual?",
                "Acesse configurações da conta, opção 'Segurança', e defina uma nova senha.",
            ),
            (
                "Posso ter mais de uma conta com o mesmo e-mail?",
                "Não, cada e-mail pode estar vinculado a apenas uma conta.",
            ),
            (
                "Como excluo meus dados pessoais?",
                "Solicite a exclusão pelo suporte — o processo segue a LGPD e leva até 15 dias úteis.",
            ),
            (
                "Meu login foi bloqueado, o que houve?",
                "Bloqueios ocorrem após várias tentativas de senha incorreta — aguarde 15 minutos ou redefina a senha.",
            ),
            (
                "Como ativo a verificação em duas etapas?",
                "Acesse configurações de segurança e ative a opção 'Verificação em duas etapas', vinculando um app.",
            ),
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
            (
                "O pagamento por Pix demora quanto tempo para confirmar?",
                "A confirmação do Pix costuma ocorrer em poucos minutos após o pagamento.",
            ),
            (
                "Posso emitir nota fiscal da compra?",
                "Sim, a nota fiscal é enviada automaticamente por e-mail após a confirmação do pagamento.",
            ),
            (
                "O que fazer se meu cartão foi recusado?",
                "Confirme os dados do cartão e o limite disponível, ou tente outra forma de pagamento.",
            ),
            (
                "Como cancelo uma assinatura recorrente?",
                "Acesse 'Minhas assinaturas' nas configurações e selecione 'Cancelar renovação automática'.",
            ),
            (
                "É possível pagar com mais de um cartão?",
                "No momento cada pedido aceita apenas um método de pagamento por vez.",
            ),
        ],
    ),
    (
        "suporte",
        "Suporte Técnico",
        [
            (
                "O aplicativo não abre, o que faço?",
                "Tente reinstalar o aplicativo ou verificar atualizações disponíveis.",
            ),
            ("Como reporto um bug?", "Envie os detalhes do problema pelo formulário de contato do suporte."),
            ("O site está fora do ar?", "Verifique nossa página de status para atualizações sobre disponibilidade."),
            ("Como falo com um atendente humano?", "Use o botão de contato no rodapé do site para abrir um chamado."),
            ("Qual o horário de atendimento?", "Nosso suporte funciona de segunda a sexta, das 9h às 18h."),
            (
                "O aplicativo está muito lento, o que fazer?",
                "Feche outros aplicativos em segundo plano e verifique sua conexão com a internet.",
            ),
            (
                "Como limpo o cache do aplicativo?",
                "Acesse as configurações do seu dispositivo, encontre o aplicativo e selecione 'Limpar cache'.",
            ),
            (
                "Perdi o acesso ao meu e-mail cadastrado, como faço?",
                "Entre em contato com o suporte apresentando um documento para verificação de identidade.",
            ),
            (
                "Existe suporte por telefone?",
                "No momento o atendimento é feito por chat e e-mail — não oferecemos suporte telefônico.",
            ),
            (
                "Como acompanho o status do meu chamado?",
                "Acesse 'Meus chamados' na área de suporte para ver o andamento e histórico de respostas.",
            ),
        ],
    ),
    (
        "entrega",
        "Entrega",
        [
            ("Qual o prazo de entrega?", "O prazo padrão é de 5 a 10 dias úteis, dependendo da sua região."),
            ("Como rastreio meu pedido?", "Acesse 'Meus pedidos' e clique em 'Rastrear' para ver a localização atual."),
            (
                "Posso alterar o endereço de entrega após a compra?",
                "Sim, desde que o pedido ainda não tenha sido despachado.",
            ),
            (
                "O que faço se o pedido não chegou no prazo?",
                "Entre em contato com o suporte informando o número do pedido para investigação.",
            ),
            (
                "Vocês entregam em todo o Brasil?",
                "Sim, entregamos para todos os estados, com prazos variando por região.",
            ),
            (
                "Como funciona a entrega expressa?",
                "A entrega expressa reduz o prazo para até 2 dias úteis em regiões atendidas, com custo adicional.",
            ),
            (
                "Recebi um produto errado, o que faço?",
                "Entre em contato pelo suporte em até 7 dias para solicitar troca sem custo.",
            ),
            (
                "É possível retirar o pedido em loja física?",
                "Sim, selecione a opção 'Retirar na loja' durante o checkout, quando disponível na sua região.",
            ),
        ],
    ),
    (
        "conta-premium",
        "Conta Premium",
        [
            (
                "O que está incluso no plano Premium?",
                "O plano Premium inclui suporte prioritário, frete grátis e acesso antecipado a promoções.",
            ),
            (
                "Como faço upgrade para o plano Premium?",
                "Acesse 'Minha assinatura' nas configurações e selecione 'Fazer upgrade'.",
            ),
            (
                "Posso cancelar o Premium a qualquer momento?",
                "Sim, o cancelamento pode ser feito a qualquer momento, sem multa.",
            ),
            (
                "O plano Premium tem período de teste gratuito?",
                "Sim, oferecemos 7 dias de teste gratuito para novos assinantes.",
            ),
            (
                "Quais os valores do plano Premium?",
                "Consulte os valores atualizados na página 'Planos', dentro das configurações da conta.",
            ),
            (
                "Perco os benefícios se atrasar o pagamento do Premium?",
                "Sim, os benefícios ficam suspensos até a regularização do pagamento.",
            ),
        ],
    ),
    (
        "seguranca",
        "Segurança e Privacidade",
        [
            (
                "Meus dados são compartilhados com terceiros?",
                "Não compartilhamos dados pessoais com terceiros sem seu consentimento, conforme a LGPD.",
            ),
            (
                "Como denuncio uma atividade suspeita na minha conta?",
                "Use 'Denunciar atividade suspeita' nas configurações de segurança ou contate o suporte.",
            ),
            (
                "Vocês armazenam os dados do meu cartão de crédito?",
                "Não — o processamento é feito por um parceiro de pagamento certificado, dados não passam por nós.",
            ),
            (
                "Como faço para baixar uma cópia dos meus dados?",
                "Solicite pela opção 'Exportar meus dados' nas configurações de privacidade da conta.",
            ),
            (
                "Recebi um e-mail suspeito em nome da empresa, o que faço?",
                "Não clique em links suspeitos e encaminhe o e-mail para nosso canal de segurança para análise.",
            ),
            (
                "Posso usar login social (Google/Apple) para acessar minha conta?",
                "Sim, você pode vincular sua conta a um login social nas configurações de segurança.",
            ),
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
