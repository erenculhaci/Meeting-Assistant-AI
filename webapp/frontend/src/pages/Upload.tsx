import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Upload as UploadIcon, 
  FileAudio, 
  FileVideo,
  X, 
  Loader2,
  CheckCircle2,
  AlertCircle,
  Mic,
  FileText,
  ListTodo
} from 'lucide-react';
import { clsx } from 'clsx';
import { uploadFile, getJobStatus } from '../api';
import type { JobStatus } from '../types';

const ALLOWED_EXTENSIONS = ['.mp3', '.mp4', '.wav', '.m4a', '.webm', '.ogg', '.flac'];

const stepInfo = {
  upload: { icon: UploadIcon, label: 'Uploading', color: 'text-blue-600' },
  transcription: { icon: Mic, label: 'Transcribing', color: 'text-purple-600' },
  summarization: { icon: FileText, label: 'Summarizing', color: 'text-indigo-600' },
  extraction: { icon: ListTodo, label: 'Extracting Tasks', color: 'text-emerald-600' },
  done: { icon: CheckCircle2, label: 'Complete', color: 'text-green-600' },
};

export default function UploadPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const validateFile = (file: File): boolean => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setError(`Invalid file type. Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`);
      return false;
    }
    if (file.size > 500 * 1024 * 1024) { // 500MB limit
      setError('File too large. Maximum size is 500MB.');
      return false;
    }
    setError(null);
    return true;
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && validateFile(droppedFile)) {
      setFile(droppedFile);
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && validateFile(selectedFile)) {
      setFile(selectedFile);
    }
  };

  const pollJobStatus = async (jobId: string) => {
    try {
      const status = await getJobStatus(jobId);
      setJobStatus(status);

      if (status.status === 'completed') {
        setIsProcessing(false);
        // Navigate to results after a brief delay
        setTimeout(() => {
          navigate(`/meetings/${jobId}`);
        }, 1500);
      } else if (status.status === 'failed') {
        setIsProcessing(false);
        setError(status.error || 'Processing failed');
      } else {
        // Continue polling
        setTimeout(() => pollJobStatus(jobId), 1000);
      }
    } catch (err) {
      setIsProcessing(false);
      setError('Failed to check job status');
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsProcessing(true);
    setError(null);

    try {
      const status = await uploadFile(file);
      setJobStatus(status);
      pollJobStatus(status.job_id);
    } catch (err: any) {
      setIsProcessing(false);
      setError(err.response?.data?.detail || 'Upload failed');
    }
  };

  const getFileIcon = () => {
    if (!file) return FileAudio;
    const ext = file.name.split('.').pop()?.toLowerCase();
    return ext === 'mp4' || ext === 'webm' ? FileVideo : FileAudio;
  };

  const FileIcon = getFileIcon();

  return (
    <div className="animate-fadeIn max-w-3xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload Meeting</h1>
        <p className="text-gray-600">
          Upload an audio or video file to transcribe, summarize, and extract action items.
        </p>
      </div>

      {/* Upload Area */}
      {!isProcessing ? (
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={clsx(
              'relative p-12 border-2 border-dashed rounded-xl m-6 transition-all duration-200',
              dragActive
                ? 'border-indigo-500 bg-indigo-50'
                : file
                ? 'border-emerald-300 bg-emerald-50'
                : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
            )}
          >
            <input
              type="file"
              accept={ALLOWED_EXTENSIONS.join(',')}
              onChange={handleFileSelect}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              disabled={isProcessing}
            />

            <div className="text-center">
              {file ? (
                <>
                  <div className="w-16 h-16 bg-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <FileIcon className="w-8 h-8 text-emerald-600" />
                  </div>
                  <p className="text-lg font-medium text-gray-900 mb-1">{file.name}</p>
                  <p className="text-sm text-gray-500 mb-4">
                    {(file.size / (1024 * 1024)).toFixed(2)} MB
                  </p>
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      setFile(null);
                    }}
                    className="inline-flex items-center gap-2 text-sm text-gray-500 hover:text-red-600 transition-colors"
                  >
                    <X className="w-4 h-4" />
                    Remove file
                  </button>
                </>
              ) : (
                <>
                  <div className="w-16 h-16 bg-indigo-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                    <UploadIcon className="w-8 h-8 text-indigo-600" />
                  </div>
                  <p className="text-lg font-medium text-gray-900 mb-1">
                    Drop your file here or click to browse
                  </p>
                  <p className="text-sm text-gray-500">
                    Supports {ALLOWED_EXTENSIONS.join(', ')} • Max 500MB
                  </p>
                </>
              )}
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="mx-6 mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Upload Button */}
          <div className="px-6 pb-6">
            <button
              onClick={handleUpload}
              disabled={!file || isProcessing}
              className={clsx(
                'w-full py-4 rounded-xl font-semibold text-lg transition-all duration-200',
                file && !isProcessing
                  ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-200 hover:shadow-xl hover:shadow-indigo-300 hover:-translate-y-0.5'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'
              )}
            >
              Start Processing
            </button>
          </div>
        </div>
      ) : (
        /* Processing View */
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-8">
          <div className="text-center mb-8">
            <div className="w-20 h-20 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
              {jobStatus?.status === 'completed' ? (
                <CheckCircle2 className="w-10 h-10 text-green-600" />
              ) : (
                <Loader2 className="w-10 h-10 text-indigo-600 animate-spin" />
              )}
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              {jobStatus?.status === 'completed' ? 'Processing Complete!' : 'Processing...'}
            </h2>
            <p className="text-gray-600">{jobStatus?.message || 'Starting...'}</p>
          </div>

          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-500">Progress</span>
              <span className="font-medium text-gray-900">{jobStatus?.progress || 0}%</span>
            </div>
            <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full transition-all duration-500"
                style={{ width: `${jobStatus?.progress || 0}%` }}
              />
            </div>
          </div>

          {/* Steps */}
          <div className="grid grid-cols-4 gap-4">
            {(['transcription', 'summarization', 'extraction', 'done'] as const).map((step, index) => {
              const info = stepInfo[step];
              const StepIcon = info.icon;
              const isActive = jobStatus?.step === step;
              const isPast = jobStatus?.step && 
                ['transcription', 'summarization', 'extraction', 'done'].indexOf(jobStatus.step) > index;

              return (
                <div
                  key={step}
                  className={clsx(
                    'text-center p-4 rounded-xl transition-all',
                    isActive && 'bg-indigo-50',
                    isPast && 'opacity-50'
                  )}
                >
                  <div
                    className={clsx(
                      'w-10 h-10 rounded-full flex items-center justify-center mx-auto mb-2',
                      isActive ? 'bg-indigo-100' : 'bg-gray-100'
                    )}
                  >
                    <StepIcon
                      className={clsx(
                        'w-5 h-5',
                        isActive ? info.color : 'text-gray-400',
                        isActive && step !== 'done' && 'animate-pulse'
                      )}
                    />
                  </div>
                  <p className={clsx(
                    'text-xs font-medium',
                    isActive ? 'text-gray-900' : 'text-gray-400'
                  )}>
                    {info.label}
                  </p>
                </div>
              );
            })}
          </div>

          {/* Error */}
          {error && (
            <div className="mt-8 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}
        </div>
      )}

      {/* Info Cards */}
      <div className="grid grid-cols-3 gap-4 mt-8">
        <div className="bg-white rounded-xl p-4 shadow border border-gray-100">
          <Mic className="w-6 h-6 text-purple-600 mb-2" />
          <h3 className="font-medium text-gray-900 mb-1">Transcription</h3>
          <p className="text-sm text-gray-500">Fast and accurate speech-to-text</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow border border-gray-100">
          <FileText className="w-6 h-6 text-indigo-600 mb-2" />
          <h3 className="font-medium text-gray-900 mb-1">Summarization</h3>
          <p className="text-sm text-gray-500">AI-powered meeting summaries</p>
        </div>
        <div className="bg-white rounded-xl p-4 shadow border border-gray-100">
          <ListTodo className="w-6 h-6 text-emerald-600 mb-2" />
          <h3 className="font-medium text-gray-900 mb-1">Task Extraction</h3>
          <p className="text-sm text-gray-500">Automatic action item detection</p>
        </div>
      </div>
    </div>
  );
}
