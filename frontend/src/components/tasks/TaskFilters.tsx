import type { Priority, TaskStatus } from '../../types';
import type { SortOption } from '../../hooks/useTasks';

export function TaskFilters(props: {
  keyword: string;
  onKeyword: (v: string) => void;
  status: TaskStatus | 'all';
  onStatus: (v: TaskStatus | 'all') => void;
  priority: Priority | 'all';
  onPriority: (v: Priority | 'all') => void;
  sortBy: SortOption;
  onSortBy: (v: SortOption) => void;
  onRefresh: () => void;
}) {
  return (
    <div className="mb-3 flex flex-wrap gap-2">
      <input
        value={props.keyword}
        onChange={(e) => props.onKeyword(e.target.value)}
        placeholder="Search keyword"
        className="min-w-[140px] flex-1 rounded-lg border border-border px-3 py-1.5 text-sm"
      />
      <select
        value={props.status}
        onChange={(e) => props.onStatus(e.target.value as TaskStatus | 'all')}
        className="rounded-lg border border-border px-2 py-1.5 text-sm"
      >
        <option value="all">All statuses</option>
        <option value="pending">pending</option>
        <option value="completed">completed</option>
      </select>
      <select
        value={props.priority}
        onChange={(e) => props.onPriority(e.target.value as Priority | 'all')}
        className="rounded-lg border border-border px-2 py-1.5 text-sm"
      >
        <option value="all">All priorities</option>
        <option value="low">low</option>
        <option value="medium">medium</option>
        <option value="high">high</option>
      </select>
      <select
        value={props.sortBy}
        onChange={(e) => props.onSortBy(e.target.value as SortOption)}
        className="rounded-lg border border-border px-2 py-1.5 text-sm"
      >
        <option value="due">Sort: due date</option>
        <option value="priority">Sort: priority</option>
        <option value="newest">Sort: newest</option>
      </select>
      <button onClick={props.onRefresh} className="rounded-lg border border-border px-3 py-1.5 text-sm text-muted hover:bg-subtle-hover">
        🔄
      </button>
    </div>
  );
}
