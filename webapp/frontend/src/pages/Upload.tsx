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
  upload: { icon: UploadIcon, label: 'Uploading', color: 'text-sky-600' },
  transcription: { icon: Mic, label: 'Transcribing', color: 'text-cyan-600' },
  summarization: { icon: FileText, label: 'Summarizing', color: 'text-blue-600' },
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
      <div className="mb-6 md:mb-8">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">Upload Meeting</h1>
        <p className="text-sm md:text-base text-gray-600">
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
              'relative p-6 md:p-12 border-2 border-dashed rounded-xl m-4 md:m-6 transition-all duration-200',
              dragActive
                ? 'border-sky-500 bg-sky-50'
                : file
                ? 'border-emerald-300 bg-emerald-50'
                : 'border-gray-200 hover:border-sky-300 hover:bg-gray-50'
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
                  <div className="w-12 h-12 md:w-16 md:h-16 bg-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-3 md:mb-4">
                    <FileIcon className="w-6 h-6 md:w-8 md:h-8 text-emerald-600" />
                  </div>
                  <p className="text-base md:text-lg font-medium text-gray-900 mb-1 truncate px-2">{file.name}</p>
                  <p className="text-xs md:text-sm text-gray-500 mb-3 md:mb-4">
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
                  <div className="w-12 h-12 md:w-16 md:h-16 bg-sky-100 rounded-2xl flex items-center justify-center mx-auto mb-3 md:mb-4">
                    <UploadIcon className="w-6 h-6 md:w-8 md:h-8 text-sky-600" />
                  </div>
                  <p className="text-base md:text-lg font-medium text-gray-900 mb-1">
                    Drop your file here or click to browse
                  </p>
                  <p className="text-xs md:text-sm text-gray-500">
                    Supports {ALLOWED_EXTENSIONS.join(', ')} • Max 500MB
                  </p>
                </>
              )}
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="mx-4 md:mx-6 mb-4 md:mb-6 p-3 md:p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {/* Upload Button */}
          <div className="px-4 md:px-6 pb-4 md:pb-6">
            <button
              onClick={handleUpload}
              disabled={!file || isProcessing}
              className={clsx(
                'w-full py-3 md:py-4 rounded-xl font-semibold text-base md:text-lg transition-all duration-200',
                file && !isProcessing
                  ? 'bg-gradient-to-r from-sky-500 via-blue-500 to-cyan-500 text-white shadow-lg shadow-sky-200 hover:shadow-xl hover:shadow-blue-300 hover:-translate-y-0.5'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'
              )}
            >
              Start Processing
            </button>
          </div>
        </div>
      ) : (
        /* Processing View */
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-4 md:p-8">
          <div className="text-center mb-6 md:mb-8">
            <div className="w-16 h-16 md:w-20 md:h-20 bg-sky-100 rounded-full flex items-center justify-center mx-auto mb-3 md:mb-4">
              {jobStatus?.status === 'completed' ? (
                <CheckCircle2 className="w-8 h-8 md:w-10 md:h-10 text-green-600" />
              ) : (
                <Loader2 className="w-8 h-8 md:w-10 md:h-10 text-sky-600 animate-spin" />
              )}
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-gray-900 mb-2">
              {jobStatus?.status === 'completed' ? 'Processing Complete!' : 'Processing...'}
            </h2>
            <p className="text-sm md:text-base text-gray-600">{jobStatus?.message || 'Starting...'}</p>
          </div>

          {/* Progress Bar */}
          <div className="mb-6 md:mb-8">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-500">Progress</span>
              <span className="font-medium text-gray-900">{jobStatus?.progress || 0}%</span>
            </div>
            <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-sky-500 via-blue-500 to-cyan-500 rounded-full transition-all duration-500"
                style={{ width: `${jobStatus?.progress || 0}%` }}
              />
            </div>
          </div>

          {/* Steps */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-4">
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
                    'text-center p-2 md:p-4 rounded-xl transition-all',
                    isActive && 'bg-sky-50',
                    isPast && 'opacity-50'
                  )}
                >
                  <div
                    className={clsx(
                      'w-8 h-8 md:w-10 md:h-10 rounded-full flex items-center justify-center mx-auto mb-1 md:mb-2',
                      isActive ? 'bg-sky-100' : 'bg-gray-100'
                    )}
                  >
                    <StepIcon
                      className={clsx(
                        'w-4 h-4 md:w-5 md:h-5',
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
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 md:gap-4 mt-6 md:mt-8">
        <div className="bg-white rounded-xl p-3 md:p-4 shadow border border-gray-100">
          <Mic className="w-5 h-5 md:w-6 md:h-6 text-cyan-600 mb-2" />
          <h3 className="font-medium text-gray-900 mb-1 text-sm md:text-base">Transcription</h3>
          <p className="text-xs md:text-sm text-gray-500">Fast and accurate speech-to-text</p>
        </div>
        <div className="bg-white rounded-xl p-3 md:p-4 shadow border border-gray-100">
          <FileText className="w-5 h-5 md:w-6 md:h-6 text-sky-600 mb-2" />
          <h3 className="font-medium text-gray-900 mb-1 text-sm md:text-base">Summarization</h3>
          <p className="text-xs md:text-sm text-gray-500">AI-powered meeting summaries</p>
        </div>
        <div className="bg-white rounded-xl p-3 md:p-4 shadow border border-gray-100">
          <ListTodo className="w-5 h-5 md:w-6 md:h-6 text-emerald-600 mb-2" />
          <h3 className="font-medium text-gray-900 mb-1 text-sm md:text-base">Task Extraction</h3>
          <p className="text-xs md:text-sm text-gray-500">Automatic action item detection</p>
        </div>
      </div>
    </div>
  );
}
