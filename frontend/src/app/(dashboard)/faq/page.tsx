"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { Categoria, FaqItem } from "@/types/api";

interface FormState {
  id: number | null;
  categoria_id: number | "";
  pergunta: string;
  resposta: string;
  ativo: boolean;
}

const EMPTY_FORM: FormState = { id: null, categoria_id: "", pergunta: "", resposta: "", ativo: true };

export default function FaqAdminPage() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [showForm, setShowForm] = useState(false);
  const categoriaSelectRef = useRef<HTMLSelectElement>(null);

  useEffect(() => {
    if (showForm) categoriaSelectRef.current?.focus();
  }, [showForm]);

  const faqItems = useQuery({
    queryKey: ["faq-items"],
    queryFn: () => api.get<FaqItem[]>("/api/faq"),
  });

  const categorias = useQuery({
    queryKey: ["categorias"],
    queryFn: () => api.get<Categoria[]>("/api/faq/categorias"),
  });

  const saveMutation = useMutation({
    mutationFn: (data: FormState) => {
      const body = {
        categoria_id: Number(data.categoria_id),
        pergunta: data.pergunta,
        resposta: data.resposta,
        ativo: data.ativo,
      };
      return data.id
        ? api.put<FaqItem>(`/api/faq/${data.id}`, body)
        : api.post<FaqItem>("/api/faq", body);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["faq-items"] });
      setForm(EMPTY_FORM);
      setShowForm(false);
      toast.success("Pergunta salva com sucesso.");
    },
    onError: () => toast.error("Erro ao salvar pergunta."),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/api/faq/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["faq-items"] });
      toast.success("Pergunta excluída.");
    },
    onError: () => toast.error("Erro ao excluir pergunta."),
  });

  function handleEdit(item: FaqItem) {
    setForm({
      id: item.id,
      categoria_id: item.categoria_id,
      pergunta: item.pergunta,
      resposta: item.resposta,
      ativo: item.ativo,
    });
    setShowForm(true);
  }

  function handleDelete(id: number) {
    if (window.confirm("Excluir esta pergunta?")) {
      deleteMutation.mutate(id);
    }
  }

  return (
    <div>
      <div className="page-header-row">
        <h1>Base de Conhecimento</h1>
        <button
          onClick={() => {
            setForm(EMPTY_FORM);
            setShowForm(!showForm);
          }}
        >
          {showForm ? "Cancelar" : "Nova pergunta"}
        </button>
      </div>

      {showForm && (
        <form
          className="faq-form"
          onSubmit={(e) => {
            e.preventDefault();
            saveMutation.mutate(form);
          }}
        >
          <label htmlFor="faq-categoria">
            Categoria
            <select
              id="faq-categoria"
              ref={categoriaSelectRef}
              value={form.categoria_id}
              onChange={(e) => setForm({ ...form, categoria_id: Number(e.target.value) })}
              required
            >
              <option value="">Selecione...</option>
              {(categorias.data ?? []).map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nome}
                </option>
              ))}
            </select>
          </label>
          <label htmlFor="faq-pergunta">
            Pergunta
            <textarea
              id="faq-pergunta"
              value={form.pergunta}
              onChange={(e) => setForm({ ...form, pergunta: e.target.value })}
              required
            />
          </label>
          <label htmlFor="faq-resposta">
            Resposta
            <textarea
              id="faq-resposta"
              value={form.resposta}
              onChange={(e) => setForm({ ...form, resposta: e.target.value })}
              required
            />
          </label>
          <label htmlFor="faq-ativo" className="faq-form-checkbox">
            <input
              id="faq-ativo"
              type="checkbox"
              checked={form.ativo}
              onChange={(e) => setForm({ ...form, ativo: e.target.checked })}
            />
            Ativo (visível no chat)
          </label>
          <button type="submit" disabled={saveMutation.isPending}>
            Salvar
          </button>
        </form>
      )}

      <div className="table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              <th>Pergunta</th>
              <th>Resposta</th>
              <th>Categoria</th>
              <th>Ativo</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            {(faqItems.data ?? []).map((item) => (
              <tr key={item.id}>
                <td>{item.pergunta}</td>
                <td>{item.resposta.slice(0, 60)}{item.resposta.length > 60 ? "..." : ""}</td>
                <td>{item.categoria_nome}</td>
                <td>{item.ativo ? "Sim" : "Não"}</td>
                <td className="actions-cell">
                  <button onClick={() => handleEdit(item)}>Editar</button>
                  <button onClick={() => handleDelete(item.id)}>Excluir</button>
                </td>
              </tr>
            ))}
            {faqItems.data?.length === 0 && (
              <tr>
                <td colSpan={5}>Nenhuma pergunta cadastrada.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
