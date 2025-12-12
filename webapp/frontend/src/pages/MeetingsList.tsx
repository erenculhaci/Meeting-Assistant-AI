import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  FileAudio, 
  Clock, 
  ListTodo,
  ArrowRight,
  Search,
  Calendar,
  FileText,
  Trash2,
  Loader2
} from 'lucide-react';
import Swal from 'sweetalert2';
import { listResults, deleteMeeting } from '../api';
import type { MeetingListItem } from '../types';

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function MeetingsList() {
  const [meetings, setMeetings] = useState<MeetingListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    async function loadMeetings() {
      try {
        const data = await listResults();
        setMeetings(data);
      } catch (error) {
        console.error('Failed to load meetings:', error);
      } finally {
        setLoading(false);
      }
    }
    loadMeetings();
  }, []);

  const handleDelete = async (e: React.MouseEvent, jobId: string, filename: string) => {
    e.preventDefault();
    e.stopPropagation();
    
    const result = await Swal.fire({
      title: 'Delete Meeting?',
      html: `Are you sure you want to delete <strong>"${filename}"</strong>?<br>This action cannot be undone.`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#dc2626',
      cancelButtonColor: '#6b7280',
      confirmButtonText: 'Yes, delete it',
      cancelButtonText: 'Cancel'
    });

    if (!result.isConfirmed) {
      return;
    }

    setDeletingId(jobId);
    try {
      await deleteMeeting(jobId);
      setMeetings(meetings.filter(m => m.job_id !== jobId));
      await Swal.fire({
        title: 'Deleted!',
        text: 'Meeting has been deleted successfully.',
        icon: 'success',
        timer: 2000,
        showConfirmButton: false
      });
    } catch (error) {
      console.error('Failed to delete meeting:', error);
      await Swal.fire({
        title: 'Error!',
        text: 'Failed to delete meeting. Please try again.',
        icon: 'error',
        confirmButtonColor: '#0ea5e9'
      });
    } finally {
      setDeletingId(null);
    }
  };

  const filteredMeetings = meetings.filter((m) =>
    m.filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 md:mb-8">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-1 md:mb-2">Meetings</h1>
          <p className="text-sm md:text-base text-gray-600">View and manage your processed meetings</p>
        </div>
        <Link
          to="/upload"
          className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors shadow-lg shadow-sky-200 text-sm md:text-base"
        >
          <FileAudio className="w-4 h-4" />
          Upload New
        </Link>
      </div>

      {/* Search */}
      <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-3 md:p-4 mb-4 md:mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 md:w-5 md:h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search meetings..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 md:pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent text-sm md:text-base"
          />
        </div>
      </div>

      {/* Meetings Grid */}
      {loading ? (
        <div className="text-center py-8 md:py-12">
          <div className="w-8 h-8 border-4 border-sky-200 border-t-sky-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500 text-sm md:text-base">Loading meetings...</p>
        </div>
      ) : filteredMeetings.length === 0 ? (
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-8 md:p-12 text-center">
          <div className="w-12 h-12 md:w-16 md:h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <FileText className="w-6 h-6 md:w-8 md:h-8 text-gray-400" />
          </div>
          <h3 className="text-base md:text-lg font-medium text-gray-900 mb-2">
            {searchQuery ? 'No meetings found' : 'No meetings yet'}
          </h3>
          <p className="text-sm md:text-base text-gray-500 mb-4">
            {searchQuery
              ? 'Try a different search term'
              : 'Upload your first meeting to get started'}
          </p>
          {!searchQuery && (
            <Link
              to="/upload"
              className="inline-flex items-center gap-2 px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors text-sm"
            >
              Upload Meeting
            </Link>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-6">
          {filteredMeetings.map((meeting) => (
            <div
              key={meeting.job_id}
              className="group bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden hover:shadow-xl hover:-translate-y-1 transition-all duration-300 relative"
            >
              <Link
                to={`/meetings/${meeting.job_id}`}
                className="block p-4 md:p-6"
              >
                <div className="flex items-start gap-3 md:gap-4 mb-3 md:mb-4">
                  <div className="w-10 h-10 md:w-12 md:h-12 bg-gradient-to-br from-sky-100 to-cyan-100 rounded-xl flex items-center justify-center flex-shrink-0">
                    <FileAudio className="w-5 h-5 md:w-6 md:h-6 text-sky-600" />
                  </div>
                  <div className="min-w-0 flex-1 pr-8">
                    <h3 className="font-semibold text-gray-900 truncate group-hover:text-sky-600 transition-colors text-sm md:text-base">
                      {meeting.filename}
                    </h3>
                    <p className="text-xs md:text-sm text-gray-500 flex items-center gap-1 mt-1">
                      <Calendar className="w-3 h-3" />
                      {formatDate(meeting.created_at)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs md:text-sm">
                  <div className="flex items-center gap-3 md:gap-4">
                    <span className="flex items-center gap-1 text-gray-500">
                      <Clock className="w-3 h-3 md:w-4 md:h-4" />
                      {formatDuration(meeting.duration)}
                    </span>
                    <span className="flex items-center gap-1 text-emerald-600 font-medium">
                      <ListTodo className="w-3 h-3 md:w-4 md:h-4" />
                      {meeting.task_count} tasks
                    </span>
                  </div>
                  <ArrowRight className="w-4 h-4 md:w-5 md:h-5 text-gray-300 group-hover:text-sky-500 group-hover:translate-x-1 transition-all" />
                </div>
              </Link>

              {/* Delete Button */}
              <button
                onClick={(e) => handleDelete(e, meeting.job_id, meeting.filename)}
                disabled={deletingId === meeting.job_id}
                className="absolute top-3 right-3 p-2 bg-white/80 hover:bg-red-50 rounded-lg border border-gray-200 hover:border-red-300 transition-colors group/delete"
                title="Delete meeting"
              >
                {deletingId === meeting.job_id ? (
                  <Loader2 className="w-4 h-4 text-gray-400 animate-spin" />
                ) : (
                  <Trash2 className="w-4 h-4 text-gray-400 group-hover/delete:text-red-600" />
                )}
              </button>

              {/* Bottom accent */}
              <div className="h-1 bg-gradient-to-r from-sky-500 via-blue-500 to-cyan-500 transform scale-x-0 group-hover:scale-x-100 transition-transform origin-left" />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
