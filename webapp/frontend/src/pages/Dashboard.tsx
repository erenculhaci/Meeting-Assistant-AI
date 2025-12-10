import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Upload, 
  FileAudio, 
  Clock, 
  CheckCircle2, 
  ArrowRight,
  Sparkles,
  ListTodo,
  FileText
} from 'lucide-react';
import { listResults, getJiraConfig } from '../api';
import type { MeetingListItem, JiraConfigStatus } from '../types';

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function Dashboard() {
  const [meetings, setMeetings] = useState<MeetingListItem[]>([]);
  const [jiraStatus, setJiraStatus] = useState<JiraConfigStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [meetingsData, jiraData] = await Promise.all([
          listResults(),
          getJiraConfig(),
        ]);
        setMeetings(meetingsData);
        setJiraStatus(jiraData);
      } catch (error) {
        console.error('Failed to load dashboard data:', error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const totalTasks = meetings.reduce((sum, m) => sum + m.task_count, 0);
  const totalDuration = meetings.reduce((sum, m) => sum + m.duration, 0);

  return (
    <div className="animate-fadeIn">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Dashboard</h1>
        <p className="text-gray-600">Welcome back! Here's an overview of your meeting analysis.</p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <Link
          to="/upload"
          className="group bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl p-6 text-white shadow-xl shadow-indigo-200 hover:shadow-2xl hover:shadow-indigo-300 transition-all duration-300 hover:-translate-y-1"
        >
          <div className="flex items-start justify-between">
            <div>
              <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center mb-4">
                <Upload className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold mb-2">Upload New Meeting</h3>
              <p className="text-indigo-100 text-sm">
                Upload audio or video files to transcribe and analyze
              </p>
            </div>
            <ArrowRight className="w-6 h-6 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </Link>

        <Link
          to="/settings"
          className={`group rounded-2xl p-6 shadow-xl transition-all duration-300 hover:-translate-y-1 ${
            jiraStatus?.configured
              ? 'bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-emerald-200 hover:shadow-2xl hover:shadow-emerald-300'
              : 'bg-white border-2 border-dashed border-gray-300 hover:border-indigo-400 text-gray-700 hover:shadow-lg'
          }`}
        >
          <div className="flex items-start justify-between">
            <div>
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 ${
                jiraStatus?.configured ? 'bg-white/20' : 'bg-gray-100'
              }`}>
                <Sparkles className={`w-6 h-6 ${jiraStatus?.configured ? 'text-white' : 'text-gray-500'}`} />
              </div>
              <h3 className="text-xl font-bold mb-2">
                {jiraStatus?.configured ? 'Jira Connected' : 'Connect Jira'}
              </h3>
              <p className={`text-sm ${jiraStatus?.configured ? 'text-emerald-100' : 'text-gray-500'}`}>
                {jiraStatus?.configured
                  ? `Connected to ${jiraStatus.domain}`
                  : 'Set up Jira integration to create tasks automatically'}
              </p>
            </div>
            <ArrowRight className={`w-6 h-6 opacity-0 group-hover:opacity-100 transition-opacity ${
              jiraStatus?.configured ? 'text-white' : 'text-gray-500'
            }`} />
          </div>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
              <FileAudio className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Meetings</p>
              <p className="text-2xl font-bold text-gray-900">{meetings.length}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
              <ListTodo className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Tasks Extracted</p>
              <p className="text-2xl font-bold text-gray-900">{totalTasks}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
              <Clock className="w-6 h-6 text-emerald-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Duration</p>
              <p className="text-2xl font-bold text-gray-900">{formatDuration(totalDuration)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Meetings */}
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Recent Meetings</h2>
          {meetings.length > 0 && (
            <Link to="/meetings" className="text-sm text-indigo-600 hover:text-indigo-700 font-medium">
              View all →
            </Link>
          )}
        </div>

        {loading ? (
          <div className="p-12 text-center">
            <div className="w-8 h-8 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-500">Loading meetings...</p>
          </div>
        ) : meetings.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <FileText className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No meetings yet</h3>
            <p className="text-gray-500 mb-4">Upload your first meeting to get started</p>
            <Link
              to="/upload"
              className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              <Upload className="w-4 h-4" />
              Upload Meeting
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {meetings.slice(0, 5).map((meeting) => (
              <Link
                key={meeting.job_id}
                to={`/meetings/${meeting.job_id}`}
                className="flex items-center gap-4 px-6 py-4 hover:bg-gray-50 transition-colors"
              >
                <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
                  <FileAudio className="w-5 h-5 text-indigo-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate">{meeting.filename}</p>
                  <p className="text-sm text-gray-500">{formatDate(meeting.created_at)}</p>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-gray-500">{formatDuration(meeting.duration)}</span>
                  <span className="flex items-center gap-1 text-emerald-600">
                    <CheckCircle2 className="w-4 h-4" />
                    {meeting.task_count} tasks
                  </span>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-400" />
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
