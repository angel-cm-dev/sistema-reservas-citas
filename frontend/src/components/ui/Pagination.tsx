import { ChevronLeft, ChevronRight } from "lucide-react";

interface Props {
  page: number;
  pages: number;
  total: number;
  onChange: (page: number) => void;
}

export function Pagination({ page, pages, total, onChange }: Props) {
  if (total === 0) return null;
  return (
    <nav aria-label="Paginación" className="flex items-center justify-between gap-4 px-4 py-3 text-sm">
      <span className="text-slate-500">
        {total} {total === 1 ? "registro" : "registros"} · Página {page} de {Math.max(pages, 1)}
      </span>
      <div className="flex gap-2">
        <button className="btn-secondary px-2" disabled={page <= 1} onClick={() => onChange(page - 1)} aria-label="Página anterior">
          <ChevronLeft className="h-4 w-4" />
        </button>
        <button className="btn-secondary px-2" disabled={page >= pages} onClick={() => onChange(page + 1)} aria-label="Página siguiente">
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </nav>
  );
}
