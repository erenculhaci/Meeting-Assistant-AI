import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  FileText, 
  ListTodo, 
  Clock, 
  Users,
  MessageSquare,
  Lightbulb,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Play
} from 'lucide-react';
import { clsx } from 'clsx';
import { getResults } from '../api';
import type { MeetingResult, TaskItem } from '../types';
import TasksPanel from '../components/TasksPanel';

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  return `${mins} min`;
}

type TabType = 'summary' | 'transcript' | 'tasks';

export default function MeetingDetail() {
  const { jobId } = useParams<{ jobId: string }>();
  const [result, setResult] = useState<MeetingResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('summary');
  const [expandedTopics, setExpandedTopics] = useState<Set<number>>(new Set([0]));

  useEffect(() => {
    async function loadResult() {
      if (!jobId) return;
      try {
        const data = await getResults(jobId);
        setResult(data);
        // task extraction'a giden ve LLM diarization sonrası transcriptleri logla
        /* if (data.transcript_before_task_extraction) {
          console.log('Task extraction\'a giden transcript (speaker\'sız):', data.transcript_before_task_extraction);
        }
        if (data.transcript_after_llm_diarization) {
          console.log('LLM diarization sonrası transcript:', data.transcript_after_llm_diarization);
        }
        // Ana transcripti de logla
        if (data.transcript) {
          console.log('Frontend\'e gelen transcript:', data.transcript);
        } */
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load meeting');
      } finally {
        setLoading(false);
      }
    }
    loadResult();
  }, [jobId]);

  const toggleTopic = (index: number) => {
    const newExpanded = new Set(expandedTopics);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedTopics(newExpanded);
  };

  if (loading) {
    return (
      <div className="animate-fadeIn flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-sky-200 border-t-sky-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500">Loading meeting details...</p>
        </div>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="animate-fadeIn">
        <div className="bg-red-50 border border-red-200 rounded-2xl p-8 text-center">
          <h2 className="text-xl font-bold text-red-700 mb-2">Error Loading Meeting</h2>
          <p className="text-red-600 mb-4">{error || 'Meeting not found'}</p>
          <Link
            to="/meetings"
            className="inline-flex items-center gap-2 text-red-700 hover:text-red-800"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Meetings
          </Link>
        </div>
      </div>
    );
  }

  const summary = result.summary;

  return (
    <div className="animate-fadeIn">
      {/* Header */}
      <div className="mb-4 md:mb-6">
        <Link
          to="/meetings"
          className="inline-flex items-center gap-2 text-gray-500 hover:text-gray-700 mb-3 md:mb-4 text-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Meetings
        </Link>
        
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl md:text-2xl font-bold text-gray-900 mb-2 break-words">{result.filename}</h1>
            <div className="flex flex-wrap items-center gap-2 md:gap-4 text-xs md:text-sm text-gray-500">
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3 md:w-4 md:h-4" />
                {formatDuration(result.duration)}
              </span>
              <span className="flex items-center gap-1">
                <MessageSquare className="w-3 h-3 md:w-4 md:h-4" />
                {result.transcript.length} segments
              </span>
              <span className="flex items-center gap-1">
                <ListTodo className="w-3 h-3 md:w-4 md:h-4" />
                {result.tasks.length} tasks
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
        <div className="border-b border-gray-100 overflow-x-auto">
          <nav className="flex min-w-max">
            {[
              { id: 'summary' as const, label: 'Summary', icon: FileText },
              { id: 'transcript' as const, label: 'Transcript', icon: MessageSquare },
              { id: 'tasks' as const, label: 'Tasks', icon: ListTodo, badge: result.tasks.length },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={clsx(
                  'flex items-center gap-1.5 md:gap-2 px-3 md:px-6 py-3 md:py-4 text-xs md:text-sm font-medium border-b-2 transition-colors whitespace-nowrap',
                  activeTab === tab.id
                    ? 'border-sky-600 text-sky-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                )}
              >
                <tab.icon className="w-3.5 h-3.5 md:w-4 md:h-4" />
                {tab.label}
                {tab.badge !== undefined && (
                  <span className={clsx(
                    'px-1.5 md:px-2 py-0.5 text-xs rounded-full',
                    activeTab === tab.id
                      ? 'bg-sky-100 text-sky-700'
                      : 'bg-gray-100 text-gray-600'
                  )}>
                    {tab.badge}
                  </span>
                )}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-4 md:p-6">
          {/* Summary Tab */}
          {activeTab === 'summary' && (
            <div className="space-y-6 md:space-y-8">
              {/* Title & Overview */}
              {summary.title && (
                <div>
                  <h2 className="text-lg md:text-xl font-bold text-gray-900 mb-2 md:mb-3">{summary.title}</h2>
                  <p className="text-sm md:text-base text-gray-600 leading-relaxed">{summary.overview}</p>
                </div>
              )}

              {/* Participants */}
              {summary.participants && summary.participants.length > 0 && (
                <div>
                  <h3 className="flex items-center gap-2 text-base md:text-lg font-semibold text-gray-900 mb-2 md:mb-3">
                    <Users className="w-4 h-4 md:w-5 md:h-5 text-sky-600" />
                    Participants
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {summary.participants.map((participant, i) => (
                      <span
                        key={i}
                        className="px-2.5 md:px-3 py-1 bg-sky-50 text-sky-700 rounded-full text-xs md:text-sm font-medium"
                      >
                        {participant}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Key Points */}
              {summary.key_points && summary.key_points.length > 0 && (
                <div>
                  <h3 className="flex items-center gap-2 text-base md:text-lg font-semibold text-gray-900 mb-2 md:mb-3">
                    <Lightbulb className="w-4 h-4 md:w-5 md:h-5 text-amber-500" />
                    Key Points
                  </h3>
                  <ul className="space-y-2">
                    {summary.key_points.map((point, i) => (
                      <li key={i} className="flex items-start gap-2 md:gap-3">
                        <span className="w-5 h-5 md:w-6 md:h-6 bg-amber-100 text-amber-700 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0">
                          {i + 1}
                        </span>
                        <span className="text-sm md:text-base text-gray-600">{point}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Decisions */}
              {summary.decisions && summary.decisions.length > 0 && (
                <div>
                  <h3 className="flex items-center gap-2 text-base md:text-lg font-semibold text-gray-900 mb-2 md:mb-3">
                    <CheckCircle2 className="w-4 h-4 md:w-5 md:h-5 text-emerald-500" />
                    Decisions Made
                  </h3>
                  <ul className="space-y-2">
                    {summary.decisions.map((decision, i) => (
                      <li key={i} className="flex items-start gap-2 md:gap-3">
                        <CheckCircle2 className="w-4 h-4 md:w-5 md:h-5 text-emerald-500 flex-shrink-0 mt-0.5" />
                        <span className="text-sm md:text-base text-gray-600">{decision}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Discussion Topics */}
              {summary.discussion_topics && summary.discussion_topics.length > 0 && (
                <div>
                  <h3 className="flex items-center gap-2 text-base md:text-lg font-semibold text-gray-900 mb-2 md:mb-3">
                    <MessageSquare className="w-4 h-4 md:w-5 md:h-5 text-blue-500" />
                    Discussion Topics
                  </h3>
                  <div className="space-y-2 md:space-y-3">
                    {summary.discussion_topics.map((topic, i) => (
                      <div
                        key={i}
                        className="border border-gray-200 rounded-xl overflow-hidden"
                      >
                        <button
                          onClick={() => toggleTopic(i)}
                          className="w-full flex items-center justify-between p-3 md:p-4 hover:bg-gray-50 transition-colors"
                        >
                          <span className="font-medium text-gray-900 text-sm md:text-base text-left">{topic.topic}</span>
                          {expandedTopics.has(i) ? (
                            <ChevronUp className="w-4 h-4 md:w-5 md:h-5 text-gray-400 flex-shrink-0" />
                          ) : (
                            <ChevronDown className="w-4 h-4 md:w-5 md:h-5 text-gray-400 flex-shrink-0" />
                          )}
                        </button>
                        {expandedTopics.has(i) && (
                          <div className="px-3 md:px-4 pb-3 md:pb-4 text-gray-600 text-xs md:text-sm">
                            {topic.summary}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Next Steps */}
              {summary.next_steps && summary.next_steps.length > 0 && (
                <div>
                  <h3 className="flex items-center gap-2 text-base md:text-lg font-semibold text-gray-900 mb-2 md:mb-3">
                    <Play className="w-4 h-4 md:w-5 md:h-5 text-teal-500" />
                    Next Steps
                  </h3>
                  <ul className="space-y-2">
                    {summary.next_steps.map((step, i) => (
                      <li key={i} className="flex items-start gap-2 md:gap-3">
                        <span className="w-5 h-5 md:w-6 md:h-6 bg-teal-100 text-teal-700 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0">
                          {i + 1}
                        </span>
                        <span className="text-sm md:text-base text-gray-600">{step}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Transcript Tab */}
          {activeTab === 'transcript' && (
            <div className="space-y-3 md:space-y-4 max-h-[400px] md:max-h-[600px] overflow-y-auto pr-2 md:pr-4">
              {(() => {
                // Transcript tabı render edilirken transcript segmentlerini console'a logla
                /* if (result.transcript) {
                  console.log('Transcript tabında gösterilen segmentler:', result.transcript);
                } */
                return result.transcript.map((segment, i) => (
                  <div key={i} className="flex gap-2 md:gap-4">
                    <div className="flex-shrink-0 w-12 md:w-20 text-right">
                      <span className="text-xs text-gray-400 font-mono">
                        {formatTime(segment.start)}
                      </span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <span 
                        className="inline-block px-2 py-0.5 bg-sky-100 text-sky-700 text-xs font-medium rounded mb-1"
                      >
                        {segment.speaker}
                      </span>
                      <p className="text-sm md:text-base text-gray-700">{segment.text}</p>
                    </div>
                  </div>
                ));
              })()}
            </div>
          )}

          {/* Tasks Tab */}
          {activeTab === 'tasks' && (
            <TasksPanel 
              jobId={result.job_id} 
              tasks={result.tasks}
              onTasksUpdate={(updatedTasks: TaskItem[]) => {
                setResult({ ...result, tasks: updatedTasks });
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
}
