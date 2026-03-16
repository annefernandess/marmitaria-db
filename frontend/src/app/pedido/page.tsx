"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { useAuth } from "@/contexts/AuthContext";
import CoxinhaCascade from "@/components/CoxinhaCascade";
import {
  ShoppingCart,
  Plus,
  Minus,
  LogOut,
  Send,
  PackageX,
  Check,
  Loader2,
  AlertCircle,
  BellRing,
  Clock3,
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import { formatCurrency, getErrorMessage } from "@/lib/format";
import type { EstoqueItem, Pedido } from "@/lib/types";

interface CartItem {
  menuItem: EstoqueItem;
  quantidade: number;
}

export default function PedidoPage() {
  const { user, logout } = useAuth();
  const [cardapio, setCardapio] = useState<EstoqueItem[]>([]);
  const [cart, setCart] = useState<Map<number, CartItem>>(new Map());
  const [pedidoEnviado, setPedidoEnviado] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [consultandoPedidos, setConsultandoPedidos] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [meusPedidos, setMeusPedidos] = useState<Pedido[]>([]);
  const nomeCliente = user?.nome.trim() ?? "";

  useEffect(() => {
    async function loadCardapio() {
      try {
        setLoading(true);
        setError(null);
        const data = await apiFetch<EstoqueItem[]>("/estoque");
        setCardapio(data);
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }

    void loadCardapio();
  }, []);

  useEffect(() => {
    async function loadMeusPedidos() {
      const nome = user?.nome.trim() ?? "";
      if (nome.length < 2) {
        setMeusPedidos([]);
        return;
      }

      try {
        setConsultandoPedidos(true);
        const data = await apiFetch<Pedido[]>("/pedidos", {
          query: { cliente_nome: nome },
        });
        setMeusPedidos(
          data.filter(
            (pedido) =>
              pedido.cliente_nome.trim().toLowerCase() === nome.toLowerCase()
          )
        );
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setConsultandoPedidos(false);
      }
    }

    void loadMeusPedidos();
  }, [user?.nome]);

  function addToCart(item: EstoqueItem) {
    setCart((prev) => {
      const next = new Map(prev);
      const existing = next.get(item.id);
      if (existing && existing.quantidade < item.quantidade_disponivel) {
        next.set(item.id, { ...existing, quantidade: existing.quantidade + 1 });
      } else if (!existing) {
        next.set(item.id, { menuItem: item, quantidade: 1 });
      }
      return next;
    });
  }

  function removeFromCart(itemId: number) {
    setCart((prev) => {
      const next = new Map(prev);
      const existing = next.get(itemId);
      if (existing && existing.quantidade > 1) {
        next.set(itemId, { ...existing, quantidade: existing.quantidade - 1 });
      } else {
        next.delete(itemId);
      }
      return next;
    });
  }

  function getQuantity(itemId: number): number {
    return cart.get(itemId)?.quantidade ?? 0;
  }

  const cartItems = Array.from(cart.values());
  const total = cartItems.reduce(
    (sum, ci) => sum + ci.menuItem.valor * ci.quantidade,
    0
  );
  const pedidosProntos = meusPedidos.filter((pedido) => pedido.estado === "PRONTO");

  async function handleEnviarPedido() {
    if (!user?.clienteId) {
      setError("Seu cadastro não possui um cliente vinculado para fazer pedidos.");
      return;
    }

    if (cartItems.length === 0) {
      setError("Adicione pelo menos um item ao carrinho.");
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      await apiFetch("/pedidos", {
        method: "POST",
        body: JSON.stringify({
          cliente_id: user.clienteId,
          itens: cartItems.map((item) => ({
            item_id: item.menuItem.id,
            quantidade: item.quantidade,
          })),
        }),
      });

      setPedidoEnviado(true);
      setCart(new Map());
      const [refreshedCardapio, pedidosCliente] = await Promise.all([
        apiFetch<EstoqueItem[]>("/estoque"),
        apiFetch<Pedido[]>("/pedidos", {
          query: { cliente_nome: nomeCliente },
        }),
      ]);
      setCardapio(refreshedCardapio);
      setMeusPedidos(
        pedidosCliente.filter(
          (pedido) =>
            pedido.cliente_nome.trim().toLowerCase() === nomeCliente.toLowerCase()
        )
      );
      setTimeout(() => setPedidoEnviado(false), 3000);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="relative min-h-screen bg-[#FFF5E6]">
      <CoxinhaCascade count={35} />

      <div className="relative z-10">
        <nav className="sticky top-0 z-20 flex items-center justify-between border-b border-[#F5C451]/20 bg-[#FFF5E6]/80 backdrop-blur-xl px-6 py-4">
          <div className="flex items-center gap-3">
            <Image
              src="/logo.jpeg"
              alt="YAO Lanches"
              width={36}
              height={36}
              className="rounded-lg"
            />
            <div>
              <span className="text-lg font-bold text-[#1B2A4A]">YAO Lanches</span>
              {user && (
                <p className="text-xs text-[#1B2A4A]/40">Olá, {user.nome}</p>
              )}
            </div>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-2 rounded-xl border border-[#F5C451]/20 bg-white/60 px-4 py-2 text-sm text-[#1B2A4A]/60 transition-all hover:bg-white hover:text-[#1B2A4A]"
          >
            <LogOut className="h-4 w-4" />
            Sair
          </button>
        </nav>

        <div className="mx-auto max-w-5xl px-6 py-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-[#1B2A4A]">
              Cardápio
            </h1>
            <p className="mt-2 text-[#1B2A4A]/50">
              Escolha seus lanches favoritos e monte seu pedido
            </p>
          </div>

          {pedidoEnviado && (
            <div className="mb-6 flex items-center gap-3 rounded-xl border border-green-200 bg-green-50 px-5 py-4 text-green-700">
              <Check className="h-5 w-5 shrink-0" />
              <span className="text-sm font-medium">
                Pedido enviado com sucesso! Em breve ficará pronto.
              </span>
            </div>
          )}

          {error && (
            <div className="mb-6 flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-red-700">
              <AlertCircle className="h-5 w-5 shrink-0" />
              <span className="text-sm font-medium">{error}</span>
            </div>
          )}

          <div className="mb-6 grid gap-4 lg:grid-cols-[1.1fr_1fr]">
            <div className="rounded-2xl border border-[#F5C451]/20 bg-white/80 p-5">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-[#1B2A4A]">
                    Meus pedidos
                  </h2>
                  <p className="mt-1 text-sm text-[#1B2A4A]/50">
                    Acompanhe aqui o status dos seus pedidos cadastrados.
                  </p>
                </div>
                {consultandoPedidos ? (
                  <Loader2 className="h-5 w-5 animate-spin text-[#F5A623]" />
                ) : (
                  <Clock3 className="h-5 w-5 text-[#F5A623]" />
                )}
              </div>

              {meusPedidos.length > 0 ? (
                <div className="mt-4 space-y-3">
                  {meusPedidos.map((pedido) => (
                    <div
                      key={pedido.id}
                      className="rounded-xl border border-[#F5C451]/15 bg-[#FFF5E6]/50 px-4 py-3"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="text-sm font-semibold text-[#1B2A4A]">
                            Pedido #{pedido.id}
                          </p>
                          <p className="text-xs text-[#1B2A4A]/45">
                            {pedido.itens.length} item(ns) • {formatCurrency(pedido.valor)}
                          </p>
                        </div>
                        <span
                          className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${
                            pedido.estado === "PRONTO"
                              ? "bg-green-50 text-green-700"
                              : pedido.estado === "ENTREGUE"
                                ? "bg-blue-50 text-blue-700"
                                : pedido.estado === "CANCELADO"
                                  ? "bg-red-50 text-red-700"
                                  : "bg-amber-50 text-amber-700"
                          }`}
                        >
                          {pedido.estado.replace("_", " ")}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="mt-4 rounded-xl border border-dashed border-[#F5C451]/20 bg-[#FFF5E6]/30 px-4 py-6 text-center text-sm text-[#1B2A4A]/45">
                  Nenhum pedido encontrado para seu cadastro ainda.
                </div>
              )}
            </div>

            <div className="rounded-2xl border border-green-200 bg-green-50/80 p-5">
              <div className="flex items-center gap-3">
                <div className="rounded-xl bg-white p-2 text-green-700">
                  <BellRing className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-[#1B2A4A]">
                    Pedidos prontos para retirada
                  </h2>
                  <p className="text-sm text-[#1B2A4A]/55">
                    Assim que um pedido ficar pronto, ele aparece aqui para o cliente.
                  </p>
                </div>
              </div>

              {pedidosProntos.length > 0 ? (
                <div className="mt-4 space-y-3">
                  {pedidosProntos.map((pedido) => (
                    <div
                      key={pedido.id}
                      className="rounded-xl border border-green-200 bg-white px-4 py-3"
                    >
                      <p className="text-sm font-semibold text-[#1B2A4A]">
                        Pedido #{pedido.id} pronto
                      </p>
                      <p className="mt-1 text-sm text-[#1B2A4A]/55">
                        Valor: {formatCurrency(pedido.valor)}
                      </p>
                      <p className="text-sm text-green-700">
                        Pode retirar seu pedido agora.
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="mt-4 rounded-xl border border-dashed border-green-200 bg-white/80 px-4 py-6 text-center text-sm text-[#1B2A4A]/45">
                  Ainda não há pedidos prontos para este cliente.
                </div>
              )}
            </div>
          </div>

          {loading ? (
            <div className="rounded-2xl border border-[#F5C451]/20 bg-white/80 p-12 text-center">
              <Loader2 className="mx-auto h-10 w-10 animate-spin text-[#F5A623]" />
              <p className="mt-3 text-sm text-[#1B2A4A]/40">
                Carregando cardápio...
              </p>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {cardapio.map((item) => {
                const qty = getQuantity(item.id);
                return (
                  <div
                    key={item.id}
                    className={`rounded-2xl border p-5 transition-all duration-200 ${
                      qty > 0
                        ? "border-[#F5A623]/40 bg-[#F5A623]/5 shadow-md"
                        : "border-[#F5C451]/20 bg-white/80 hover:border-[#F5A623]/30 hover:shadow-sm"
                    }`}
                  >
                    <div className="mb-3 flex items-start justify-between">
                      <div>
                        <h3 className="font-semibold text-[#1B2A4A]">{item.item}</h3>
                        <p className="mt-0.5 text-xs text-[#1B2A4A]/40">
                          {item.quantidade_disponivel} disponíveis
                        </p>
                      </div>
                      <span className="text-lg font-bold text-[#F5A623]">
                        {formatCurrency(item.valor)}
                      </span>
                    </div>

                    <div className="flex items-center justify-end gap-2">
                      {qty > 0 && (
                        <>
                          <button
                            onClick={() => removeFromCart(item.id)}
                            className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#1B2A4A]/10 text-[#1B2A4A]/60 transition-colors hover:bg-[#1B2A4A]/20 hover:text-[#1B2A4A]"
                          >
                            <Minus className="h-4 w-4" />
                          </button>
                          <span className="w-8 text-center text-sm font-bold text-[#1B2A4A]">
                            {qty}
                          </span>
                        </>
                      )}
                      <button
                        onClick={() => addToCart(item)}
                        disabled={qty >= item.quantidade_disponivel}
                        className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#F5A623]/20 text-[#F5A623] transition-colors hover:bg-[#F5A623]/30 disabled:opacity-30 disabled:cursor-not-allowed"
                      >
                        <Plus className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {cartItems.length > 0 && (
            <div className="fixed bottom-0 left-0 right-0 z-30 border-t border-[#F5C451]/20 bg-white/90 backdrop-blur-xl px-6 py-4 shadow-lg">
              <div className="mx-auto flex max-w-5xl items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#FFF5E6]">
                    <ShoppingCart className="h-5 w-5 text-[#F5A623]" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-[#1B2A4A]">
                      {cartItems.reduce((sum, ci) => sum + ci.quantidade, 0)}{" "}
                      {cartItems.reduce((sum, ci) => sum + ci.quantidade, 0) === 1
                        ? "item"
                        : "itens"}
                    </p>
                    <p className="text-lg font-bold text-[#F5A623]">
                      {formatCurrency(total)}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => void handleEnviarPedido()}
                  disabled={submitting}
                  className="inline-flex items-center gap-2 rounded-xl bg-[#F5A623] px-6 py-3 text-sm font-bold text-[#1B2A4A] shadow-md shadow-[#F5A623]/20 transition-all hover:bg-[#F5C451] hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {submitting ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                  {submitting ? "Enviando..." : "Enviar Pedido"}
                </button>
              </div>
            </div>
          )}

          {cartItems.length === 0 && !pedidoEnviado && (
            <div className="mt-12 text-center">
              <PackageX className="mx-auto h-12 w-12 text-[#1B2A4A]/15" />
              <p className="mt-3 text-sm text-[#1B2A4A]/40">
                Seu carrinho está vazio. Adicione itens do cardápio acima.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
