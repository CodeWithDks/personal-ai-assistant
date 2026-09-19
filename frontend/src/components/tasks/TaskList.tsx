import { useTasks } from '../../hooks/useTasks';
import { BulkActions } from './BulkActions';
import { TaskCard } from './TaskCard';
import { TaskFilters } from './TaskFilters';
import { TaskForm } from './TaskForm';
import { EmptyState } from '../shared/EmptyState';
import { Pagination } from '../shared/Pagination';
import { Spinner } from '../shared/Spinner';

export function TaskList() {
  const t = useTasks();
  const pendingCount = t.allFilteredTasks.filter((x) => x.status !== 'completed').length;
  const completedCount = t.allFilteredTasks.filter((x) => x.status === 'completed').length;
  const isFiltering = !!t.keyword || t.statusFilter !== 'all' || t.priorityFilter !== 'all';

  return (
    <div>
      <TaskForm onCreate={t.addTask} />
      <TaskFilters
        keyword={t.keyword}
        onKeyword={t.setKeyword}
        status={t.statusFilter}
        onStatus={t.setStatusFilter}
        priority={t.priorityFilter}
        onPriority={t.setPriorityFilter}
        sortBy={t.sortBy}
        onSortBy={t.setSortBy}
        onRefresh={t.refetch}
      />

      {t.error && <p className="mb-3 rounded-md bg-danger-soft px-3 py-2 text-sm text-danger">{t.error}</p>}

      {t.loading ? (
        <Spinner />
      ) : t.allFilteredTasks.length === 0 ? (
        <EmptyState
          icon="📭"
          title="No tasks found"
          subtitle={isFiltering ? 'Try clearing your filters.' : "You're all caught up!"}
        />
      ) : (
        <>
          <BulkActions
            pendingCount={pendingCount}
            completedCount={completedCount}
            onMarkAllDone={t.markAllDone}
            onDeleteCompleted={t.deleteCompleted}
          />
          <div className="flex flex-col gap-2">
            {t.tasks.map((task) => (
              <TaskCard
                key={task.id}
                task={task}
                onToggleDone={() => t.editTask(task.id, { status: 'completed' })}
                onEdit={(fields) => t.editTask(task.id, fields)}
                onDelete={() => t.removeTask(task.id)}
              />
            ))}
          </div>
          <Pagination page={t.page} totalPages={t.totalPages} onChange={t.setPage} />
        </>
      )}
    </div>
  );
}
