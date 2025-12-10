import { useState, useEffect } from 'react';
import { 
  CheckCircle2, 
  Circle, 
  Calendar, 
  User, 
  AlertCircle,
  ExternalLink,
  Edit2,
  Save,
  X,
  Send,
  Loader2
} from 'lucide-react';
import { clsx } from 'clsx';
import { 
  getJiraConfig, 
  getJiraUsers, 
  getUserMappings,
  updateTask,
  createJiraIssues
} from '../api';
import type { TaskItem, JiraUser, JiraConfigStatus, JiraTaskDraft } from '../types';

interface TasksPanelProps {
  jobId: string;
  tasks: TaskItem[];
  onTasksUpdate: (tasks: TaskItem[]) => void;
}

const priorityColors = {
  Low: 'bg-gray-100 text-gray-700',
  Medium: 'bg-blue-100 text-blue-700',
  High: 'bg-orange-100 text-orange-700',
  Critical: 'bg-red-100 text-red-700',
};

export default function TasksPanel({ jobId, tasks, onTasksUpdate }: TasksPanelProps) {
  const [jiraConfig, setJiraConfig] = useState<JiraConfigStatus | null>(null);
  const [jiraUsers, setJiraUsers] = useState<JiraUser[]>([]);
  const [userMappings, setUserMappings] = useState<Record<string, string>>({});
  const [editingTask, setEditingTask] = useState<string | null>(null);
  const [editedTask, setEditedTask] = useState<TaskItem | null>(null);
  const [selectedTasks, setSelectedTasks] = useState<Set<string>>(new Set());
  const [isCreatingJira, setIsCreatingJira] = useState(false);
  const [jiraResults, setJiraResults] = useState<{ created: string[]; errors: string[] } | null>(null);

  useEffect(() => {
    async function loadJiraData() {
      try {
        const [config, users, mappings] = await Promise.all([
          getJiraConfig(),
          getJiraConfig().then(c => c.configured ? getJiraUsers() : []),
          getUserMappings(),
        ]);
        setJiraConfig(config);
        setJiraUsers(users);
        setUserMappings(mappings);
      } catch (error) {
        console.error('Failed to load Jira data:', error);
      }
    }
    loadJiraData();
  }, []);

  const handleEditTask = (task: TaskItem) => {
    setEditingTask(task.id);
    setEditedTask({ ...task });
  };

  const handleSaveTask = async () => {
    if (!editedTask) return;

    try {
      const updated = await updateTask(jobId, editedTask.id, editedTask);
      const newTasks = tasks.map(t => t.id === updated.id ? updated : t);
      onTasksUpdate(newTasks);
      setEditingTask(null);
      setEditedTask(null);
    } catch (error) {
      console.error('Failed to update task:', error);
    }
  };

  const handleCancelEdit = () => {
    setEditingTask(null);
    setEditedTask(null);
  };

  const toggleTaskSelection = (taskId: string) => {
    const newSelected = new Set(selectedTasks);
    if (newSelected.has(taskId)) {
      newSelected.delete(taskId);
    } else {
      newSelected.add(taskId);
    }
    setSelectedTasks(newSelected);
  };

  const selectAllTasks = () => {
    if (selectedTasks.size === tasks.filter(t => !t.jira_created).length) {
      setSelectedTasks(new Set());
    } else {
      setSelectedTasks(new Set(tasks.filter(t => !t.jira_created).map(t => t.id)));
    }
  };

  const getJiraAssigneeId = (task: TaskItem): string | undefined => {
    if (task.jira_assignee_id) return task.jira_assignee_id;
    if (task.assignee && userMappings[task.assignee]) {
      return userMappings[task.assignee];
    }
    return undefined;
  };

  const handleCreateJiraIssues = async () => {
    if (selectedTasks.size === 0 || !jiraConfig?.configured) return;

    setIsCreatingJira(true);
    setJiraResults(null);

    const taskDrafts: JiraTaskDraft[] = tasks
      .filter(t => selectedTasks.has(t.id))
      .map(task => ({
        task_id: task.id,
        summary: task.description.slice(0, 100),
        description: task.description,
        assignee_id: getJiraAssigneeId(task),
        due_date: task.due_date,
        priority: task.priority || 'Medium',
        issue_type: 'Task',
        labels: ['meeting-assistant'],
      }));

    try {
      const result = await createJiraIssues({ job_id: jobId, tasks: taskDrafts });
      
      // Update tasks with Jira info
      const newTasks = tasks.map(t => {
        const created = result.created.find(c => c.task_id === t.id);
        if (created) {
          return { ...t, jira_created: true, jira_key: created.jira_key };
        }
        return t;
      });
      onTasksUpdate(newTasks);
      
      setJiraResults({
        created: result.created.map(c => c.jira_key),
        errors: result.errors.map(e => e.error),
      });
      setSelectedTasks(new Set());
    } catch (error) {
      console.error('Failed to create Jira issues:', error);
      setJiraResults({ created: [], errors: ['Failed to create issues'] });
    } finally {
      setIsCreatingJira(false);
    }
  };

  if (tasks.length === 0) {
    return (
      <div className="text-center py-8 md:py-12">
        <div className="w-12 h-12 md:w-16 md:h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle2 className="w-6 h-6 md:w-8 md:h-8 text-gray-400" />
        </div>
        <h3 className="text-base md:text-lg font-medium text-gray-900 mb-2">No Action Items</h3>
        <p className="text-sm md:text-base text-gray-500">No tasks were extracted from this meeting.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 md:space-y-6">
      {/* Jira Integration Banner */}
      {!jiraConfig?.configured && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 md:p-4 flex flex-col sm:flex-row items-start sm:items-center gap-2 md:gap-3">
          <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0" />
          <div className="flex-1">
            <p className="text-xs md:text-sm text-amber-800">
              Connect Jira to create tasks directly from extracted action items.
            </p>
          </div>
          <a
            href="/settings"
            className="text-xs md:text-sm font-medium text-amber-700 hover:text-amber-800"
          >
            Configure →
          </a>
        </div>
      )}

      {/* Bulk Actions */}
      {jiraConfig?.configured && (
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-gray-50 rounded-xl p-3 md:p-4">
          <div className="flex items-center gap-3">
            <button
              onClick={selectAllTasks}
              className="text-xs md:text-sm text-sky-600 hover:text-sky-700 font-medium"
            >
              {selectedTasks.size === tasks.filter(t => !t.jira_created).length
                ? 'Deselect All'
                : 'Select All'}
            </button>
            {selectedTasks.size > 0 && (
              <span className="text-xs md:text-sm text-gray-500">
                {selectedTasks.size} selected
              </span>
            )}
          </div>
          
          <button
            onClick={handleCreateJiraIssues}
            disabled={selectedTasks.size === 0 || isCreatingJira}
            className={clsx(
              'inline-flex items-center gap-2 px-3 md:px-4 py-2 rounded-lg text-xs md:text-sm font-medium transition-colors w-full sm:w-auto justify-center',
              selectedTasks.size > 0 && !isCreatingJira
                ? 'bg-sky-600 text-white hover:bg-sky-700'
                : 'bg-gray-200 text-gray-400 cursor-not-allowed'
            )}
          >
            {isCreatingJira ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Create in Jira
              </>
            )}
          </button>
        </div>
      )}

      {/* Jira Results */}
      {jiraResults && (
        <div className={clsx(
          'rounded-xl p-4',
          jiraResults.errors.length > 0 ? 'bg-red-50 border border-red-200' : 'bg-emerald-50 border border-emerald-200'
        )}>
          {jiraResults.created.length > 0 && (
            <p className="text-sm text-emerald-700 mb-2">
              ✅ Created: {jiraResults.created.join(', ')}
            </p>
          )}
          {jiraResults.errors.length > 0 && (
            <p className="text-sm text-red-700">
              ❌ Errors: {jiraResults.errors.join(', ')}
            </p>
          )}
        </div>
      )}

      {/* Tasks List */}
      <div className="space-y-4">
        {tasks.map((task) => (
          <div
            key={task.id}
            className={clsx(
              'border rounded-xl overflow-hidden transition-all',
              task.jira_created
                ? 'border-emerald-200 bg-emerald-50/50'
                : selectedTasks.has(task.id)
                ? 'border-sky-300 bg-sky-50/50'
                : 'border-gray-200 hover:border-gray-300'
            )}
          >
            {editingTask === task.id && editedTask ? (
              /* Edit Mode */
              <div className="p-3 md:p-4 space-y-3 md:space-y-4">
                <div>
                  <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={editedTask.description}
                    onChange={(e) => setEditedTask({ ...editedTask, description: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-transparent text-sm"
                    rows={3}
                  />
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-4">
                  <div>
                    <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">
                      Assignee
                    </label>
                    <input
                      type="text"
                      value={editedTask.assignee || ''}
                      onChange={(e) => setEditedTask({ ...editedTask, assignee: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-transparent text-sm"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">
                      Due Date
                    </label>
                    <input
                      type="date"
                      value={editedTask.due_date || ''}
                      onChange={(e) => setEditedTask({ ...editedTask, due_date: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-transparent text-sm"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 md:gap-4">
                  <div>
                    <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">
                      Priority
                    </label>
                    <select
                      value={editedTask.priority || 'Medium'}
                      onChange={(e) => setEditedTask({ ...editedTask, priority: e.target.value as TaskItem['priority'] })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-transparent text-sm"
                    >
                      <option value="Low">Low</option>
                      <option value="Medium">Medium</option>
                      <option value="High">High</option>
                      <option value="Critical">Critical</option>
                    </select>
                  </div>

                  {jiraConfig?.configured && (
                    <div>
                      <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">
                        Jira Assignee
                      </label>
                      <select
                        value={editedTask.jira_assignee_id || ''}
                        onChange={(e) => setEditedTask({ ...editedTask, jira_assignee_id: e.target.value || undefined })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-transparent text-sm"
                      >
                        <option value="">Unassigned</option>
                        {jiraUsers.map(user => (
                          <option key={user.account_id} value={user.account_id}>
                            {user.display_name}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>

                <div className="flex justify-end gap-2">
                  <button
                    onClick={handleCancelEdit}
                    className="inline-flex items-center gap-2 px-3 py-2 text-xs md:text-sm text-gray-600 hover:text-gray-800"
                  >
                    <X className="w-4 h-4" />
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveTask}
                    className="inline-flex items-center gap-2 px-3 md:px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 text-xs md:text-sm"
                  >
                    <Save className="w-4 h-4" />
                    Save
                  </button>
                </div>
              </div>
            ) : (
              /* View Mode */
              <div className="p-3 md:p-4">
                <div className="flex items-start gap-2 md:gap-3">
                  {/* Selection Checkbox */}
                  {jiraConfig?.configured && !task.jira_created && (
                    <button
                      onClick={() => toggleTaskSelection(task.id)}
                      className="mt-0.5 flex-shrink-0"
                    >
                      {selectedTasks.has(task.id) ? (
                        <CheckCircle2 className="w-5 h-5 text-sky-600" />
                      ) : (
                        <Circle className="w-5 h-5 text-gray-300 hover:text-sky-400" />
                      )}
                    </button>
                  )}

                  {/* Task Content */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm md:text-base text-gray-900 mb-2">{task.description}</p>
                    
                    <div className="flex flex-wrap items-center gap-1.5 md:gap-2 text-xs md:text-sm">
                      {task.assignee && (
                        <span className="inline-flex items-center gap-1 px-1.5 md:px-2 py-0.5 md:py-1 bg-gray-100 text-gray-700 rounded">
                          <User className="w-3 h-3" />
                          <span className="truncate max-w-[80px] md:max-w-none">{task.assignee}</span>
                        </span>
                      )}
                      
                      {task.due_date && (
                        <span className="inline-flex items-center gap-1 px-1.5 md:px-2 py-0.5 md:py-1 bg-gray-100 text-gray-700 rounded">
                          <Calendar className="w-3 h-3" />
                          {task.due_date}
                        </span>
                      )}
                      
                      {task.priority && (
                        <span className={clsx(
                          'px-1.5 md:px-2 py-0.5 md:py-1 rounded text-xs font-medium',
                          priorityColors[task.priority]
                        )}>
                          {task.priority}
                        </span>
                      )}

                      {task.jira_created && task.jira_key && (
                        <a
                          href={`https://${jiraConfig?.domain}/browse/${task.jira_key}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 px-1.5 md:px-2 py-0.5 md:py-1 bg-emerald-100 text-emerald-700 rounded hover:bg-emerald-200"
                        >
                          <ExternalLink className="w-3 h-3" />
                          {task.jira_key}
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Edit Button */}
                  {!task.jira_created && (
                    <button
                      onClick={() => handleEditTask(task)}
                      className="p-1.5 md:p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg flex-shrink-0"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
