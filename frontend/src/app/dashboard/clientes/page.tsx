"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Plus,
  Search,
  Edit2,
  Trash2,
  Eye,
  UserX,
  Loader2,
  X,
  AlertCircle,
} from "lucide-react";
import { apiFetch } from "@/lib/api";
import { getErrorMessage } from "@/lib/format";
import type { Cliente } from "@/lib/types";

export default function ClientesPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Cliente | null>(null);
  const [editing, setEditing] = useState<Cliente | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    nome: "",
    numero: "",
    torce_flamengo: false,
    assiste_one_piece: false,
    eh_de_sousa: false,
  });

  async function loadClientes(term = searchTerm) {
    try {
      setLoading(true);
      setError(null);
      const data = await apiFetch<Cliente[]>("/clientes", {
        query: { nome: term || undefined },
      });
      setClientes(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadClientes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchTerm]);

  const filtered = useMemo(() => clientes, [clientes]);

  function openCreate() {
    setEditing(null);
    setForm({
      nome: "",
      numero: "",
      torce_flamengo: false,
      assiste_one_piece: false,
      eh_de_sousa: false,
    });
    setShowForm(true);
  }

  function openEdit(cliente: Cliente) {
    setEditing(cliente);
    setForm({
      nome: cliente.nome,
      numero: cliente.numero,
      torce_flamengo: cliente.torce_flamengo,
      assiste_one_piece: cliente.assiste_one_piece,
      eh_de_sousa: cliente.eh_de_sousa,
    });
    setShowForm(true);
  }

  function closeForm() {
    setShowForm(false);
    setEditing(null);
    setForm({
      nome: "",
      numero: "",
      torce_flamengo: false,
      assiste_one_piece: false,
      eh_de_sousa: false,
    });
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      setSubmitting(true);
      setError(null);

      if (editing) {
        await apiFetch<Cliente>(`/clientes/${editing.id}`, {
          method: "PUT",
          body: JSON.stringify(form),
        });
      } else {
        await apiFetch<Cliente>("/clientes", {
          method: "POST",
          body: JSON.stringify(form),
        });
      }

      closeForm();
      await loadClientes();
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(cliente: Cliente) {
    const confirmed = window.confirm(
      `Deseja remover o cliente "${cliente.nome}"?`
    );
    if (!confirmed) {
      return;
    }

    try {
      setError(null);
      await apiFetch<void>(`/clientes/${cliente.id}`, { method: "DELETE" });
      if (selected?.id === cliente.id) {
        setSelected(null);
      }
      await loadClientes();
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  return (
    <div>
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#1B2A4A] sm:text-3xl tracking-[-0.02em]">
            Clientes
          </h1>
          <p className="mt-1 text-[#1B2A4A]/50">
            Gerencie os clientes cadastrados
          </p>
        </div>
        <button
          onClick={openCreate}
          className="inline-flex items-center gap-2 rounded-xl bg-[#F5A623] px-5 py-3 text-sm font-bold text-[#1B2A4A] transition-all duration-200 hover:bg-[#F5C451] hover:shadow-lg hover:shadow-[#F5A623]/20"
        >
          <Plus className="h-4 w-4" />
          Novo Cliente
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="mb-6 rounded-2xl border border-[#F5C451]/20 bg-white/90 p-6"
        >
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-[#1B2A4A]">
                {editing ? "Editar cliente" : "Novo cliente"}
              </h2>
              <p className="text-sm text-[#1B2A4A]/50">
                Preencha os dados para salvar no backend.
              </p>
            </div>
            <button
              type="button"
              onClick={closeForm}
              className="rounded-lg p-2 text-[#1B2A4A]/40 transition-colors hover:bg-[#FFF5E6] hover:text-[#1B2A4A]"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <input
              value={form.nome}
              onChange={(e) => setForm((prev) => ({ ...prev, nome: e.target.value }))}
              placeholder="Nome do cliente"
              required
              className="rounded-xl border border-[#F5C451]/20 bg-white px-4 py-3 text-sm text-[#1B2A4A] outline-none transition-all focus:border-[#F5A623]/30 focus:ring-2 focus:ring-[#F5A623]/10"
            />
            <input
              value={form.numero}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, numero: e.target.value }))
              }
              placeholder="Telefone / número"
              required
              className="rounded-xl border border-[#F5C451]/20 bg-white px-4 py-3 text-sm text-[#1B2A4A] outline-none transition-all focus:border-[#F5A623]/30 focus:ring-2 focus:ring-[#F5A623]/10"
            />
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <label className="flex cursor-pointer items-center gap-3 rounded-xl border border-[#F5C451]/20 px-4 py-3 transition-colors hover:bg-[#FFF5E6]/30">
              <input
                type="checkbox"
                checked={form.torce_flamengo}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, torce_flamengo: e.target.checked }))
                }
                className="h-4 w-4 rounded accent-[#E85B5B]"
              />
              <span className="text-sm text-[#1B2A4A]">Torce pro Flamengo</span>
            </label>
            <label className="flex cursor-pointer items-center gap-3 rounded-xl border border-[#F5C451]/20 px-4 py-3 transition-colors hover:bg-[#FFF5E6]/30">
              <input
                type="checkbox"
                checked={form.assiste_one_piece}
                onChange={(e) =>
                  setForm((prev) => ({
                    ...prev,
                    assiste_one_piece: e.target.checked,
                  }))
                }
                className="h-4 w-4 rounded accent-[#F5A623]"
              />
              <span className="text-sm text-[#1B2A4A]">Assiste One Piece</span>
            </label>
            <label className="flex cursor-pointer items-center gap-3 rounded-xl border border-[#F5C451]/20 px-4 py-3 transition-colors hover:bg-[#FFF5E6]/30">
              <input
                type="checkbox"
                checked={form.eh_de_sousa}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, eh_de_sousa: e.target.checked }))
                }
                className="h-4 w-4 rounded accent-[#3BB5E8]"
              />
              <span className="text-sm text-[#1B2A4A]">De Sousa</span>
            </label>
          </div>

          <div className="mt-4 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={closeForm}
              className="rounded-xl border border-[#F5C451]/20 px-4 py-2.5 text-sm font-medium text-[#1B2A4A]/70 transition-colors hover:bg-[#FFF5E6]"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-2 rounded-xl bg-[#F5A623] px-4 py-2.5 text-sm font-bold text-[#1B2A4A] transition-all hover:bg-[#F5C451] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {editing ? "Salvar alterações" : "Cadastrar cliente"}
            </button>
          </div>
        </form>
      )}

      {error && (
        <div className="mb-6 flex items-center gap-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      <div className="mb-6 flex items-center gap-3 rounded-xl border border-[#F5C451]/20 bg-white/80 px-4 py-3 focus-within:border-[#F5A623]/30 focus-within:ring-2 focus-within:ring-[#F5A623]/10 transition-all">
        <Search className="h-5 w-5 text-[#1B2A4A]/30" />
        <input
          type="text"
          placeholder="Pesquisar por nome..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1 bg-transparent text-sm text-[#1B2A4A] placeholder:text-[#1B2A4A]/30 outline-none"
        />
      </div>

      {selected && (
        <div className="mb-6 rounded-2xl border border-[#3BB5E8]/20 bg-[#3BB5E8]/5 p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-[#3BB5E8]">
                Cliente selecionado
              </p>
              <h2 className="mt-1 text-lg font-semibold text-[#1B2A4A]">
                {selected.nome}
              </h2>
              <p className="mt-1 text-sm text-[#1B2A4A]/60">
                Número: {selected.numero}
              </p>
              <div className="mt-2 flex flex-wrap gap-1">
                {selected.torce_flamengo && (
                  <span className="rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-600">
                    Flamengo
                  </span>
                )}
                {selected.assiste_one_piece && (
                  <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-600">
                    One Piece
                  </span>
                )}
                {selected.eh_de_sousa && (
                  <span className="rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-600">
                    Sousa
                  </span>
                )}
              </div>
              <p className="text-sm text-[#1B2A4A]/40">ID #{selected.id}</p>
            </div>
            <button
              onClick={() => setSelected(null)}
              className="rounded-lg p-2 text-[#1B2A4A]/40 transition-colors hover:bg-white/70 hover:text-[#1B2A4A]"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {loading ? (
        <div className="rounded-2xl border border-[#F5C451]/20 bg-white/80 p-12 text-center">
          <Loader2 className="mx-auto h-10 w-10 animate-spin text-[#F5A623]" />
          <p className="mt-3 text-sm text-[#1B2A4A]/40">Carregando clientes...</p>
        </div>
      ) : filtered.length > 0 ? (
        <div className="overflow-hidden rounded-2xl border border-[#F5C451]/20 bg-white/80">
          <table className="w-full">
            <thead>
              <tr className="border-b border-[#F5C451]/10">
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                  ID
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                  Nome
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                  Número
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                  Descontos
                </th>
                <th className="px-6 py-4 text-right text-xs font-semibold uppercase tracking-wider text-[#1B2A4A]/40">
                  Ações
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#F5C451]/10">
              {filtered.map((cliente) => (
                <tr
                  key={cliente.id}
                  className="transition-colors hover:bg-[#FFF5E6]/30"
                >
                  <td className="px-6 py-4 text-sm font-mono text-[#1B2A4A]/40">
                    #{cliente.id}
                  </td>
                  <td className="px-6 py-4 text-sm font-medium text-[#1B2A4A]">
                    {cliente.nome}
                  </td>
                  <td className="px-6 py-4 text-sm text-[#1B2A4A]/60">
                    {cliente.numero}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {cliente.torce_flamengo && (
                        <span className="rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-600">
                          Flamengo
                        </span>
                      )}
                      {cliente.assiste_one_piece && (
                        <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-600">
                          One Piece
                        </span>
                      )}
                      {cliente.eh_de_sousa && (
                        <span className="rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-600">
                          Sousa
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setSelected(cliente)}
                        className="rounded-lg p-2 text-[#3BB5E8]/60 hover:bg-[#3BB5E8]/10 hover:text-[#3BB5E8] transition-colors"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => openEdit(cliente)}
                        className="rounded-lg p-2 text-[#F5A623]/60 hover:bg-[#F5A623]/10 hover:text-[#F5A623] transition-colors"
                      >
                        <Edit2 className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => void handleDelete(cliente)}
                        className="rounded-lg p-2 text-[#E85B5B]/60 hover:bg-[#E85B5B]/10 hover:text-[#E85B5B] transition-colors"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="rounded-2xl border border-[#F5C451]/20 bg-white/80 p-12 text-center">
          <UserX className="mx-auto h-16 w-16 text-[#1B2A4A]/20" />
          <h2 className="mt-4 text-lg font-semibold text-[#1B2A4A]">
            {searchTerm
              ? "Nenhum cliente encontrado"
              : "Nenhum cliente cadastrado"}
          </h2>
          <p className="mt-2 text-sm text-[#1B2A4A]/40">
            {searchTerm
              ? `Nenhum resultado para "${searchTerm}"`
              : "Comece cadastrando o primeiro cliente."}
          </p>
        </div>
      )}
    </div>
  );
}
