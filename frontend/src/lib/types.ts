export type EstadoPedido = "EM_ANDAMENTO" | "PRONTO" | "ENTREGUE" | "CANCELADO";
export type FormaPagamento = "CARTAO" | "BOLETO" | "PIX" | "BERRIES";
export type StatusPagamento = "PENDENTE" | "CONFIRMADO" | "REJEITADO";

export interface Cliente {
  id: number;
  nome: string;
  numero: string;
  torce_flamengo: boolean;
  assiste_one_piece: boolean;
  eh_de_sousa: boolean;
  ativo: boolean;
}

export interface EstoqueItem {
  id: number;
  item: string;
  quantidade_disponivel: number;
  valor: number;
  categoria: string;
  fabricado_em_mari: boolean;
  ativo: boolean;
}

export interface PedidoItem {
  id: number;
  pedido_id: number;
  item_id: number;
  quantidade: number;
  valor_unitario: number;
}

export interface Pedido {
  id: number;
  cliente_id: number;
  cliente_nome: string;
  data: string;
  estado: EstadoPedido;
  valor: number;
  pago: boolean;
  vendedor_id: number | null;
  vendedor_nome: string | null;
  forma_pagamento: FormaPagamento | null;
  status_pagamento: StatusPagamento;
  desconto: number;
  itens: PedidoItem[];
}

export interface RelatorioVendas {
  total_pedidos: number;
  valor_total: number;
  pedidos_pagos: number;
  pedidos_nao_pagos: number;
  ticket_medio: number;
}

export interface RelatorioEstoque {
  itens_cadastrados: number;
  quantidade_total: number;
  valor_inventario: number;
  itens_sem_estoque: number;
}

export interface RelatorioClientes {
  total_clientes: number;
  clientes_com_pedidos_ativos: number;
  clientes_sem_pedidos: number;
}

export interface VendaVendedor {
  vendedor_id: number;
  vendedor_nome: string;
  mes: string;
  total_pedidos: number;
  valor_total: number;
  desconto_total: number;
  pagamentos_confirmados: number;
}
