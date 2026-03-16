export type EstadoPedido =
  | "EM_ANDAMENTO"
  | "PRONTO"
  | "ENTREGUE"
  | "CANCELADO";

export interface Cliente {
  id: number;
  nome: string;
  numero: string;
  ativo: boolean;
}

export interface EstoqueItem {
  id: number;
  item: string;
  quantidade_disponivel: number;
  valor: number;
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
