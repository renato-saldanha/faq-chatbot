export interface Categoria {
  id: number;
  nome: string;
  slug: string;
}

export interface FaqItem {
  id: number;
  categoria_id: number;
  categoria_nome: string;
  pergunta: string;
  resposta: string;
  ativo: boolean;
}

export interface ChatAskRequest {
  pergunta: string;
}

export interface ChatAskResponse {
  resposta: string;
  faq_item_id: number | null;
  categoria: string | null;
  sem_resposta: boolean;
  score: number | null;
}

export interface MetricsSummary {
  total_conversas: number;
  total_sem_resposta: number;
  taxa_sem_resposta: number;
}

export interface DailyCount {
  data: string;
  quantidade: number;
}

export interface TopQuestion {
  faq_item_id: number;
  pergunta: string;
  quantidade: number;
}

export interface CategoryBreakdown {
  categoria: string;
  quantidade: number;
}

export interface UnansweredQuestion {
  id: number;
  pergunta_usuario: string;
  criado_em: string;
}
